from dataclasses import dataclass
import os
from pprint import pprint
import requests

@dataclass
class OmdbEntity():
  imdb_id: str
  full_entity: dict

  def __init__(self, imdb_id):
    self.imdb_id = imdb_id
    self.full_entity = {}
    url = "http://www.omdbapi.com/"
    payload = {"i": self.imdb_id, "r": "json", "apikey": os.environ["OMDB_API_KEY"]}
    self.full_entity = requests.get(url, params=payload).json()
  
    # TODO: Create a disk file based cache so that OMDB calls can be avoided.
    if self.full_entity.pop('Response') == 'False':
      raise GetMovieException(result['Error'])
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