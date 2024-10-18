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
notion = Client(auth=os.environ["NOTION_TOKEN"])
shows_db = notion_database_query_all(notion, os.environ["SHOWS_DB"])
seasons_db = notion_database_query_all(notion, os.environ["SEASONS_DB"])


def update_show_notion_row(show: NotionRow, tmdb: TmdbEntity):
  pprint(">>>> Updating Notion row for show with IMDB ID: " +
         tmdb.get_imdb_id())
  show.update_value(ColumnType.RICH_TEXT, "Original Title",
                    tmdb.get_original_title())
  show.update_value(ColumnType.RICH_TEXT, "Tagline", tmdb.get_tagline())
  show.update_value(ColumnType.RICH_TEXT, "Plot", tmdb.get_plot())

  show.update_value(ColumnType.FILES,
                    "Backdrop",
                    tmdb.get_backdrop_path_url(),
                    title=tmdb.get_title())

  show.update_value(ColumnType.DATE, "Release Date", tmdb.get_release_date())

  show.update_value(ColumnType.SELECT, "Status", tmdb.get_status())
  show.update_value(ColumnType.SELECT, "Type", tmdb.get_type())
  show.update_value(ColumnType.SELECT, "Content Rating (US)",
                    tmdb.get_content_rating())

  show.update_value(ColumnType.MULTI_SELECT, "Cast", tmdb.get_cast())
  show.update_value(ColumnType.MULTI_SELECT, "Creators", tmdb.get_creators())
  show.update_value(ColumnType.MULTI_SELECT, "Production Companies",
                    tmdb.get_production_companies())
  show.update_value(ColumnType.MULTI_SELECT, "Networks", tmdb.get_networks())
  show.update_value(ColumnType.MULTI_SELECT, "Countries", tmdb.get_countries())
  show.update_value(ColumnType.MULTI_SELECT, "Languages", tmdb.get_languages())
  show.update_value(ColumnType.MULTI_SELECT, "Genres", tmdb.get_genres())
  show.update_value(ColumnType.MULTI_SELECT, "Keywords", tmdb.get_keywords())

  show.update_value(ColumnType.NUMBER, "Number of Seasons",
                    tmdb.get_number_of_seasons())
  show.update_value(ColumnType.NUMBER, "TMDB Rating", tmdb.get_tmdb_rating())

  show.update_db_row()


def update_season_notion_row(show_id: str, season: NotionRow, tmdb: TmdbEntity):
  title = season.get_value(ColumnType.TITLE, "Season Index")[0]
  season_number = int(title.split(" ")[1])  # title looks like "Season 3"

  pprint(">> Updating Notion row for " + title + " for IMDB ID: " +
         tmdb.get_imdb_id())
  season.update_value(ColumnType.RELATION,
                      "Show", [show_id],
                      relation_db=shows_db)
  season.update_value(ColumnType.DATE, "Air Date",
                      tmdb.get_season_air_date(season_number))
  season.update_value(ColumnType.RICH_TEXT, "Overview",
                      tmdb.get_season_overview(season_number))
  season.update_value(ColumnType.NUMBER, "Number of Episodes",
                      tmdb.get_season_number_of_episodes(season_number))
  season.update_value(ColumnType.NUMBER, "Total Runtime (mins)",
                      tmdb.get_season_runtime_mins(season_number))
  season.update_db_row()


def create_season_notion_row(show_id: str, season_number: int,
                             tmdb: TmdbEntity):
  season = NotionRow("", {})
  season.set_client(notion)
  title = "Season " + str(season_number)

  pprint(">> Creating Notion row for " + title + " for IMDB ID: " +
         tmdb.get_imdb_id())
  season.create_field(ColumnType.TITLE, "Season Index", title)
  season.create_field(ColumnType.RELATION, "Show", [show_id])
  # TODO: create other fields, will need notion functions
  season.create_new_db_row(os.environ["SEASONS_DB"],
                           icon={
                               "type": "external",
                               "external": {
                                   "url":
                                   "https://www.notion.so/icons/view_green.svg"
                               }
                           })


# We assume that all shows which are desired are added to the shows DB,
# even if all seasons aren't present.
# Assume IMDB ID and title are populated in the original show row.
# Otherwise nothing will work.
# TODO: Make this work with only IMDB ID
imdb_to_show = {}
show_id_to_imdb = {}
for result in shows_db["results"]:
  notion_row = NotionRow(result["id"], result["properties"])
  notion_row.set_client(notion)
  imdb_id = notion_row.get_value(ColumnType.RICH_TEXT, "IMDB ID")[0]
  try:
    tmdb_entity = TmdbEntity(imdb_id)
  except Exception as e:
    pprint("Could not fetch TMDB Entity for IMDB ID: " + imdb_id)
    pprint("Exception: " + str(e))
  imdb_to_show[imdb_id] = {
      "notion_row": notion_row,
      "tmdb_entity": tmdb_entity,
      "seasons_db_notion_rows": {}
  }
  show_id_to_imdb[notion_row.get_id()] = imdb_id

for result in seasons_db["results"]:
  notion_row = NotionRow(result["id"], result["properties"])
  notion_row.set_client(notion)
  imdb_id = show_id_to_imdb[notion_row.get_value(ColumnType.RELATION,
                                                 "Show")[0]]
  season_index = notion_row.get_value(ColumnType.TITLE, "Season Index")[0]
  imdb_to_show[imdb_id]["seasons_db_notion_rows"][season_index] = notion_row

imdb_id = 'tt0106179'

update_show_notion_row(imdb_to_show[imdb_id]["notion_row"],
                       imdb_to_show[imdb_id]["tmdb_entity"])
show_id = imdb_to_show[imdb_id]["notion_row"].get_id()

num_seasons = imdb_to_show[imdb_id]["tmdb_entity"].get_number_of_seasons()
for s in range(1, num_seasons + 1):
  season_index = "Season " + str(s)
  if season_index in imdb_to_show[imdb_id]["seasons_db_notion_rows"]:
    update_season_notion_row(
        show_id, imdb_to_show[imdb_id]["seasons_db_notion_rows"][season_index],
        imdb_to_show[imdb_id]["tmdb_entity"])
  else:
    create_season_notion_row(show_id, s, imdb_to_show[imdb_id]["tmdb_entity"])