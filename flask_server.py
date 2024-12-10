import sys
from pprint import pprint
from datetime import datetime
from tvshowsupdater import UpdateFromTmdb
from flask import Flask, render_template, request

app = Flask(__name__)


@app.route('/')
def index():
  return render_template('index.html')


@app.route('/update_result', methods=['POST'])
def update_result():
  imdb_ids = request.form["imdbIds"]
  action_log = []
  if not imdb_ids:
    action_log.append("Will not run script with empty IMDB ID.")
  else:
    pprint("+++++++++++ Starting update run for IMDB ID: " + imdb_ids + " at " +
           str(datetime.now().strftime('%Y-%m-%d %H:%M:%S')))
    updater = UpdateFromTmdb(imdb_ids=[imdb_ids])
    action_log = updater.update_shows_and_seasons()
  if action_log:
    action_log.insert(0, "Failed to update IMDB ID: " + imdb_ids)
  else:
    action_log.insert(0, "Successfully updated IMDB ID: " + imdb_ids)
  return render_template('update_result.html', result=action_log)


if __name__ == '__main__':
  app.run(debug=True)