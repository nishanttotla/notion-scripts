from dataclasses import dataclass
from diskcache import Cache
import os
from pprint import pprint
import requests


@dataclass
class OmdbEntity():
  imdb_id: str
  full_entity: dict
  force_update_cache: bool

  def __init__(self, imdb_id, force_update_cache=False):
    self.imdb_id = imdb_id
    self.full_entity = {}
    self.force_update_cache = force_update_cache

    if not force_update_cache:
      cache = Cache("./omdbcache")
      cached_full_entity = cache.get(imdb_id)

      # If a cached entity is found, use that to avoid the RPC
      if cached_full_entity:
        pprint("--------------------------------------")
        pprint("Fetched CACHED MDB entity successfuly for IMDB ID: " +
               self.imdb_id)
        self.full_entity = cached_full_entity
        return
    else:
      pprint("force_update_cache=True")

    url = "http://www.omdbapi.com/"
    payload = {
        "i": self.imdb_id,
        "r": "json",
        "apikey": os.environ["OMDB_API_KEY"]
    }
    self.full_entity = requests.get(url, params=payload).json()

    if self.full_entity.pop('Response') == 'False':
      raise GetMovieException(result['Error'])

    # Cache value for 60 days (15*86400 seconds)
    cache.set(imdb_id, self.full_entity, expire=5184000)
    pprint("--------------------------------------")
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
    if self.full_entity["totalSeasons"] == "N/A":
      return 0
    return int(self.full_entity["totalSeasons"])

  def poster_url(self) -> str:
    return self.full_entity["Poster"]

  def plot(self) -> str:
    return self.full_entity["Plot"]