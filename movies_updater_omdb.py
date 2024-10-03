import csv
import os
import requests
from notion_client import Client
from pprint import pprint

# Environment variable must be exported for use with os.environ, for example:
# $ export NOTION_TOKEN="secret_xyz"
# For ease of use, define an env_vars.sh file and add it to .gitignore and run:
# $ source env_vars.sh


def notion_database_query_all(notion: Client, database_id: str) -> dict:
  """Return all rows for the database."""
  data = notion.databases.query(database_id)
  database_object = data['object']
  has_more = data['has_more']
  next_cursor = data['next_cursor']
  while has_more == True:
      data_while = notion.databases.query(database_id, start_cursor=next_cursor)
      for row in data_while['results']:
          data['results'].append(row)
      has_more = data_while['has_more']
      next_cursor = data_while['next_cursor']

  new_database = {
      "object": database_object,
      "results": data["results"],
      "next_cursor": next_cursor,
      "has_more": has_more
  }
  return new_database

def read_csv(path: str) -> dict:
  """Read an IMDB export CSV file and create a dictionary keyed by movie title."""
  imdb_dict = {}
  with open(path, mode ='r') as file:    
    csv_file = csv.DictReader(file)
    # Title is at position 5 in IMDB export
    for lines in csv_file:
      if lines["Title"] in imdb_dict:
        pprint("Found repeated key: "+ lines["Title"])
      else:
        imdb_dict[lines["Title"]] = lines
  return imdb_dict

def notion_row_add_genres(title: str, db_row: dict, imdb_dict: dict):
  """Takes a row from the Notion DB and returns an updated version of it by filling in genre from imdb_dict"""
  genres_str = imdb_dict[title]["Genres"]
  genres = genres_str.split(",")

  new_db_row = db_row
  new_db_row["properties"] = { "Genres" : { "type": "multi_select"}}

  genres_tagged = []
  for genre in genres:
    genres_tagged.append({"name": genre})

  new_db_row["properties"]["Genres"]["multi_select"] = genres_tagged
  return new_db_row

def omdb_get_entity(imdb_id: str):
  """Fetches an entity using the IMDB ID. Uses the OMDB API."""
  url = 'http://www.omdbapi.com/'
  payload = {"i": imdb_id, "r": "json", "apikey": os.environ["OMDB_API_KEY"]}
  result = requests.get(url, params=payload).json()
  
  if result.pop('Response') == 'False':
    raise GetMovieException(result['Error'])

  return result


notion = Client(auth=os.environ["NOTION_TOKEN"])

# Integration permissions must be updated to allow read/write content
# In addition, the specific page(s) must also be explicitly shared with
# the integration. It's a two way sharing.

full_db = notion_database_query_all(notion, os.environ["MOVIES_DB"])
imdb_dict = read_csv("imdb_exports.csv")


### Updating genres
# for result in full_db["results"]:
#   title = result["properties"]["Title"]["title"][0]["plain_text"]
#   new_db_row = {}
#   new_db_row = notion_row_add_genres(title, new_db_row, imdb_dict)
#   pprint("Updated genres for: " + title)
#   notion.pages.update(**{"page_id": result["id"], "properties": new_db_row["properties"]})

res = omdb_get_entity("tt13802576")
pprint(res)

