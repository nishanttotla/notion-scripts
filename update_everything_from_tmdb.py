import sys
from pprint import pprint
from datetime import datetime
from tvshowsupdater import UpdateFromTmdb

pprint("+++++++++++ Starting update_from_tmdb run at " +
       str(datetime.now().strftime('%Y-%m-%d %H:%M:%S')))

updater = UpdateFromTmdb()
updater.update_shows_and_seasons()

pprint("+++++++++++ Starting update_watchlist_from_tmdb run at " +
       str(datetime.now().strftime('%Y-%m-%d %H:%M:%S')))

updater = UpdateFromTmdb(is_watchlist=True)
updater.update_watchlist()