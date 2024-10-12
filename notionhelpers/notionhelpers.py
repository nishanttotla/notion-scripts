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


class NotionRowUpdateConfig(Enum):
  UNKNOWN = 0
  COMBINE = 1
  REPLACE = 2


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
class NotionRow():
  row_id: str
  properties: dict
  commit_required: bool

  def __init__(self, row_id: str, properties: dict):
    self.row_id = row_id
    self.properties = properties
    self.commit_required = False

  ############################## Getter Functions ##############################

  def get_id(self):
    return row_id

  def get_properties(self):
    return properties

  def commit_required(self):
    return self.commit_required

  ############################## Setter Functions ##############################
  # The setter functions only update the data values. It is assumed that the
  # row provided in the constructor is a properly formed Notion row i.e. it has
  # the field types and ids already set. This means that we don't need to worry
  # about the full dictionaries for each property being empty - just the values
  # may be empty.

  def update_field(self, col_type: ColumnType, name: str, value):
    # TODO: For Python 3.10 and above, switch case statements can be used.
    # Validate input types and call the right update function.
    if col_type == ColumnType.UNKNOWN:
      raise ValueError("Type was not set for field: " + name)
    elif col_type == ColumnType.TEXT:
      self.update_text_field_internal(name, value)
    elif col_type == ColumnType.DATE:
      self.update_date_field_internal(name, value)
    elif col_type == ColumnType.NUMBER:
      self.update_number_field_internal(name, value)
    elif col_type == ColumnType.SELECT:
      self.update_select_field_internal(name, value)
    elif col_type == ColumnType.MULTI_SELECT:
      self.update_multi_select_field_internal(name, value)
    elif col_type == ColumnType.FILE:
      self.update_file_field_internal(name, value)
    else:
      raise NotImplementedError("No implementation yet for type: " + type.name)

  def update_text_field_internal(self, name: str, value: str):
    # TODO: Implement ability to append text instead of replacing it.
    self.properties[name]["rich_text"] = [{
        "plain_text": value,
        "text": {
            "content": value
        }
    }]
    self.commit_required = True

  def update_date_field_internal(self, name: str, value: str):
    if self.properties[name]["date"] == None:
      self.properties[name]["date"] = {"start": value}
      self.commit_required = True
    elif self.properties[name]["date"]["start"] != value:
      self.properties[name]["date"]["start"] = value
      self.commit_required = True
    else:
      pprint("Update not required for field: " + name)

  def update_number_field_internal(self, name: str, value: int):
    if self.properties[name]["number"] == None:
      self.properties[name]["number"] = value
      self.commit_required = True
    elif self.properties[name]["number"] != value:
      self.properties[name]["number"] = value
      self.commit_required = True
    else:
      pprint("Update not required for field: " + name)

  def update_select_field_internal(self, name: str, value: str):
    if self.properties[name]["select"] == None:
      self.properties[name]["select"] = {"name": value}
      self.commit_required = True
    elif self.properties[name]["select"]["name"] != value:
      self.properties[name]["select"]["name"] = value
      self.commit_required = True
    else:
      pprint("Update not required for field: " + name)

  def update_multi_select_field_internal(self, name: str, value: list):
    list_tagged = []
    for item in value:
      list_tagged.append({"name": item})

    # TODO: Implement ability to perform a union of the current and new lists
    # and also figure out how to pass it in every function call
    self.properties[name]["multi_select"] = list_tagged
    self.commit_required = True

  def update_file_field_internal(self, name: str, value: str):
    # TODO: Implement ability to append file instead of replacing it.

    # TODO: Pass title as a parameter
    title = "Unnamed file"
    self.properties[name]["files"] = [{
        "external": {
            "url": value
        },
        "type": "external",
        "name": "Poster for " + title
    }]

  ############################# Clearing Functions #############################

  def clear_field(self, col_type: ColumnType, name: str):
    # TODO: For Python 3.10 and above, switch case statements can be used.
    # Validate input types and call the right update function.
    if col_type == ColumnType.UNKNOWN:
      raise ValueError("Type was not set for field: " + name)
    elif col_type == ColumnType.TEXT:
      self.clear_text_field_internal(name, value)
    elif col_type == ColumnType.DATE:
      self.clear_date_field_internal(name, value)
    elif col_type == ColumnType.NUMBER:
      self.clear_number_field_internal(name, value)
    elif col_type == ColumnType.SELECT:
      self.clear_select_field_internal(name, value)
    elif col_type == ColumnType.MULTI_SELECT:
      self.clear_multi_select_field_internal(name, value)
    elif col_type == ColumnType.FILE:
      self.clear_file_field_internal(name, value)
    else:
      raise NotImplementedError("No implementation yet for type: " + type.name)

  def clear_text_field_internal(self, name: str):
    self.properties[name]["rich_text"] = []
    self.commit_required = True

  def clear_date_field_internal(self, name: str):
    self.properties[name]["date"] = None
    self.commit_required = True

  def clear_number_field_internal(self, name: str):
    self.properties[name]["number"] = None
    self.commit_required = True

  def clear_select_field_internal(self, name: str):
    self.properties[name]["select"] = None
    self.commit_required = True

  def clear_multi_select_field_internal(self, name: str):
    self.properties[name]["multi_select"] = []
    self.commit_required = True

  def clear_file_field_internal(self, name: str):
    self.properties[name]["files"] = []
    self.commit_required = True
