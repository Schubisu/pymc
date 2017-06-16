from settings import *
from mpd import MPDClient
import RPi.GPIO as GPIO
import MFRC522
import json

# backstring = "".join([chr(c) for c in backdata]).replace(chr(0x00), "")


class PyMC():
    def __init__(self):
        self.uid = None
        self.key = [0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF]

        self.mpd = MPDClient()
        self.read_playlists()
        self.track_number = 0
        self.track_time = 0

    def authenticate(self, blockid):
        self.MIFAREReader = MFRC522.MFRC522()
        (status, TagType) = self.MIFAREReader.MFRC522_Request(self.MIFAREReader.PICC_REQIDL)
        if status == self.MIFAREReader.MI_OK:
            (status, uid) = self.MIFAREReader.MFRC522_Anticoll()
            if status == self.MIFAREReader.MI_OK:
                self.MIFAREReader.MFRC522_SelectTag(uid)
                status = self.MIFAREReader.MFRC522_Auth(self.MIFAREReader.PICC_AUTHENT1A, blockid, self.key, uid)
            else:
                print("error: anticoll failed")
                # GPIO.cleanup()
                return (1, None)
        else:
            print("error: no card detected")
            # GPIO.cleanup()
            return (1, None)
        return (status, uid)

    def read_block(self, blockid):
        status, uid = self.authenticate(blockid)
        if status == self.MIFAREReader.MI_OK:
            self.uid = str(uid)
            (blkid, data) = self.MIFAREReader.MFRC522_Read(blockid)
            self.MIFAREReader.MFRC522_StopCrypto1()
        else:
            print("Authentication error")
            # GPIO.cleanup()
            return 1
        # GPIO.cleanup()
        return data

    def write_block(self, blockid, content):
        status, uid = self.authenticate(blockid)
        # if status == self.MIFAREReader.MI_OK:
        print('writing block: {}'.format(content))
        if str(uid) == self.uid:
            self.MIFAREReader.MFRC522_Write(blockid, content)
            self.MIFAREReader.MFRC522_StopCrypto1()
        else:
            print("Authentication error")
            # GPIO.cleanup()
            return 1
        # GPIO.cleanup()
        return 0

    def read_pymc(self):
        pymcdata = self.read_block(PYMC_BLOCK)
        if not pymcdata == 1:
            self.track_number = int(pymcdata[TRACK_NUMBER])
            self.playlist_repeat = int(pymcdata[PLAYLIST_REPEAT])
            self.playlist_shuffle = int(pymcdata[PLAYLIST_SHUFFLE])
            self.track_time = int(pymcdata[TRACK_TIME_MSB] * 100) + int(pymcdata[TRACK_TIME_LSB])

    def write_pymc(self):
        pymcdata = [0] * 16
        pymcdata[TRACK_NUMBER] = int(self.track_number)
        pymcdata[PLAYLIST_REPEAT] = int(self.playlist_repeat)
        pymcdata[PLAYLIST_SHUFFLE] = int(self.playlist_shuffle)
        pymcdata[TRACK_TIME_MSB] = int(self.track_time / 100)
        pymcdata[TRACK_TIME_LSB] = int(self.track_time % 100)
        self.write_block(PYMC_BLOCK, pymcdata)

    def connect_mpd(self):
        try:
            self.mpd.connect(MPD_IP, MPD_PORT)
        except:
            pass

    def play_next(self):
        self.connect_mpd()
        self.mpd.next()
        self.mpd_to_card()

    def play_previous(self):
        self.connect_mpd()
        self.mpd.previous()
        self.mpd_to_card()

    def start_playback(self):
        self.connect_mpd()
        self.read_pymc()
        self.mpd.clear()
        self.mpd.load(self.playlists[self.uid])
        self.mpd.play(self.track_number)
        if self.track_time > 0:
            self.mpd.seek(self.track_number, self.track_time)

    def stop_playback(self):
        self.connect_mpd()
        self.mpd.pause()
        self.mpd_to_card()
        self.mpd.stop()

    def mpd_to_card(self):
        self.connect_mpd()
        mpd_status = self.mpd.status()
        if mpd_status:
            self.track_number = mpd_status.get('song', 0)
            self.playlist_repeat = mpd_status.get('repeat', 0)
            self.playlist_shuffle = mpd_status.get('random', 0)
            self.track_time = mpd_status.get('time', 0)
            if self.track_time != 0:
                # time is given in 'seconds:miliseconds', convert to full seconds int
                self.track_time = int(str(self.track_time.split(':')[0]))
            self.write_pymc()

    def read_playlists(self):
        try:
            with open(PLAYLIST_PATH, 'r') as _in:
                self.playlists = json.load(_in)
        except Exception as e:
            print('could not open playlists file')
            print(e)
        if not self.playlists:
            self.playlists = dict()

    def write_playlists(self):
        try:
            with open(PLAYLIST_PATH, 'w') as _out:
                json.dump(self.playlists, _out)
        except Exception as e:
            print('could not write playlists file')
            print(e)

    def create_playlist(self, playlistname):
        self.connect_mpd()
        try:
            self.mpd.save(playlistname)
        except:
            pass
        self.read_block(PYMC_BLOCK)
        self.mpd_to_card()
        self.playlists[self.uid] = playlistname
        self.write_playlists()
