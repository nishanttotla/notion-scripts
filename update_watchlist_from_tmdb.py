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

# THIS CODE MUST BE IDEMPOTENT !!!
input_imdb_ids = sys.argv[1:]

# TODO: Maybe we need multiple clients for better bandwidth?
notion = Client(auth=os.environ["NOTION_TOKEN"])
pprint("Fetching watchlist...")
shows_db = notion_database_query_all(notion, os.environ["FUTURE_SHOWS_DB"])


def sanitize_keywords(keywords: list) -> list:
  sanitized_keywords = []
  for w in keywords:
    sanitized_keywords.extend(w.split(","))
  return sanitized_keywords


def update_show_notion_row(show: NotionRow, tmdb: TmdbEntity):
  pprint(">>>> Updating Notion row for show with IMDB ID: " +
         tmdb.get_imdb_id())

  show.update_value(ColumnType.RICH_TEXT, "Original Title",
                    tmdb.get_original_title())
  show.update_value(ColumnType.RICH_TEXT, "Tagline", tmdb.get_tagline())
  show.update_value(ColumnType.RICH_TEXT, "Plot", tmdb.get_plot())

  if tmdb.get_backdrop_path_url():
    show.update_value(ColumnType.FILES,
                      "Backdrop",
                      tmdb.get_backdrop_path_url(),
                      title=tmdb.get_title())

  show_release_date = tmdb.get_release_date()
  if show_release_date != None:
    show.update_value(ColumnType.DATE, "Release Date", show_release_date)

  show.update_value(ColumnType.SELECT, "Status", tmdb.get_status())
  show.update_value(ColumnType.SELECT, "Type", tmdb.get_type())

  if tmdb.get_content_rating():
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
  show.update_value(ColumnType.MULTI_SELECT, "Keywords",
                    sanitize_keywords(tmdb.get_keywords()))

  show.update_value(ColumnType.NUMBER, "Number of Seasons",
                    tmdb.get_number_of_seasons())
  show.update_value(ColumnType.NUMBER, "TMDB Rating", tmdb.get_tmdb_rating())

  show.update_value(ColumnType.DATE, "[IMPORT] Last Import Date",
                    datetime.today().strftime('%Y-%m-%d'))
  show.update_db_row()


def delete_show_notion_row(show: NotionRow, tmdb: TmdbEntity):
  pprint(">>>> Deleting Notion row for show with IMDB ID: " +
         tmdb.get_imdb_id())
  show.delete_db_row()


# We assume that all shows which are desired are added to the shows DB,
# even if all seasons aren't present.
# Assume IMDB ID and title are populated in the original show row.
# Otherwise nothing will work.
# TODO: Make this work with only IMDB ID
# Pre-process shows
imdb_to_show = {}

for result in shows_db["results"]:
  notion_row = NotionRow(result["id"], result["properties"])
  notion_row.set_client(notion)
  imdb_id = notion_row.get_value(ColumnType.RICH_TEXT, "IMDB ID")[0]

  try:
    tmdb_entity = TmdbEntity(imdb_id, force_update_cache=True)
  except Exception as e:
    pprint("Could not fetch TMDB Entity for IMDB ID: " + imdb_id)
    pprint("Exception: " + str(e))
    tmdb_entity = {}
  imdb_to_show[imdb_id] = {
      "notion_row": notion_row,
      "tmdb_entity": tmdb_entity,
  }

# Update requested IMDB IDs or everything.
update_imdb_ids = []
if not input_imdb_ids:
  update_imdb_ids = list(imdb_to_show.keys())
else:
  update_imdb_ids = input_imdb_ids

for imdb_id in update_imdb_ids:
  if imdb_to_show[imdb_id]["tmdb_entity"] == {}:
    continue
  if imdb_to_show[imdb_id]["notion_row"].get_value(ColumnType.RELATION,
                                                   "Shows DB Reference"):
    delete_show_notion_row(imdb_to_show[imdb_id]["notion_row"],
                           imdb_to_show[imdb_id]["tmdb_entity"])
    continue

  update_show_notion_row(imdb_to_show[imdb_id]["notion_row"],
                         imdb_to_show[imdb_id]["tmdb_entity"])