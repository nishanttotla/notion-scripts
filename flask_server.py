import sys
from pprint import pprint
from datetime import datetime
from tvshowsupdater import search_from_tmdb
from tvshowsupdater import AddFromTmdb
from tvshowsupdater import UpdateFromTmdb
from flask import Flask, render_template, request

app = Flask(__name__)


@app.route("/")
def index():
  return render_template("index.html")


@app.route("/search")
def search():
  return render_template("search.html")


@app.route("/search_results", methods=["POST"])
def search_results():
  search_query = request.form["searchQuery"]
  search_results = search_from_tmdb(search_query)
  return render_template("search_results.html", result=search_results)


@app.route("/add_to_watchlist", methods=["POST"])
def add_to_watchlist():
  tmdb_id = request.form["tmdbId"]

  print("TMDB ID: " + tmdb_id, flush=True)
  add_entity = AddFromTmdb(tmdb_id=tmdb_id, is_watchlist=True)

  # If there is an error message, then just return that, else return the
  # full entity.
  if add_entity.get_error_message():
    return render_template("search.html", result=add_entity.get_error_message())

  resp = ""
  try:
    add_entity.create_show_notion_row()
    resp = "Successfully added " + add_entity.get_imdb_id() + " to Watchlist."
  except Exception as e:
    resp = "Could not add " + add_entity.get_imdb_id(
    ) + " to watchlist: " + str(e)
  return render_template("search.html", result=resp)


@app.route("/update_result", methods=["GET", "POST"])
def update_result():
  imdb_ids = ""
  if request.method == "GET":
    imdb_ids = request.args.get("imdbIds", "").replace(" ", "")
  elif request.method == "POST":
    imdb_ids = request.form["imdbIds"].replace(" ", "")
  action_log = []
  if not imdb_ids:
    action_log.append("Cannot import with empty IMDB IDs.")
  elif imdb_ids == "updateall":
    pprint("+++++++++++ Starting update run for all IMDB IDs: " + " at " +
           str(datetime.now().strftime('%Y-%m-%d %H:%M:%S')))
    updater = UpdateFromTmdb()
    action_log = updater.update_shows_and_seasons()
  else:
    split_imdb_ids = imdb_ids.split(",")
    pprint("+++++++++++ Starting update run for IMDB IDs: " + imdb_ids +
           " at " + str(datetime.now().strftime('%Y-%m-%d %H:%M:%S')))
    updater = UpdateFromTmdb(imdb_ids=split_imdb_ids)
    action_log = updater.update_shows_and_seasons()

  if action_log:
    action_log.insert(
        0, "Received some errors while importing IMDB IDs: " + imdb_ids)
  else:
    action_log.insert(0, "Successfully imported IMDB IDs: " + imdb_ids)
  return render_template("update_result.html", result=action_log)


if __name__ == "__main__":
  app.run(debug=True)