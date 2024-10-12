import os
import sys

# Get the absolute path of the directory containing the module
omdb_module_directory = "./omdb"
notion_module_directory = "./notionhelpers"

# Add the directory to the system path
sys.path.append(omdb_module_directory)
sys.path.append(notion_module_directory)

from datetime import datetime
from notion_client import Client
from notionhelpers import ColumnType
from notionhelpers import notion_database_query_all
from notionhelpers import NotionRow
from omdbhelpers import OmdbEntity
from pprint import pprint

# Main code here

notion = Client(auth=os.environ["NOTION_TOKEN"])

# Integration permissions must be updated to allow read/write content
# In addition, the specific page(s) must also be explicitly shared with
# the integration. It's a two way sharing.

full_db = notion_database_query_all(notion, os.environ["MOVIES_DB"])
pprint("Successfully fetched all DB rows from Notion")

# Update all fields that are missing in each row in the current Notion DB
for result in full_db["results"]:
  pprint("===================================================")

  imdb_id = result["properties"]["IMDB ID"]["rich_text"][0]["plain_text"]
  title = result["properties"]["Title"]["title"][0]["plain_text"]

  if imdb_id != "tt31091039":
    continue

  pprint("--------------------------------------")
  pprint("Processing IMDB ID: " + imdb_id + " (Title: " + title + ")")

  # Fetch the entity from OMDB
  omdb_entity = OmdbEntity(imdb_id)

  pprint("--------------------------------------")
  pprint("Creating updated Notion row...")

  notion_row = NotionRow(result["id"], result["properties"])

  notion_row.update_field(ColumnType.TEXT, "Plot", omdb_entity.plot())
  notion_row.update_field(ColumnType.MULTI_SELECT, "Genres",
                          omdb_entity.genres())
  notion_row.update_field(ColumnType.MULTI_SELECT, "Languages",
                          omdb_entity.languages())
  notion_row.update_field(ColumnType.MULTI_SELECT, "Actors",
                          omdb_entity.actors())
  notion_row.update_field(ColumnType.MULTI_SELECT, "Countries",
                          omdb_entity.countries())
  notion_row.update_field(ColumnType.FILE, "Poster", omdb_entity.poster_url())
  notion_row.update_field(ColumnType.SELECT, "Rated", omdb_entity.rated())
  notion_row.update_field(
      ColumnType.DATE, "Release Date",
      datetime.strptime(omdb_entity.release_date(),
                        '%d %b %Y').strftime('%Y-%m-%d'))
  notion_row.update_field(ColumnType.NUMBER, "Total Seasons",
                          omdb_entity.total_seasons())

  pprint("--------------------------------------")
  # pprint("Created updated Notion row:")
  # pprint(notion_row.get_properties())

  if not notion_row.is_commit_required():
    pprint("SKIPPING Notion page update for IMDB ID: " + imdb_id + " (Title: " +
           title + ")")
    continue

  # TODO: Add a last updated by script date field so that automatic periodic
  # updates can happen
  pprint("SENDING Notion page for IMDB ID: " + imdb_id + " (Title: " + title +
         ")")
  notion.pages.update(**{
      "page_id": result["id"],
      "properties": notion_row.get_pending_update()
  })
