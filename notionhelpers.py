from dataclasses import dataclass
from enum import Enum
from notion_client import Client
from pprint import pprint
import requests

class ColumnType(Enum):
  UNKNOWN = 0
  TEXT = 1
  DATE = 2
  NUMBER = 3
  SELECT = 4
  MULTI_SELECT = 5
  FILE = 6
  CHECKBOX = 7

def notion_database_query_all(notion: Client, database_id: str) -> dict:
  """Return all rows for the database."""
  data = notion.databases.query(database_id)
  database_object = data['object']
  has_more = data['has_more']
  next_cursor = data['next_cursor']
  while has_more == True:
      data_while = notion.databases.query(database_id, start_cursor=next_cursor)
      for row in data_while['results']:
          data['results'].append(row)
      has_more = data_while['has_more']
      next_cursor = data_while['next_cursor']

  new_database = {
      "object": database_object,
      "results": data["results"],
      "next_cursor": next_cursor,
      "has_more": has_more
  }
  return new_database

@dataclass
class NotionRowProperties():
  row_id: str
  updated_properties: dict
  old_properties: dict
  force_update: bool

  def __init__(self, row_id: str, updated_properties: dict, old_properties: dict):
    self.row_id = row_id
    self.updated_properties = updated_properties
    self.old_properties = old_properties
    self.force_update = False


  def maybe_update_field(self,  col_type: ColumnType, name: str, value):
    # TODO: For Python 3.10 and above, switch case statements can be used.
    # Validate input types and call the right update function.
    if col_type == ColumnType.UNKNOWN:
      raise ValueError("Type was not set for field: " + name)
    elif col_type == ColumnType.TEXT:
      self.maybe_update_text_field_internal(name, value)
    elif col_type == ColumnType.DATE:
      self.maybe_update_date_field_internal(name, value)
    elif col_type == ColumnType.NUMBER:
      self.maybe_update_number_field_internal(name, value)
    elif col_type == ColumnType.SELECT:
      self.maybe_update_select_field_internal(name, value)
    elif col_type == ColumnType.MULTI_SELECT:
      self.maybe_update_multi_select_field_internal(name, value)
    elif col_type == ColumnType.FILE:
      self.maybe_update_file_field_internal(name, value)
    else:
      raise NotImplementedError("No implementation yet for type: " + type.name)

  # The update functions will skip updating if the existing property is non-empty
  # unless force_update is set.
  def maybe_update_text_field_internal(self, name:str, value: str):
    if (len(self.old_properties[name]["rich_text"]) != 0) & (not self.force_update):
      pprint("Skipping update for non-empty field '" + name + "' for row_id: " + self.row_id)
      return

    self.updated_properties[name] = self.old_properties[name]
    self.updated_properties[name]["rich_text"] = [{"plain_text": value, "text": {"content": value}}]

  def maybe_update_date_field_internal(self, name:str, value: str):
    if (self.old_properties[name]["date"] != None) & (not self.force_update):
      pprint("Skipping update for non-empty field: " + name)
      return

    self.updated_properties[name] = self.old_properties[name]
    self.updated_properties[name]["date"] = {"start": value}

  def maybe_update_number_field_internal(self, name:str, value: int):
    if (self.old_properties[name]["number"] != None) & (not self.force_update):
      pprint("Skipping update for non-empty field: " + name)
      return

    self.updated_properties[name] = self.old_properties[name]
    self.updated_properties[name]["number"] = value

  def maybe_update_select_field_internal(self, name:str, value: str):
    if (self.old_properties[name]["select"] != None) & (not self.force_update):
      pprint("Skipping update for non-empty field: " + name)
      return

    self.updated_properties[name] = self.old_properties[name]
    self.updated_properties[name]["select"] = {"name": value}

  def maybe_update_multi_select_field_internal(self, name:str, value: list):
    if (len(self.old_properties[name]["multi_select"]) != 0) & (not self.force_update):
      pprint("Skipping update for non-empty field: " + name)
      return

    list_tagged = []
    for item in value:
      list_tagged.append({"name": item})

    self.updated_properties[name] = self.old_properties[name]
    self.updated_properties[name]["multi_select"] = list_tagged

  def maybe_update_file_field_internal(self, name:str, value: str):
    if (len(self.old_properties[name]["files"]) != 0) & (not self.force_update):
      pprint("Skipping update for non-empty field: " + name)
      return

    title = self.old_properties["Title"]["title"][0]["plain_text"]
    self.updated_properties[name] = self.old_properties[name]
    self.updated_properties[name]["files"] = [{"external": {"url": value}, "type": "external", "name": "Poster for " + title}]