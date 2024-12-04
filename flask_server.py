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
  imdb_id = request.form['imdbId']
  pprint("+++++++++++ Starting update run for IMDB ID: " + imdb_id + " at " +
         str(datetime.now().strftime('%Y-%m-%d %H:%M:%S')))
  updater = UpdateFromTmdb(imdb_ids=[imdb_id])
  updater.update_shows_and_seasons()
  return render_template('update_result.html', result=imdb_id)


if __name__ == '__main__':
  app.run(debug=True)