from dataclasses import dataclass
from enum import Enum
from notion_client import Client
from pprint import pprint
import requests


class ColumnType(Enum):
  TEXT = 0
  DATE = 1
  NUMBER = 2
  SELECT = 3
  MULTI_SELECT = 4
  FILES = 5
  CHECKBOX = 6
  RELATION = 7
  FORMULA = 8
  TITLE = 9


class NotionRowUpdateConfig(Enum):
  REPLACE = 0
  COMBINE = 1


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
  __row_id: str
  __properties: dict
  __pending_update: dict
  __sync_client: Client

  def __init__(self, row_id: str, properties: dict):
    """Basic constructor. Assumes that an empty row_id means the row is non-existent"""
    self.__row_id = row_id
    self.__properties = properties

    if not row_id:
      self.__pending_update = properties
    else:
      self.__pending_update = {}

  ############################## Setup Functions ###############################

  def set_client(self, client: Client):
    self.__sync_client = client

  ############################## Getter Functions ##############################

  def get_id(self) -> str:
    """Get the Notion row ID."""
    return self.__row_id

  def is_commit_required(self) -> bool:
    """Check if the value of the row has been updated since the last commit."""
    return (self.__pending_update == {})

  ############################## Creator Functions #############################

  def create_field(self,
                   col_type: ColumnType,
                   name: str,
                   value,
                   title: str = "",
                   relation_db: str = ""):
    """Create new field given type, name, value, and optional fields that specify configurations."""
    if col_type == ColumnType.TEXT:
      self.__create_text_field_internal(name, value)
    elif col_type == ColumnType.DATE:
      self.__create_date_field_internal(name, value)
    elif col_type == ColumnType.NUMBER:
      self.__create_number_field_internal(name, value)
    elif col_type == ColumnType.SELECT:
      self.__create_select_field_internal(name, value)
    elif col_type == ColumnType.MULTI_SELECT:
      self.__create_multi_select_field_internal(name, value)
    elif col_type == ColumnType.FILES:
      self.__create_file_field_internal(name, value, title)
    elif col_type == ColumnType.RELATION:
      self.__create_relation_field_internal(name, value, relation_db)
    else:
      raise NotImplementedError("No implementation yet for type: " + type.name)

  ############################## Setter Functions ##############################
  # The setter functions only update the data values. It is assumed that the
  # row provided in the constructor is a properly formed Notion row i.e. it has
  # the field types and ids already set. This means that we don't need to worry
  # about the full dictionaries for each property being empty - just the values
  # may be empty.

  def update_value(
      self,
      col_type: ColumnType,
      name: str,
      value,
      title: str = "",
      update_config: NotionRowUpdateConfig = NotionRowUpdateConfig.REPLACE,
      relation_db: str = ""):
    """Update value of field given type, name, value, and optional fields that specify configurations."""
    if col_type == ColumnType.TEXT:
      self.__update_text_value_internal(name, value, update_config)
    elif col_type == ColumnType.DATE:
      self.__update_date_value_internal(name, value)
    elif col_type == ColumnType.NUMBER:
      self.__update_number_value_internal(name, value)
    elif col_type == ColumnType.SELECT:
      self.__update_select_value_internal(name, value)
    elif col_type == ColumnType.MULTI_SELECT:
      self.__update_multi_select_value_internal(name, value, update_config)
    elif col_type == ColumnType.FILES:
      self.__update_file_value_internal(name, value, title, update_config)
    elif col_type == ColumnType.RELATION:
      self.__update_relation_value_internal(name, value, update_config,
                                            relation_db)
    else:
      raise NotImplementedError("No implementation yet for type: " + type.name)

  def __update_text_value_internal(self, name: str, value: str,
                                   update_config: NotionRowUpdateConfig):
    # TODO: Implement ability to append text instead of replacing it.
    self.__properties[name]["rich_text"] = [{
        "plain_text": value,
        "text": {
            "content": value
        }
    }]

  def __update_date_value_internal(self, name: str, value: str):
    if self.__properties[name]["date"] == None:
      self.__properties[name]["date"] = {"start": value}
      self.__pending_update[name] = self.__properties[name]
    elif self.__properties[name]["date"]["start"] != value:
      self.__properties[name]["date"]["start"] = value
      self.__pending_update[name] = self.__properties[name]
    else:
      pprint("Update not required for field: " + name)

  def __update_number_value_internal(self, name: str, value: int):
    if self.__properties[name]["number"] == None:
      self.__properties[name]["number"] = value
      self.__pending_update[name] = self.__properties[name]
    elif self.__properties[name]["number"] != value:
      self.__properties[name]["number"] = value
      self.__pending_update[name] = self.__properties[name]
    else:
      pprint("Update not required for field: " + name)

  def __update_select_value_internal(self, name: str, value: str):
    if self.__properties[name]["select"] == None:
      self.__properties[name]["select"] = {"name": value}
      self.__pending_update[name] = self.__properties[name]
    elif self.__properties[name]["select"]["name"] != value:
      self.__properties[name]["select"]["name"] = value
      self.__pending_update[name] = self.__properties[name]
    else:
      pprint("Update not required for field: " + name)

  def __update_multi_select_value_internal(
      self, name: str, value: list, update_config: NotionRowUpdateConfig):
    list_tagged = []
    for item in value:
      list_tagged.append({"name": item})

    # TODO: Implement ability to perform a union of the current and new lists
    # and also figure out how to pass it in every function call
    self.__properties[name]["multi_select"] = list_tagged
    self.__pending_update[name] = self.__properties[name]

  def __update_file_value_internal(self, name: str, value: str, title: str,
                                   update_config: NotionRowUpdateConfig):
    # TODO: Implement ability to append file instead of replacing it.

    if not title:
      title = "Unnamed file"
    self.__properties[name]["files"] = [{
        "external": {
            "url": value
        },
        "type": "external",
        "name": "Poster for " + title
    }]
    self.__pending_update[name] = self.__properties[name]

  def __update_relation_value_internal(self, name: str, value: list,
                                       update_config: NotionRowUpdateConfig,
                                       relation_db: str):
    if not relation_db:
      raise ValueError("No relation_db passed for updating RELATION field: ",
                       name)
    # TODO: What happens if a duplicate is added here?
    list_tagged = []
    for item in value:
      list_tagged.append({"id": item})

    if update_config == NotionRowUpdateConfig.REPLACE:
      self.__properties[name]["relation"] = list_tagged
    elif update_config == NotionRowUpdateConfig.COMBINE:
      self.__properties[name]["relation"].extend(list_tagged)

    self.__pending_update[name] = self.__properties[name]

  ############################# Clearing Functions #############################

  def clear_value(self, col_type: ColumnType, name: str):
    """Clear field value by type and name."""
    if col_type == ColumnType.TEXT:
      self.__clear_text_value_internal(name)
    elif col_type == ColumnType.DATE:
      self.__clear_date_value_internal(name)
    elif col_type == ColumnType.NUMBER:
      self.__clear_number_value_internal(name)
    elif col_type == ColumnType.SELECT:
      self.__clear_select_value_internal(name)
    elif col_type == ColumnType.MULTI_SELECT:
      self.__clear_multi_select_value_internal(name)
    elif col_type == ColumnType.FILES:
      self.__clear_file_value_internal(name)
    elif col_type == ColumnType.FORMULA:
      self.__clear_formula_value_internal(name)
    else:
      raise NotImplementedError("No implementation yet for type: " + type.name)

  def __clear_text_value_internal(self, name: str):
    self.__properties[name]["rich_text"] = []
    self.__pending_update[name] = self.__properties[name]

  def __clear_date_value_internal(self, name: str):
    self.__properties[name]["date"] = None
    self.__pending_update[name] = self.__properties[name]

  def __clear_number_value_internal(self, name: str):
    self.__properties[name]["number"] = None
    self.__pending_update[name] = self.__properties[name]

  def __clear_select_value_internal(self, name: str):
    self.__properties[name]["select"] = None
    self.__pending_update[name] = self.__properties[name]

  def __clear_multi_select_value_internal(self, name: str):
    self.__properties[name]["multi_select"] = []
    self.__pending_update[name] = self.__properties[name]

  def __clear_file_value_internal(self, name: str):
    self.__properties[name]["files"] = []
    self.__pending_update[name] = self.__properties[name]

  def __clear_formula_value_internal(self, name: str):
    self.__properties[name].pop("formula", None)
    self.__pending_update[name] = self.__properties[name]

  ############################## DB Call Functions #############################

  def create_db_row(self, database_id: str) -> bool:
    """Create a new page with the current properties in the provided database_id."""
    if not database_id:
      raise ValueError("Cannot create row without a database_id")

    if self.__row_id:
      raise ValueError("Row already exists for ID: " + self.__row_id)

    if self.__pending_update == {}:
      raise ValueError("Cannot write empty properties to database ID: " +
                       database_id)

    try:
      resp = self.__sync_client.pages.create(
          **{
              "parent": {
                  "database_id": database_id
              },
              "properties": self.__pending_update
          })
      self.__row_id = resp["id"]
      self.__properties = resp["properties"]
      self.__pending_update = {}
    except Exception as e:
      pprint("Got exception while adding row for database_id: " + database_id)
      pprint("Exception: " + str(e))

  def update_db_row(self):
    """Update the page with the current properties."""
    if not self.__row_id:
      raise ValueError("Row ID not found for row")

    if self.__pending_update == {}:
      pprint("No pending updates for row ID: " + self.__row_id)

    try:
      resp = self.__sync_client.pages.update(**{
          "page_id": self.__row_id,
          "properties": self.__pending_update
      })
      self.__pending_update = {}
    except Exception as e:
      pprint("Got exception while update row for row ID: " + self.__row_id)
      pprint("Exception: " + str(e))
