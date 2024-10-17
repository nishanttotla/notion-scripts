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


def update_show_notion_row(show_row: NotionRow, show_tmdb: TmdbEntity):
  show_row.update_value(ColumnType.RICH_TEXT, "Original Title",
                        show_tmdb.get_original_title())
  show.update_value(ColumnType.RICH_TEXT, "Tagline", show_tmdb.get_tagline())
  show.update_value(ColumnType.RICH_TEXT, "Plot", show_tmdb.get_plot())

  show.update_value(ColumnType.FILE,
                    "Backdrop",
                    show_tmdb.get_backdrop_path_url(),
                    title=show_tmdb.get_title())

  show.update_value(ColumnType.DATE, "Release Date",
                    show_tmdb.get_release_date())

  show.update_value(ColumnType.SELECT, "Status", show_tmdb.get_status())
  show.update_value(ColumnType.SELECT, "Type", show_tmdb.get_type())
  show.update_value(ColumnType.SELECT, "Content Rating (US)",
                    show_tmdb.get_content_rating())

  show.update_value(ColumnType.MULTI_SELECT, "Cast", show_tmdb.get_cast())
  show.update_value(ColumnType.MULTI_SELECT, "Creators",
                    show_tmdb.get_creators())
  show.update_value(ColumnType.MULTI_SELECT, "Production Companies",
                    show_tmdb.get_production_companies())
  show.update_value(ColumnType.MULTI_SELECT, "Networks",
                    show_tmdb.get_networks())
  show.update_value(ColumnType.MULTI_SELECT, "Countries",
                    show_tmdb.get_countries())
  show.update_value(ColumnType.MULTI_SELECT, "Languages",
                    show_tmdb.get_languages())
  show.update_value(ColumnType.MULTI_SELECT, "Genres", show_tmdb.get_genres())
  show.update_value(ColumnType.MULTI_SELECT, "Keywords",
                    show_tmdb.get_keywords())

  show.update_value(ColumnType.NUMBER, "Number of Seasons",
                    show_tmdb.get_number_of_seasons())
  show.update_value(ColumnType.NUMBER, "TMDB Rating",
                    show_tmdb.get_tmdb_rating())


def update_season_notion_row(season_row: NotionRow,
                             show_tmdb_entity: TmdbEntity):
  return false


def create_season_notion_row(season_index: str, show_row: NotionRow,
                             show_tmdb_entity: TmdbEntity):
  return false


# We assume that all shows which are desired are added to the shows DB,
# even if all seasons aren't present.
# Assume IMDB ID and title are populated in the original show row.
# Otherwise nothing will work.
# TODO: Make this work with only IMDB ID
imdb_to_show = {}
for result in shows_db["results"]:
  notion_row = NotionRow(result["id"], result["properties"])
  notion_row.set_client(notion)
  imdb_id = notion_row.get_value(ColumnType.RICH_TEXT, "IMDB ID")[0]
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
