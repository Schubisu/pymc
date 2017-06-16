import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# mpd connection settings
MPD_PORT = 6600
MPD_IP = "localhost"

# block to read and write from MIFARE card
PYMC_BLOCK = 4
PYMC_KEY = [0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF]

# sectors in block for specific mpd data
# PLAYLIST_NUMBER = 0
TRACK_NUMBER = 1
PLAYLIST_REPEAT = 2
PLAYLIST_SHUFFLE = 3
TRACK_TIME_MSB = 4
TRACK_TIME_LSB = 5

# where to store the {uid: playlist} dict
PLAYLIST_PATH = os.path.join(BASE_DIR, 'playlists.json')

# gpio pins for push buttons
BTN_PLAY = 7
BTN_STOP = 11
BTN_NEXT = 13
BTN_PREVIOUS = 15
