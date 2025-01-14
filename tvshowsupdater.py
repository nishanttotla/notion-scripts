import os
import sys

# Get the absolute path of the directory containing the module
current_directory = os.path.dirname(os.path.abspath(__file__))
tmdb_module_directory = os.path.join(current_directory, "tmdb")
notion_module_directory = os.path.join(current_directory, "notionhelpers")

# Add the directory to the system path
sys.path.append(tmdb_module_directory)
sys.path.append(notion_module_directory)

from datetime import datetime
from notion_client import Client
from notionhelpers import ColumnType
from notionhelpers import notion_database_query_all
from notionhelpers import NotionRow
from tmdbhelpers import TmdbEntity
from tmdbhelpers import TmdbSearcher
from tmdbhelpers import kDefaultTimezone
from pprint import pprint

kAutomateUpdateIntervalDays = 3


def search_from_tmdb(query: str):
  searcher = TmdbSearcher(query)
  # sort results by vote average (outer sort) and then air date (inner sort)
  latest_first = sorted(searcher.fetch_results(),
                        key=lambda d: d["first_air_date"])
  latest_first.reverse()
  return sorted(latest_first, key=lambda d: 0 - d["vote_average"])


class AddFromTmdb():
  __notion: Client
  __tmdb_id: str
  __is_watchlist: bool
  __tmdb_entity: TmdbEntity
  __entity_available: bool
  __error_message: str

  def __init__(self, tmdb_id: str = "", is_watchlist: bool = False):
    self.__notion = Client(auth=os.environ["NOTION_TOKEN"])
    self.__tmdb_id = tmdb_id
    self.__is_watchlist = is_watchlist
    self.__entity_available = False
    self.__error_message = ""

    try:
      self.__tmdb_entity = TmdbEntity(tmdb_id=tmdb_id, force_update_cache=True)
      self.__entity_available = True
    except Exception as e:
      pprint("Could not fetch TMDB Entity for TMDB ID: " + tmdb_id)
      pprint("Exception: " + str(e))
      self.__error_message = str(e)

  ############################## Helper Functions ##############################

  def __sanitize_multi_select_list(self, words: list) -> list:
    clean_list = []
    for word in words:
      clean_list.append(word.replace(",", ""))
    return clean_list

  def __update_notion_row_with_error(self, imdb_id: str, error_msg: str,
                                     row_id: str):
    pprint(">>>> Updating Notion row WITH ERRORS for show with IMDB ID: " +
           imdb_id)
    new_row = NotionRow(row_id, {
        "[IMPORT] Errors": {},
        "[IMPORT] Last Import Date": {}
    })
    new_row.set_client(self.__notion)
    new_row.update_value(ColumnType.RICH_TEXT, "[IMPORT] Errors", error_msg)
    new_row.update_value(
        ColumnType.DATE, "[IMPORT] Last Import Date",
        datetime.today().astimezone(kDefaultTimezone).strftime('%Y-%m-%d'))
    new_row.update_db_row()

  def __update_show_notion_row(self, show: NotionRow) -> str:
    pprint(">>>> Updating Notion row for show with IMDB ID: " +
           self.__tmdb_entity.get_imdb_id())

    show.update_value(ColumnType.RICH_TEXT, "Original Title",
                      self.__tmdb_entity.get_original_title())
    show.update_value(ColumnType.RICH_TEXT, "Tagline",
                      self.__tmdb_entity.get_tagline())
    show.update_value(ColumnType.RICH_TEXT, "Plot",
                      self.__tmdb_entity.get_plot())

    if self.__tmdb_entity.get_backdrop_path_url():
      show.update_value(ColumnType.FILES,
                        "Backdrop",
                        self.__tmdb_entity.get_backdrop_path_url(),
                        title=self.__tmdb_entity.get_title())

    show_release_date = self.__tmdb_entity.get_release_date()
    if show_release_date != None:
      show.update_value(ColumnType.DATE, "Release Date", show_release_date)

    show.update_value(ColumnType.SELECT, "Status",
                      self.__tmdb_entity.get_status())
    show.update_value(ColumnType.SELECT, "Type", self.__tmdb_entity.get_type())

    if self.__tmdb_entity.get_content_rating():
      show.update_value(ColumnType.SELECT, "Content Rating (US)",
                        self.__tmdb_entity.get_content_rating())

    show.update_value(
        ColumnType.MULTI_SELECT, "Cast",
        self.__sanitize_multi_select_list(self.__tmdb_entity.get_cast()))
    show.update_value(
        ColumnType.MULTI_SELECT, "Creators",
        self.__sanitize_multi_select_list(self.__tmdb_entity.get_creators()))
    show.update_value(
        ColumnType.MULTI_SELECT, "Production Companies",
        self.__sanitize_multi_select_list(
            self.__tmdb_entity.get_production_companies()))
    show.update_value(
        ColumnType.MULTI_SELECT, "Networks",
        self.__sanitize_multi_select_list(self.__tmdb_entity.get_networks()))
    show.update_value(
        ColumnType.MULTI_SELECT, "Watch Providers (US)",
        self.__sanitize_multi_select_list(
            self.__tmdb_entity.get_watch_providers()))
    show.update_value(ColumnType.MULTI_SELECT, "Countries",
                      self.__tmdb_entity.get_countries())
    show.update_value(ColumnType.MULTI_SELECT, "Languages",
                      self.__tmdb_entity.get_languages())
    show.update_value(ColumnType.MULTI_SELECT, "Genres",
                      self.__tmdb_entity.get_genres())
    show.update_value(
        ColumnType.MULTI_SELECT, "Keywords",
        self.__sanitize_multi_select_list(self.__tmdb_entity.get_keywords()))

    show.update_value(ColumnType.NUMBER, "Number of Seasons",
                      self.__tmdb_entity.get_number_of_seasons())
    show.update_value(ColumnType.NUMBER, "TMDB Rating",
                      self.__tmdb_entity.get_tmdb_rating())

    show.update_value(ColumnType.DATE, "[IMPORT] Last Import Date",
                      self.__tmdb_entity.get_import_date())

    show.clear_value(ColumnType.RICH_TEXT, "[IMPORT] Errors")
    if show.update_db_row():
      self.__update_notion_row_with_error(self.__tmdb_entity.get_imdb_id(),
                                          show.get_update_errors(),
                                          show.get_id())
    return show.get_update_errors()

  ################################ API Functions ###############################

  def get_error_message(self):
    return self.__error_message

  def get_entity(self):
    return self.__tmdb_entity

  def get_imdb_id(self):
    return self.__tmdb_entity.get_imdb_id()

  def create_show_notion_row(self):
    # TODO: Add a lookup to check if this IMDB ID already exists
    if not self.__entity_available:
      raise ValueError("Entity is unavailable for TMDB ID: " + self.__tmdb_id)
    show = NotionRow("", {})
    show.set_client(self.__notion)
    title = self.__tmdb_entity.get_title()
    imdb_id = self.__tmdb_entity.get_imdb_id()

    pprint(">> Creating Notion row for show " + title + " with IMDB ID: " +
           self.__tmdb_entity.get_imdb_id())
    show.create_field(ColumnType.TITLE, "Title", title)
    show.create_field(ColumnType.RICH_TEXT, "IMDB ID", imdb_id)
    show.create_field(ColumnType.SELECT, "[IMPORT] Next Import Hint",
                      "Automate")
    # TODO: create other fields, will need notion functions

    db = os.environ["SHOWS_DB"]
    icon = "https://www.notion.so/icons/movie-clapboard-play_orange.svg"
    if self.__is_watchlist:
      db = os.environ["FUTURE_SHOWS_DB"]
      icon = "https://www.notion.so/icons/movie-clapboard-play_blue.svg"

    show.create_new_db_row(db,
                           icon={
                               "type": "external",
                               "external": {
                                   "url": icon
                               }
                           })

    # Update the row right away to fill in all available data
    self.__update_show_notion_row(show)


class UpdateFromTmdb():
  __notion: Client
  __shows_db: dict
  __seasons_db: dict
  __input_imdb_ids: list
  __imdb_to_show: dict
  __show_id_to_imdb: dict
  __is_watchlist: bool

  def __init__(self, imdb_ids: list = [], is_watchlist: bool = False):
    # TODO: Maybe we need multiple clients for better bandwidth?
    self.__notion = Client(auth=os.environ["NOTION_TOKEN"])
    self.__is_watchlist = is_watchlist

    if not is_watchlist:
      pprint("Fetching all shows...")
      self.__shows_db = notion_database_query_all(self.__notion,
                                                  os.environ["SHOWS_DB"])
      pprint("Fetching all seasons...")
      self.__seasons_db = notion_database_query_all(self.__notion,
                                                    os.environ["SEASONS_DB"])
    else:
      pprint("Fetching watchlist...")
      self.__shows_db = notion_database_query_all(self.__notion,
                                                  os.environ["FUTURE_SHOWS_DB"])

    self.__input_imdb_ids = imdb_ids
    self.__imdb_to_show = {}
    self.__show_id_to_imdb = {}

  ############################## Helper Functions ##############################

  def __sanitize_multi_select_list(self, words: list) -> list:
    clean_list = []
    for word in words:
      clean_list.append(word.replace(",", ""))
    return clean_list

  ########################## Notion Updater Functions ##########################

  def __update_notion_row_with_error(self, imdb_id: str, error_msg: str,
                                     row_id: str):
    pprint(">>>> Updating Notion row WITH ERRORS for show with IMDB ID: " +
           imdb_id)
    new_row = NotionRow(row_id, {
        "[IMPORT] Errors": {},
        "[IMPORT] Last Import Date": {}
    })
    new_row.set_client(self.__notion)
    new_row.update_value(ColumnType.RICH_TEXT, "[IMPORT] Errors", error_msg)
    new_row.update_value(
        ColumnType.DATE, "[IMPORT] Last Import Date",
        datetime.today().astimezone(kDefaultTimezone).strftime('%Y-%m-%d'))
    new_row.update_db_row()

  def __update_show_notion_row(self, show: NotionRow, tmdb: TmdbEntity,
                               is_automated_update: bool) -> str:
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

    show.update_value(ColumnType.MULTI_SELECT, "Cast",
                      self.__sanitize_multi_select_list(tmdb.get_cast()))
    show.update_value(ColumnType.MULTI_SELECT, "Creators",
                      self.__sanitize_multi_select_list(tmdb.get_creators()))
    show.update_value(
        ColumnType.MULTI_SELECT, "Production Companies",
        self.__sanitize_multi_select_list(tmdb.get_production_companies()))
    show.update_value(ColumnType.MULTI_SELECT, "Networks",
                      self.__sanitize_multi_select_list(tmdb.get_networks()))
    show.update_value(
        ColumnType.MULTI_SELECT, "Watch Providers (US)",
        self.__sanitize_multi_select_list(tmdb.get_watch_providers()))
    show.update_value(ColumnType.MULTI_SELECT, "Countries",
                      tmdb.get_countries())
    show.update_value(ColumnType.MULTI_SELECT, "Languages",
                      tmdb.get_languages())
    show.update_value(ColumnType.MULTI_SELECT, "Genres", tmdb.get_genres())
    show.update_value(ColumnType.MULTI_SELECT, "Keywords",
                      self.__sanitize_multi_select_list(tmdb.get_keywords()))

    show.update_value(ColumnType.NUMBER, "Number of Seasons",
                      tmdb.get_number_of_seasons())
    show.update_value(ColumnType.NUMBER, "TMDB Rating", tmdb.get_tmdb_rating())

    show.update_value(ColumnType.DATE, "[IMPORT] Last Import Date",
                      tmdb.get_import_date())
    # TODO: Ideally, this import hint update should be done after the seasons
    # are updated. Possible way to accomplish this is to update the show after
    # seasons.
    if not is_automated_update:
      show.update_value(ColumnType.SELECT, "[IMPORT] Next Import Hint",
                        "Check Status")
    show.clear_value(ColumnType.RICH_TEXT, "[IMPORT] Errors")
    if show.update_db_row():
      self.__update_notion_row_with_error(tmdb.get_imdb_id(),
                                          show.get_update_errors(),
                                          show.get_id())
    return show.get_update_errors()

  def __delete_show_notion_row(self, show: NotionRow, tmdb: TmdbEntity):
    pprint(">>>> Deleting Notion row for show with IMDB ID: " +
           tmdb.get_imdb_id())
    show.delete_db_row()

  def __update_season_notion_row(self,
                                 show_id: str,
                                 season: NotionRow,
                                 tmdb: TmdbEntity,
                                 set_unwatched: bool = False):
    title = season.get_value(ColumnType.TITLE, "Season Index")[0]
    season_number = int(title.split(" ")[1])  # title looks like "Season 3"
    pprint(">> Updating Notion row for " + title + " for IMDB ID: " +
           tmdb.get_imdb_id())

    season.update_value(ColumnType.RELATION,
                        "Show", [show_id],
                        relation_db=self.__shows_db)
    season_air_date = tmdb.get_season_air_date(season_number)
    if season_air_date != None:
      season.update_value(ColumnType.DATE, "Air Date",
                          tmdb.get_season_air_date(season_number))
    season_finale_date = tmdb.get_season_finale_date(season_number)
    if season_finale_date != None:
      season.update_value(ColumnType.DATE, "Finale Date",
                          tmdb.get_season_finale_date(season_number))
    season.update_value(ColumnType.RICH_TEXT, "Overview",
                        tmdb.get_season_overview(season_number))
    season.update_value(ColumnType.NUMBER, "Number of Episodes",
                        tmdb.get_season_number_of_episodes(season_number))
    season.update_value(ColumnType.NUMBER, "Total Runtime (mins)",
                        tmdb.get_season_runtime_mins(season_number))
    per_episode_runtimes = str(
        tmdb.get_season_runtimes_list_mins(season_number))
    season.update_value(ColumnType.RICH_TEXT, "Per Episode Runtimes (mins)",
                        per_episode_runtimes[1:-1])
    if tmdb.get_backdrop_path_url():
      season.update_value(ColumnType.FILES,
                          "Backdrop",
                          tmdb.get_backdrop_path_url(),
                          title=tmdb.get_title() + " " + title)

    if set_unwatched:
      season.update_value(ColumnType.SELECT, "Watch Status", "Not Started")

    season.update_value(ColumnType.DATE, "[IMPORT] Last Import Date",
                        tmdb.get_import_date())
    season.update_db_row()

  def __create_season_notion_row(self, show_id: str, season_number: int,
                                 tmdb: TmdbEntity):
    season = NotionRow("", {})
    season.set_client(self.__notion)
    title = "Season " + str(season_number)

    pprint(">> Creating Notion row for " + title + " for IMDB ID: " +
           tmdb.get_imdb_id())
    season.create_field(ColumnType.TITLE, "Season Index", title)
    season.create_field(ColumnType.RELATION, "Show", [show_id])
    season.create_field(ColumnType.RICH_TEXT, "Overview",
                        [tmdb.get_season_overview(season_number)])
    # TODO: create other fields, will need notion functions
    season.create_new_db_row(
        os.environ["SEASONS_DB"],
        icon={
            "type": "external",
            "external": {
                "url": "https://www.notion.so/icons/view_green.svg"
            }
        })

    # Update the row right away to fill in all available data
    self.__update_season_notion_row(show_id, season, tmdb, set_unwatched=True)

  def __cache_update_needed(self, import_hint: str,
                            date_last_updated: str) -> bool:
    if not date_last_updated:
      return True
    if import_hint == "Force Update":
      return True
    days_since_last_update = (
        datetime.today().astimezone(kDefaultTimezone) - datetime.strptime(
            date_last_updated, '%Y-%m-%d').astimezone(kDefaultTimezone)).days
    if import_hint == "Automate" and (days_since_last_update
                                      >= kAutomateUpdateIntervalDays):
      return True
    return False

  def __run_automated_update(self, import_hint: str,
                             date_last_updated: str) -> bool:
    if not date_last_updated:
      return True
    if import_hint != "Automate":
      return False
    days_since_last_update = (
        datetime.today().astimezone(kDefaultTimezone) - datetime.strptime(
            date_last_updated, '%Y-%m-%d').astimezone(kDefaultTimezone)).days
    if days_since_last_update >= kAutomateUpdateIntervalDays:
      return True
    return False

  ###################### Notion Rows Processing Functions ######################

  def __process_shows(self):
    for result in self.__shows_db["results"]:
      notion_row = NotionRow(result["id"], result["properties"])
      notion_row.set_client(self.__notion)
      imdb_id = notion_row.get_value(ColumnType.RICH_TEXT, "IMDB ID")[0]

      # If only specific IDs are requested, no need to process everything
      if self.__input_imdb_ids and (not imdb_id in self.__input_imdb_ids):
        continue

      import_hint = notion_row.get_value(ColumnType.SELECT,
                                         "[IMPORT] Next Import Hint")
      date_last_updated = notion_row.get_value(ColumnType.DATE,
                                               "[IMPORT] Last Import Date")
      try:
        tmdb_entity = TmdbEntity(imdb_id=imdb_id,
                                 force_update_cache=self.__cache_update_needed(
                                     import_hint, date_last_updated or ""))
      except Exception as e:
        pprint("Could not fetch TMDB Entity for IMDB ID: " + imdb_id)
        pprint("Exception: " + str(e))
        tmdb_entity = {}
      if not self.__is_watchlist:
        self.__imdb_to_show[imdb_id] = {
            "notion_row": notion_row,
            "tmdb_entity": tmdb_entity,
            "seasons_db_notion_rows": {}
        }
        self.__show_id_to_imdb[notion_row.get_id()] = imdb_id
      else:
        self.__imdb_to_show[imdb_id] = {
            "notion_row": notion_row,
            "tmdb_entity": tmdb_entity,
        }

  def __process_seasons(self):
    for result in self.__seasons_db["results"]:
      notion_row = NotionRow(result["id"], result["properties"])
      notion_row.set_client(self.__notion)

      show_id = notion_row.get_value(ColumnType.RELATION, "Show")[0]
      imdb_id = ""
      # show_id will be missing from show_id_to_imdb if this show was not
      # processed by __process_shows
      if show_id in self.__show_id_to_imdb:
        imdb_id = self.__show_id_to_imdb[show_id]
      else:
        continue

      season_index = notion_row.get_value(ColumnType.TITLE, "Season Index")[0]
      self.__imdb_to_show[imdb_id]["seasons_db_notion_rows"][
          season_index] = notion_row

  ################################ API Functions ###############################

  def update_shows_and_seasons(self) -> list:
    if self.__is_watchlist:
      raise NotImplementedError(
          "update_shows_and_seasons is not implemented for is_watchlist=True")
    self.__process_shows()
    self.__process_seasons()
    error_log = []

    for imdb_id in self.__imdb_to_show:
      if self.__imdb_to_show[imdb_id]["tmdb_entity"] == {}:
        err = "No TMDB Entity found for IMDB ID: " + imdb_id
        self.__update_notion_row_with_error(
            imdb_id, err, self.__imdb_to_show[imdb_id]["notion_row"].get_id())
        error_log.append(err)
        continue
      import_hint = self.__imdb_to_show[imdb_id]["notion_row"].get_value(
          ColumnType.SELECT, "[IMPORT] Next Import Hint")
      date_last_updated = self.__imdb_to_show[imdb_id]["notion_row"].get_value(
          ColumnType.DATE, "[IMPORT] Last Import Date")
      run_automated_update = self.__run_automated_update(
          import_hint, date_last_updated)
      if import_hint != "Update" and import_hint != "Force Update" and (
          not run_automated_update):
        pprint("Skipping update for IMDB ID: " + imdb_id +
               " with import_hint=" + str(import_hint))
        continue

      err = self.__update_show_notion_row(
          self.__imdb_to_show[imdb_id]["notion_row"],
          self.__imdb_to_show[imdb_id]["tmdb_entity"], run_automated_update)
      if err:
        error_log.append(err)

      show_id = self.__imdb_to_show[imdb_id]["notion_row"].get_id()
      num_seasons = self.__imdb_to_show[imdb_id][
          "tmdb_entity"].get_number_of_seasons()
      for s in range(1, num_seasons + 1):
        season_index = "Season " + str(s)
        if season_index in self.__imdb_to_show[imdb_id][
            "seasons_db_notion_rows"]:
          self.__update_season_notion_row(
              show_id, self.__imdb_to_show[imdb_id]["seasons_db_notion_rows"]
              [season_index], self.__imdb_to_show[imdb_id]["tmdb_entity"])
        else:
          self.__create_season_notion_row(
              show_id, s, self.__imdb_to_show[imdb_id]["tmdb_entity"])

    # IMDB IDs that came as input but were not found in the Shows DB.
    if self.__input_imdb_ids:
      invalid_imdb_ids = list(
          set(self.__input_imdb_ids) - set(self.__imdb_to_show))
      if invalid_imdb_ids:
        error_log.append("Invalid IMDB IDs: " + str(invalid_imdb_ids))

    return error_log

  def update_watchlist(self):
    if not self.__is_watchlist:
      raise NotImplementedError(
          "update_watchlist is not implemented for is_watchlist=False")
    self.__process_shows()

    for imdb_id in self.__imdb_to_show:
      if self.__imdb_to_show[imdb_id]["tmdb_entity"] == {}:
        self.__update_notion_row_with_error(
            imdb_id, "No TMDB Entity found for IMDB ID: " + imdb_id,
            self.__imdb_to_show[imdb_id]["notion_row"].get_id())
        continue
      if self.__imdb_to_show[imdb_id]["notion_row"].get_value(
          ColumnType.RELATION, "Shows DB Reference"):
        self.__delete_show_notion_row(
            self.__imdb_to_show[imdb_id]["notion_row"],
            self.__imdb_to_show[imdb_id]["tmdb_entity"])
        continue

      import_hint = self.__imdb_to_show[imdb_id]["notion_row"].get_value(
          ColumnType.SELECT, "[IMPORT] Next Import Hint")
      date_last_updated = self.__imdb_to_show[imdb_id]["notion_row"].get_value(
          ColumnType.DATE, "[IMPORT] Last Import Date")
      run_automated_update = self.__run_automated_update(
          import_hint, date_last_updated)
      if import_hint != "Update" and import_hint != "Force Update" and (
          not run_automated_update):
        pprint("Skipping update for IMDB ID: " + imdb_id +
               " with import_hint=" + str(import_hint))
        continue

      self.__update_show_notion_row(self.__imdb_to_show[imdb_id]["notion_row"],
                                    self.__imdb_to_show[imdb_id]["tmdb_entity"],
                                    run_automated_update)