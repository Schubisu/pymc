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
        self.playlists = dict()

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
                GPIO.cleanup()
                return 1
        else:
            print("error: no card detected")
            GPIO.cleanup()
            return 1
        return (status, uid)

    def read_block(self, blockid):
        status = self.authenticate(blockid)
        if status == self.MIFAREReader.MI_OK:
            (blkid, data) = self.MIFAREReader.MFRC522_Read(blockid)
            self.MIFAREReader.MFRC522_StopCrypto1()
        else:
            print("Authentication error")
            GPIO.cleanup()
            return 1
        GPIO.cleanup()
        return data

    def write_block(self, blockid, content):
        status = self.authenticate(blockid)
        if status == self.MIFAREReader.MI_OK:
            self.MIFAREReader.MFRC522_Write(blockid, content)
            self.MIFAREReader.MFRC522_StopCrypto1()
        else:
            print("Authentication error")
            GPIO.cleanup()
            return 1
        GPIO.cleanup()
        return 0

    def read_pymc(self):
        (status, uid) = self.authenticate(PYMC_BLOCK)
        if status == self.MIFAREReader.MI_OK:
            pymcdata = self.read_block(PYMC_BLOCK)
            GPIO.cleanup()
            if not pymcdata == 1:
                # self.playlist_number = pymcdata[PLAYLIST_NUMBER]
                self.track_number = pymcdata[TRACK_NUMBER]
                self.playlist_repeat = pymcdata[PlAYLIST_REPEAT]
                self.playlist_shuffle = pymcdata[PLAYLIST_SHUFFLE]

    def write_pymc(self):
        (status, uid) = self.authenticate(PYMC_BLOCK)
        if status == self.MIFAREReader.MI_OK:
            pymcdata = [0] * 16
            # pymcdata[PLAYLIST_NUMBER] = self.playlist_number
            pymcdata[TRACK_NUMBER] = self.track_number
            pymcdata[PLAYLIST_REPEAT] = self.playlist_repeat
            pymcdata[PLAYLIST_SHUFFLE] = self.playlist_shuffle
            self.write_block(PYMC_BLOCK, pymcdata)
            GPIO.cleanup()

    def connect_mpd(self):
        try:
            self.mpd.connect(MPD_IP, MPD_PORT)
        except:
            pass

    def play_next(self):
        self.connect_mpd()
        self.mpd.next()
        status, uid = self.authenticate(PYMC_BLOCK)
        if str(uid) == self.uid:
            self.mpd_to_card()

    def play_previous(self):
        self.connect_mpd()
        self.mpd.previous()
        status, uid = self.authenticate(PYMC_BLOCK)
        if str(uid) == self.uid:
            self.mpd_to_card()

    def start_playback(self):
        self.connect_mpd()
        status, uid = self.authenticate(PYMC_BLOCK)
        if not str(uid) == self.uid:
            self.read_pymc()
            self.uid = str(uid)
            if not self.uid in self.playlists.keys():
                self.mpd_to_card()
            self.mpd.load(self.playlists[self.uid])
            track_number = self.track_number
        else:
            track_number = 0

        self.mpd.play(track_number)

    def stop_playback(self):
        self.connect_mpd()
        self.mpd.stop()
        status, uid = self.authenticate(PYMC_BLOCK)
        if str(uid) == self.uid:
            self.mpd_to_card()

    def mpd_to_card(self):
        self.connect_mpd()
        mpd_status = self.mpd.status()
        if mpd_status:
            # self.playlist_number
            self.track_number = mpd_status['song']
            self.playlist_repeat = mpd_status['repeat']
            self.playlist_shuffle = mpd_status['random']
            # self.track_time = mpd_status['time']
            self.write_pymc()

    def read_playlists(self):
        try:
            with open(PLAYLIST_PATH, 'r') as _in:
                self.playlists = json.load(_in)
        except Exception as e:
            print('could not open playlists file')
            print(e)
            print('creating new one')
            self.playlists = dict()
            self.write_playlists()
        if not self.playlists:
            self.playlists = dict()

    def write_playlists(self):
        try:
            with open(PLAYLIST_PATH, 'w') as _out:
                self.playlists = json.dump(self.playlists, _out)
        except Exception as e:
            print('could not write playlists file')
            print(e)

    def create_playlist(self, playlistname):
        status, uid = self.authenticate(PYMC_BLOCK)
        print(uid)
        if status == self.MIFAREReader.MI_OK:
            self.connect_mpd()
            try:
                self.mpd.save(playlistname)
            except:
                pass
            self.playlists[str(uid)] = playlistname
            self.mpd_to_card()
            self.write_playlists()
        else:
            print("authentication failed")
