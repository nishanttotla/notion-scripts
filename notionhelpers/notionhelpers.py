from dataclasses import dataclass
from enum import Enum
from notion_client import Client
from pprint import pprint
import requests


class ColumnType(Enum):
  RICH_TEXT = 0
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
  SKIP_FILLED = 2


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
  __update_errors: str
  __properties: dict
  __pending_update: dict
  __sync_client: Client

  def __init__(self, row_id: str, properties: dict):
    """Basic constructor. Assumes that an empty row_id means the row is non-existent"""
    self.__row_id = row_id
    self.__update_errors = ""
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

  def print(self):
    """Print the current version of the row (includes pending updates)."""
    pprint(self.__properties)

  def get_update_errors(self) -> str:
    """Returns update errors."""
    return self.__update_errors

  def get_value(self, col_type: ColumnType, name: str):
    """Get value of field given type and name. Field must exist."""
    if col_type == ColumnType.RICH_TEXT:
      return self.__get_text_value_internal(name)
    elif col_type == ColumnType.TITLE:
      return self.__get_title_value_internal(name)
    elif col_type == ColumnType.DATE:
      return self.__get_date_value_internal(name)
    elif col_type == ColumnType.NUMBER:
      return self.__get_number_value_internal(name)
    elif col_type == ColumnType.SELECT:
      return self.__get_select_value_internal(name)
    elif col_type == ColumnType.MULTI_SELECT:
      return self.__get_multi_select_value_internal(name)
    elif col_type == ColumnType.FILES:
      return self.__get_files_value_internal(name)
    elif col_type == ColumnType.RELATION:
      return self.__get_relation_value_internal(name)
    else:
      raise NotImplementedError("No get_value implementation yet for type: " +
                                type.name)

  def __get_text_value_internal(self, name: str):
    value_list = []
    for rt in self.__properties[name]["rich_text"]:
      value_list.append(rt["plain_text"])
    return value_list

  def __get_title_value_internal(self, name: str):
    value_list = []
    for rt in self.__properties[name]["title"]:
      value_list.append(rt["plain_text"])
    return value_list

  def __get_date_value_internal(self, name: str):
    if self.__properties[name]["date"] == None:
      return None
    return self.__properties[name]["date"]["start"]

  def __get_number_value_internal(self, name: str):
    if self.__properties[name]["number"] == None:
      return None
    return self.__properties[name]["number"]

  def __get_select_value_internal(self, name: str):
    if self.__properties[name]["select"] == None:
      return None
    return self.__properties[name]["select"]["name"]

  def __get_multi_select_value_internal(self, name: str):
    value_list = []
    for ms in self.__properties[name]["multi_select"]:
      value_list.append(ms["name"])
    return value_list

  def __get_files_value_internal(self, name: str):
    value_list = []
    for f in self.__properties[name]["files"]:
      value_list.append(f["external"]["url"])
    return value_list

  def __get_relation_value_internal(self, name: str):
    value_list = []
    for rl in self.__properties[name]["relation"]:
      value_list.append(rl["id"])
    return value_list

  ############################## Creator Functions #############################

  def create_field(self,
                   col_type: ColumnType,
                   name: str,
                   value,
                   title: str = "",
                   relation_db: str = ""):
    """Create new field given type, name, value, and optional fields that specify configurations. Field should not exist."""
    if col_type == ColumnType.RICH_TEXT:
      self.__create_text_field_internal(name, value)
    elif col_type == ColumnType.TITLE:
      self.__create_title_field_internal(name, value)
    elif col_type == ColumnType.RELATION:
      self.__create_relation_field_internal(name, value)
    else:
      raise NotImplementedError("No create_field implementation yet for type: " +
                                type.name)

  def __create_text_field_internal(self, name: str, value: list):
    self.__properties[name] = {"type": "rich_text"}
    list_tagged = []
    for item in value:
      list_tagged.append({"plain_text": item, "text": {"content": item}})
    self.__properties[name]["rich_text"] = list_tagged
    self.__pending_update[name] = self.__properties[name]

  def __create_title_field_internal(self, name: str, value: str):
    self.__properties[name] = {"id": "title", "type": "title"}
    self.__properties[name]["title"] = [{
        "plain_text": value,
        "text": {
            "content": value
        }
    }]
    self.__pending_update[name] = self.__properties[name]

  def __create_relation_field_internal(self, name: str, value: list):
    self.__properties[name] = {"type": "relation", "has_more": False}
    list_tagged = []
    for item in value:
      list_tagged.append({"id": item})
    self.__properties[name]["relation"] = list_tagged
    self.__pending_update[name] = self.__properties[name]

  ############################## Setter Functions ##############################
  # The setter functions only update the data values. It is assumed that the
  # row provided in the constructor is a properly formed Notion row i.e. it has
  # the field types and ids already set. This means that we don't need to worry
  # about the full dictionaries for each property being empty - just the values
  # may be empty.

  # TODO: if the field name doesn't exist, the update function should create it.
  def update_value(
      self,
      col_type: ColumnType,
      name: str,
      value,
      title: str = "",
      update_config: NotionRowUpdateConfig = NotionRowUpdateConfig.REPLACE,
      relation_db: str = ""):
    """Update value of field given type, name, value, and optional fields that specify configurations. Field must exist."""
    if col_type == ColumnType.RICH_TEXT:
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
      raise NotImplementedError("No update_value implementation yet for type: " +
                                type.name)

  def __update_text_value_internal(self, name: str, value: str,
                                   update_config: NotionRowUpdateConfig):
    # TODO: Implement ability to append text instead of replacing it.
    # TODO: Don't update when there are no changes!
    self.__properties[name]["rich_text"] = [{
        "plain_text": value,
        "text": {
            "content": value
        }
    }]
    self.__pending_update[name] = self.__properties[name]

  def __update_date_value_internal(self, name: str, value: str):
    if not "date" in self.__properties[name]:
      self.__properties[name]["date"] = {"start": value}
      self.__pending_update[name] = self.__properties[name]
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
      # Only keep "name" in case the field was not empty.
      self.__properties[name]["select"] = {"name": value}
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
    # TODO: Don't update when there are no changes!
    self.__properties[name]["multi_select"] = list_tagged
    self.__pending_update[name] = self.__properties[name]

  def __update_file_value_internal(self, name: str, value: str, title: str,
                                   update_config: NotionRowUpdateConfig):
    # TODO: Implement ability to append file instead of replacing it.
    # TODO: Don't update when there are no changes!
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

  def clear_row(self):
    """Clear every field value."""
    for name in self.__properties:
      col_type = ColumnType[self.__properties[name]["type"].upper()]
      self.clear_value(col_type, name)

  def clear_value(self, col_type: ColumnType, name: str):
    """Clear field value by type and name. Field must exist."""
    if col_type == ColumnType.RICH_TEXT:
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
    elif col_type == ColumnType.RELATION:
      self.__clear_relation_value_internal(name)
    elif col_type == ColumnType.TITLE:
      self.__clear_title_value_internal(name)
    else:
      raise NotImplementedError("No clear_value implementation yet for type: " +
                                type.name)

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

  def __clear_relation_value_internal(self, name: str):
    self.__properties[name]["relation"] = []
    self.__pending_update[name] = self.__properties[name]

  def __clear_title_value_internal(self, name: str):
    self.__properties[name]["title"] = []
    self.__pending_update[name] = self.__properties[name]

  ############################## DB Call Functions #############################

  def create_new_db_row(self, database_id: str, icon: dict = {}) -> bool:
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
              "properties": self.__pending_update,
              "icon": icon
          })
      self.__row_id = resp["id"]
      self.__properties = resp["properties"]
      self.__pending_update = {}
      pprint(">>>> >>>> >>>> Created Notion row successfully")
    except Exception as e:
      pprint("Got exception while adding row for database_id: " + database_id)
      pprint("Exception: " + str(e))

  def update_db_row(self) -> str:
    """Update the page with the current properties."""
    if not self.__row_id:
      raise ValueError("Row ID not found for row")

    if self.__pending_update == {}:
      pprint("No pending updates for row ID: " + self.__row_id)
      return

    try:
      resp = self.__sync_client.pages.update(**{
          "page_id": self.__row_id,
          "properties": self.__pending_update
      })
      self.__pending_update = {}
      self.__update_errors = ""
      pprint(">>>> >>>> >>>> Updated Notion row successfully")
    except Exception as e:
      pprint("Got exception while update row for row ID: " + self.__row_id)
      pprint("Exception: " + str(e))
      self.__update_errors = "Exception while updating row: " + str(e)
    return self.__update_errors

  def delete_db_row(self):
    """Delete the page associated with the current row_id."""
    if not self.__row_id:
      raise ValueError("Row ID not found for row")

    try:
      resp = self.__sync_client.pages.update(**{
          "page_id": self.__row_id,
          "archived": True
      })
      self.__row_id = ""
      self.__pending_update = {}
      self.__properties = {}
      pprint(">>>> >>>> >>>> Deleted Notion row successfully")
    except Exception as e:
      pprint("Got exception while delete row for row ID: " + self.__row_id)
      pprint("Exception: " + str(e))