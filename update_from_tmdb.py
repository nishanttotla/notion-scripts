import os
import sys

# Get the absolute path of the directory containing the module
tmdb_module_directory = "./tmdb"
notion_module_directory = "./notionhelpers"

# Add the directory to the system path
sys.path.append(tmdb_module_directory)
sys.path.append(notion_module_directory)

from datetime import datetime
from notion_client import Client
from notionhelpers import ColumnType
from notionhelpers import notion_database_query_all
from notionhelpers import NotionRow
from tmdbhelpers import TmdbEntity
from pprint import pprint

# TODO: Maybe we need multiple clients for better bandwidth?
notion = Client(auth=fos.environ["NOTION_TOKEN"])
shows_db = notion_database_query_all(notion, auth=os.environ["SHOWS_DB"])
seasons_db = notion_database_query_all(notion, auth=os.environ["SEASONS_DB"])


def update_show_notion_row(show_row: NotionRow):
  return false


def update_season_notion_row(season_row: NotionRow):
  return false


def create_season_notion_row(imdb_id: str, season_index: str):
  return false


# We assume that all shows which are desired are added to the shows DB,
# even if all seasons aren't present.
# Assume IMDB ID is populated in the original show row. Otherwise nothing will work.
imdb_to_show = {}
for result in shows_db["results"]:
  notion_row = NotionRow(result["id"], result["properties"])
  notion_row.set_client(notion)
  imdb_id = notion_row.get_value(ColumnType.TEXT, "IMDB ID")[0]
  tmdb_entity = TmdbEntity(imdb_id)
  imdb_to_show[imdb_id] = {
      "notion_row": notion_row,
      "tmdb_entity": tmdb_entity,
      "seasons_db_notion_rows": {}
  }

for result in seasons_db["results"]:
  notion_row = NotionRow(result["id"], result["properties"])
  notion_row.set_client(notion)
  imdb_id = ""  # TODO get it somehow
  seasons_index = ""  # TODO get title
  imdb_to_show[imdb_id]["seasons_db_notion_rows"][season_index] = notion_row

test_imdb_id = 'tt12345678'
