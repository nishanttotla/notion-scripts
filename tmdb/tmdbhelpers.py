from dataclasses import dataclass
from diskcache import Cache
import os
from pprint import pprint
from datetime import datetime, timedelta
import requests
import pytz
import tmdbsimple as tmdb

kMaxSupportedSeasons = 20
kDefaultContentRatingCountryCode = "US"
kCacheTtlDays = 15
kDefaultTimezone = pytz.timezone('America/New_York')


@dataclass
class TmdbEntity():
  __imdb_id: str
  __tmdb_id: str
  __full_entity: dict
  __force_update_cache: bool

  def __init__(self, imdb_id, tmdb_id="", force_update_cache=False):
    self.__imdb_id = imdb_id
    self.__tmdb_id = tmdb_id
    self.__full_entity = {}
    self.__force_update_cache = force_update_cache

    cache = Cache("./tmdbcache")
    if not self.__force_update_cache:
      cached_full_entity = cache.get(self.__imdb_id)

      # If a cached entity is found, use that to avoid multiple (5) RPCs
      if cached_full_entity:
        pprint("Fetched CACHED TMDB entity for IMDB ID: " + self.__imdb_id +
               " with TMDB ID: " + str(cached_full_entity["id"]))
        self.__full_entity = cached_full_entity
        self.__tmdb_id = cached_full_entity["id"]
        return

    tmdb.API_KEY = os.environ["TMDB_API_KEY"]

    # Fetch tmdb_id if it is empty
    if not self.__tmdb_id:
      search_result = tmdb.Find(imdb_id).info(external_source="imdb_id")
      if len(search_result["tv_results"]) == 0:
        raise KeyError("No TV show found for imdb_id: " + self.__imdb_id)
      else:
        show_result = search_result["tv_results"][0]
        self.__tmdb_id = show_result["id"]

    # Create a fetcher that will be used to call multiple endpoints.
    fetcher = tmdb.TV(self.__tmdb_id)

    # TODO: Some shows have specials listed as season/0. That needs special handling.
    append_seasons = ""
    for season_number in range(1, kMaxSupportedSeasons):
      append_seasons = append_seasons + self.__season_key(season_number) + ","
    append_seasons = append_seasons + self.__season_key(kMaxSupportedSeasons)

    self.__full_entity = fetcher.info(append_to_response=append_seasons)
    self.__full_entity["credits"] = fetcher.credits()
    self.__full_entity["content_ratings"] = fetcher.content_ratings()
    self.__full_entity["keywords"] = fetcher.keywords()
    self.__full_entity["import_date"] = datetime.today().astimezone(
        kDefaultTimezone).strftime('%Y-%m-%d')

    # TODO: How to check if the responses are bad?

    cache.set(self.__imdb_id, self.__full_entity, expire=kCacheTtlDays * 86400)
    pprint("Fetched TMDB entity for IMDB ID: " + self.__imdb_id)

  def print(self):
    pprint(self.__full_entity)

  ############################ Show Getter Functions ###########################

  def __extract_name(self, d: dict):
    return d["name"]

  def get_import_date(self) -> str:
    if "import_date" in self.__full_entity:
      return self.__full_entity["import_date"]
    # If import date is missing for some reason, assume that data is stale
    stale_date = datetime.now().astimezone(kDefaultTimezone) - timedelta(
        days=kCacheTtlDays)
    return stale_date.strftime('%Y-%m-%d')

  def get_imdb_id(self) -> str:
    return self.__imdb_id

  def get_tmdb_id(self) -> str:
    return self.__tmdb_id

  def get_title(self) -> str:
    return self.__full_entity["name"]

  def get_original_title(self) -> str:
    return self.__full_entity["original_name"]

  def get_tagline(self) -> str:
    return self.__full_entity["tagline"]

  def get_plot(self) -> str:
    return self.__full_entity["overview"]

  def get_backdrop_path_url(self) -> str:
    if self.__full_entity["backdrop_path"] == None:
      return ""
    return "https://image.tmdb.org/t/p/w780" + self.__full_entity["backdrop_path"]

  def get_release_date(self) -> str:
    return self.__full_entity["first_air_date"]

  def get_status(self) -> str:
    return self.__full_entity["status"]

  def get_type(self) -> str:
    return self.__full_entity["type"]

  def get_content_rating(self,
                         country_code: str = kDefaultContentRatingCountryCode
                         ) -> str:
    default_code = ""
    for result in self.__full_entity["content_ratings"]["results"]:
      if result["iso_3166_1"] == country_code:
        return result["rating"]
      if result["iso_3166_1"] == kDefaultContentRatingCountryCode:
        default_code = result["rating"]
    return default_code

  def get_cast(self) -> list:
    return list(map(self.__extract_name, self.__full_entity["credits"]["cast"]))

  def get_creators(self) -> list:
    return list(map(self.__extract_name, self.__full_entity["created_by"]))

  def get_production_companies(self) -> list:
    return list(
        map(self.__extract_name, self.__full_entity["production_companies"]))

  def get_networks(self) -> list:
    return list(map(self.__extract_name, self.__full_entity["networks"]))

  def get_countries(self) -> list:
    return list(
        map(self.__extract_name, self.__full_entity["production_countries"]))

  def get_languages(self) -> list:
    def extract_language(g):
      return g["english_name"]

    return list(map(extract_language, self.__full_entity["spoken_languages"]))

  def get_genres(self) -> list:
    return list(map(self.__extract_name, self.__full_entity["genres"]))

  def get_keywords(self) -> list:
    return list(
        map(self.__extract_name, self.__full_entity["keywords"]["results"]))

  def get_number_of_seasons(self) -> int:
    return self.__full_entity["number_of_seasons"]

  def get_tmdb_rating(self) -> float:
    return self.__full_entity["vote_average"]

  ########################### Season Getter Functions ##########################

  def __season_key(self, season_number: int) -> str:
    return "season/" + str(season_number)

  def __validate_season_number(self, season_number: int):
    if season_number < 1 or season_number > kMaxSupportedSeasons:
      raise ValueError("Accessing out of range season number: " +
                       str(season_number) + " for IMDB ID: " + self.__imdb_id)
    if season_number > self.__full_entity["number_of_seasons"]:
      raise ValueError("Accessing non-existent season number: " +
                       str(season_number) + " for IMDB ID: " + self.__imdb_id)
    if not self.__season_key(season_number) in self.__full_entity:
      raise ValueError("Accessing unavailable season number: " +
                       str(season_number) + " for IMDB ID: " + self.__imdb_id)

  def get_season_air_date(self, season_number: int) -> str:
    self.__validate_season_number(season_number)
    return self.__full_entity[self.__season_key(season_number)]["air_date"]

  def get_season_finale_date(self, season_number: int) -> str:
    self.__validate_season_number(season_number)
    episodes = self.__full_entity[self.__season_key(season_number)]["episodes"]
    if episodes != None and len(episodes) > 0:
      return episodes[len(episodes) - 1]["air_date"]
    return None

  def get_season_overview(self, season_number: int) -> str:
    self.__validate_season_number(season_number)
    return self.__full_entity[self.__season_key(season_number)]["overview"]

  def get_season_number_of_episodes(self, season_number: int) -> int:
    self.__validate_season_number(season_number)
    return len(self.__full_entity[self.__season_key(season_number)]["episodes"])

  def get_season_runtime_mins(self, season_number: int) -> int:
    self.__validate_season_number(season_number)

    runtime = 0
    for episode in self.__full_entity[self.__season_key(
        season_number)]["episodes"]:
      runtime = runtime + (0 if
                           (episode["runtime"] == None) else episode["runtime"])
    return runtime

  def get_season_runtimes_list_mins(self, season_number: int) -> int:
    self.__validate_season_number(season_number)

    runtimes = []
    for episode in self.__full_entity[self.__season_key(
        season_number)]["episodes"]:
      runtimes.append(0 if (episode["runtime"] == None) else episode["runtime"])
    return runtimes
