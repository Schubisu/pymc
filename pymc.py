from settings import *
from mpd import MPDClient

backstring = "".join([chr(c) for c in backdata]).replace(chr(0x00), "")
