import os
from notion_client import Client
from pprint import pprint

# Environment variable must be exported for use with os.environ, for example:
# $ export NOTION_TOKEN="secret_xyz"
# For ease of use, define an env_vars.sh file and add it to .gitignore and run:
# $ source env_vars.sh


notion = Client(auth=os.environ["NOTION_TOKEN"])

list_users_response = notion.users.list()
pprint(list_users_response)

# Integration permissions must be updated to allow read/write content
# In addition, the specific page(s) must also be explicitly shared with
# the integration. It's a two way sharing.
my_page = notion.databases.query(
    **{
        "database_id": os.environ["MOVIES_DB"],
        "filter": {
            "property": "Title",
            "rich_text": {
                "contains": "Couple",
            },
        },
    }
)

pprint("Printing search results:")

for result in my_page["results"]:
	pprint(result)