import os
from notion_client import Client
from pprint import pprint

# Environment variable must be exported for use with os.environ, for example:
# $ export NOTION_TOKEN="secret_xyz"
# For ease of use, define an env_vars.sh file and add it to .gitignore and run:
# $ source env_vars.sh


def database_query_all(notion: Client, databaseID: str) -> dict:
  """Return the query of all the databases."""
  data = notion.databases.query(databaseID)
  database_object = data['object']
  has_more = data['has_more']
  next_cursor = data['next_cursor']
  while has_more == True:
      data_while = notion.databases.query(databaseID, start_cursor=next_cursor)
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


notion = Client(auth=os.environ["NOTION_TOKEN"])
list_users_response = notion.users.list()
pprint(list_users_response)

# Integration permissions must be updated to allow read/write content
# In addition, the specific page(s) must also be explicitly shared with
# the integration. It's a two way sharing.
my_page = notion.databases.query(
    **{
        "database_id": os.environ["MOVIES_DB"],
        # "filter": {
        #     "property": "Title",
        #     "rich_text": {
        #         "contains": "Couple",
        #     },
        # },
    }
)

full_db = database_query_all(notion, os.environ["MOVIES_DB"])
pprint(len(full_db["results"]))


