from dataclasses import dataclass
from diskcache import Cache
import os
from pprint import pprint
import requests
import tmdbsimple as tmdb


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

    if not self.__force_update_cache:
      cache = Cache("./tmdbcache")
      cached_full_entity = cache.get(self.__imdb_id)

      # If a cached entity is found, use that to avoid the RPC
      if cached_full_entity:
        pprint("--------------------------------------")
        pprint("Fetched CACHED TMDB entity successfuly for IMDB ID: " +
               self.__imdb_id + " with TMDB ID: " +
               str(cached_full_entity["id"]))
        self.__full_entity = cached_full_entity
        self.__tmdb_id = cached_full_entity["id"]
        return
    else:
      pprint("force_update_cache=True")

    tmdb.API_KEY = os.environ["TMDB_API_KEY"]

    # Fetch tmdb_id if it is still empty
    if not self.__tmdb_id:
      search_result = tmdb.Find(imdb_id).info(external_source="imdb_id")
      if len(search_result["tv_results"]) == 0:
        raise KeyError("No TV show found for imdb_id: " + self.__imdb_id)
      else:
        show_result = search_result["tv_results"][0]
        self.__tmdb_id = show_result["id"]

    # The TMDB API will append all seasons to the output and skip the ones that aren't
    # present so just request up to 20 seasons. I'm hard press to think of a show
    # that would have more, and that I'd even bother much about them. Still, it's
    # something that can be adjusted for special cases later.
    # See https://en.wikipedia.org/wiki/List_of_longest-running_scripted_American_primetime_television_series
    append_seasons = "season/1,season/2,season/3,season/4,season/5,season/6,season/7,season/8,season/9,season/10,season/11,season/12,season/13,season/14,season/15,season/16,season/17,season/18,season/19,season/20"
    self.__full_entity = tmdb.TV(
        self.__tmdb_id).info(append_to_response=append_seasons)
    # TODO: How to check if the response is bad?

    # Cache value for 60 days (60*86400 seconds)
    cache.set(self.__imdb_id, self.__full_entity, expire=5184000)
    pprint("--------------------------------------")
    pprint("Fetched TMDB entity successfuly for IMDB ID: " + self.__imdb_id)

  ############################## Getter Functions ##############################
