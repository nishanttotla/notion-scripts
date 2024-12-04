import sys
from pprint import pprint
from datetime import datetime
from tvshowsupdater import UpdateFromTmdb

input_imdb_ids = sys.argv[1:]

pprint("+++++++++++ Starting update_from_tmdb run at " +
       str(datetime.now().strftime('%Y-%m-%d %H:%M:%S')))

updater = UpdateFromTmdb(imdb_ids=input_imdb_ids)
updater.update_shows_and_seasons()