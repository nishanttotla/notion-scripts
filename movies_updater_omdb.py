import os
import requests
from notion_client import Client
from pprint import pprint
from dataclasses import dataclass
from enum import Enum

class ColumnType(Enum):
  UNKNOWN = 0
  TEXT = 1
  DATE = 2
  NUMBER = 3
  SELECT = 4
  MULTI_SELECT = 5
  FILE = 6
  CHECKBOX = 7

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

@dataclass
class OmdbEntity():
  imdb_id: str
  full_entity: dict

  def __init__(self, imdb_id):
    self.imdb_id = imdb_id
    self.full_entity = {}
    url = "http://www.omdbapi.com/"
    payload = {"i": self.imdb_id, "r": "json", "apikey": os.environ["OMDB_API_KEY"]}
    self.full_entity = requests.get(url, params=payload).json()
  
    if self.full_entity.pop('Response') == 'False':
      raise GetMovieException(result['Error'])
    pprint("Fetched OMDB entity successfuly for IMDB ID: " + self.imdb_id)

  def genres(self) -> list:
    return self.full_entity["Genre"].split(",")

  def countries(self) -> list:
    return self.full_entity["Country"].split(",")

  def actors(self) -> list:
    return self.full_entity["Actors"].split(",")

  def languages(self) -> list:
    return self.full_entity["Language"].split(",")

  def rated(self) -> str:
    return self.full_entity["Rated"]

  def release_date(self) -> str:
    return self.full_entity["Released"]

  def total_seasons(self) -> int:
    return int(self.full_entity["totalSeasons"])

  def poster_url(self) -> str:
    return self.full_entity["Poster"]

  def plot(self) -> str:
    return self.full_entity["Plot"]


@dataclass
class NotionRowProperties():
  row_id: str
  updated_properties: dict
  old_properties: dict
  force_update: bool

  def __init__(self, row_id: str, updated_properties: dict, old_properties: dict):
    self.row_id = row_id
    self.updated_properties = updated_properties
    self.old_properties = old_properties
    self.force_update = False


  def maybe_update_field(self,  col_type: ColumnType, name: str, value):
    # TODO: For Python 3.10 and above, switch case statements can be used.
    # Validate input types and call the right update function.
    if col_type == ColumnType.UNKNOWN:
      raise ValueError("Type was not set for field: " + name)
    elif col_type == ColumnType.TEXT:
      if not type(value) is str:
        raise TypeError("Expected type str, got: " + type(value))      
      self.maybe_update_text_field_internal(name, value)
    elif col_type == ColumnType.DATE:
      if not type(value) is str:
        raise TypeError("Expected type str, got: " + type(value))  
      self.maybe_update_date_field_internal(name, value)
    elif col_type == ColumnType.NUMBER:
      if not type(value) is int:
        raise TypeError("Expected type int, got: " + type(value))      
      self.maybe_update_number_field_internal(name, value)
    elif col_type == ColumnType.SELECT:
      if not type(value) is str:
        raise TypeError("Expected type str, got: " + type(value))      
      self.maybe_update_select_field_internal(name, value)
    elif col_type == ColumnType.MULTI_SELECT:
      if not type(value) is list:
        raise TypeError("Expected type list, got: " + type(value))
      self.maybe_update_multi_select_field_internal(name, value)
    elif col_type == ColumnType.FILE:
      if not type(value) is str:
        raise TypeError("Expected type str, got: " + type(value))      
      self.maybe_update_file_field_internal(name, value)
    else:
      raise NotImplementedError("No implementation yet for type: " + type.name)

  # The update functions will skip updating if the existing property is non-empty
  # unless force_update is set.
  def maybe_update_text_field_internal(self, name:str, value):
    print("In due time! text")

  def maybe_update_date_field_internal(self, name:str, value):
    print("In due time! date")

  def maybe_update_number_field_internal(self, name:str, value):
    print("In due time! number")

  def maybe_update_select_field_internal(self, name:str, value):
    if (self.old_properties[name]["select"] == None) & (not self.force_update):
      pprint("Skipping update for non-empty field " + name + " for row_id: " + self.row_id)

    self.updated_properties[name] = {"type": "select"}
    self.updated_properties[name]["select"] = {"name": value}

  def maybe_update_multi_select_field_internal(self, name:str, value):
    if (len(self.old_properties[name]["multi_select"]) == 0) & (not self.force_update):
      pprint("Skipping update for non-empty field " + name + " for row_id: " + self.row_id)

    self.updated_properties[name] = {"type": "multi_select"}

    list_tagged = []
    for item in value:
      list_tagged.append({"name": item})

    self.updated_properties[name]["multi_select"] = list_tagged

  def maybe_update_file_field_internal(self, name:str, value):
    print("In due time! file")

# Main code here

notion = Client(auth=os.environ["NOTION_TOKEN"])

# Integration permissions must be updated to allow read/write content
# In addition, the specific page(s) must also be explicitly shared with
# the integration. It's a two way sharing.

full_db = notion_database_query_all(notion, os.environ["MOVIES_DB"])
pprint("Successfully fetched all DB rows from Notion")

i = 0;
# Update all fields that are missing in each row in the current Notion DB
for result in full_db["results"]:
  imdb_id = title = result["properties"]["IMDB ID"]["rich_text"][0]["plain_text"]
  title = result["properties"]["Title"]["title"][0]["plain_text"]
  pprint("Processing IMDB ID: " + imdb_id + " (Title: " + title + ")")

  # Fetch the entity from OMDB
  omdb_entity = OmdbEntity(imdb_id)

  updated_properties = NotionRowProperties(result["id"], {}, result["properties"])
  updated_properties.maybe_update_field(ColumnType.MULTI_SELECT, "Genres", omdb_entity.genres())
  updated_properties.maybe_update_field(ColumnType.SELECT, "Rated", omdb_entity.rated())

  pprint(updated_properties.updated_properties)
  i=i+1
  if (i>0):
    break

  # fetch OMDB entity for this page
  # omdb_entity = omdb_get_entity(imdb_id)

  # pprint("Updated genres for: " + title)
  # notion.pages.update(**{"page_id": result["id"], "properties": new_db_row["properties"]})

