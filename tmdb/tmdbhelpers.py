from dataclasses import dataclass
from diskcache import Cache
import os
from pprint import pprint
import requests
import tmdbsimple as tmdb


@dataclass
class TmdbEntity():
  imdb_id: str
  tmdb_id: str
  full_entity: dict
  force_update_cache: bool

  def __init__(self, imdb_id, tmbd_id="", force_update_cache=False):
    self.imdb_id = imdb_id
    self.tmdb_id = tmdb_id
    self.full_entity = {}
    self.force_update_cache = force_update_cache

    if not force_update_cache:
      cache = Cache("./tmdbcache")
      cached_full_entity = cache.get(imdb_id)

      # If a cached entity is found, use that to avoid the RPC
      if cached_full_entity:
        pprint("--------------------------------------")
        pprint("Fetched CACHED TMDB entity successfuly for IMDB ID: " +
               self.imdb_id + " with TMDB ID: " + cached_tmdb_id)
        self.full_entity = cached_full_entity
        self.tmdb_id = cached_tmdb_id
        return
    else:
      pprint("force_update_cache=True")

    tmdb.API_KEY = os.environ["TMDB_API_KEY"]

    # Fetch tmdb_id if it is still empty
    if not self.tmdb_id:
      search_result = tmdb.Find(imdb_id).info(external_source="imdb_id")
      if len(search_result["tv_results"]) == 0:
        raise KeyError("No TV show found for IMDB_ID: " + imdb_id)
      else:
        show_result = search_result["tv_results"][0]
        self.tmdb_id = show_result["id"]

    # The TMDB API will append all seasons to the output and skip the ones that aren't
    # present so just request up to 20 seasons. I'm hard press to think of a show
    # that would have more, and that I'd even bother much about them. Still, it's
    # something that can be adjusted for special cases later.
    # See https://en.wikipedia.org/wiki/List_of_longest-running_scripted_American_primetime_television_series
    append_seasons = "season/1,season/2,season/3,season/4,season/5,season/6,season/7,season/8,season/9,season/10,season/11,season/12,season/13,season/14,season/15,season/16,season/17,season/18,season/19,season/20,"
    self.full_entity = tmdb.TV(tmdb_id).info(append_to_response=append_seasons)
    # TODO: How to check if the response is bad?

    # Cache value for 60 days (60*86400 seconds)
    cache.set(imdb_id, self.full_entity, expire=5184000)
    pprint("--------------------------------------")
    pprint("Fetched TMDB entity successfuly for IMDB ID: " + self.imdb_id)

  ######################### Getter Functions ###########################
