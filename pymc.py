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
        self.MIFAREReader = MFRC522.MFRC522()

        self.mpd = MPDClient()
        self.read_playlists()

    def authenticate(self, blockid):
        (status, TagType) = self.MIFAREReader.MFRC522_Request(self.MIFAREReader.PICC_REQIDL)
        if status == self.MIFAREReader.MI_OK:
            (status, uid) = self.MIFAREReader.MFRC522_Anticoll()
            if status == self.MIFAREReader.MI_OK:
                self.MIFAREReader.MFRC522_SelectTag(uid)
                status = self.MIFAREReader.MFRC522_Auth(self.MIFAREReader.PICC_AUTHENT1A, blockid, self.key, uid)
            else:
                print("error: anticoll failed")
                return 1
        else:
            print("error: no card detected")
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
        (status, uid) = self.authenticate(settings.PYMC_BLOCK)
        if status == self.MIFAREReader.MI_OK:
            pymcdata = self.read_block(settings.PYMC_BLOCK)
            GPIO.cleanup()
            if not pymcdata == 1:
                self.playlist_number = pymcdata[settings.PLAYLIST_NUMBER]
                self.track_number = pymcdata[settings.TRACK_NUMBER]
                self.playlist_repeat = pymcdata[settings.PlAYLIST_REPEAT]
                self.playlist_shuffle = pymcdata[settings.PLAYLIST_SHUFFLE]

    def write_pymc(self):
        (status, uid) = self.authenticate(settings.PYMC_BLOCK)
        if status == self.MIFAREReader.MI_OK:
            pymcdata = [0] * 16
            pymcdata[settings.PLAYLIST_NUMBER] = self.playlist_number
            pymcdata[settings.TRACK_NUMBER] = self.track_number
            pymcdata[settings.PlAYLIST_REPEAT] = self.playlist_repeat
            pymcdata[settings.PLAYLIST_SHUFFLE] = self.playlist_shuffle
            self.write_block(settings.PYMC_BLOCK, pymcdata)
            GPIO.cleanup()

    def connect_mpd(self):
        self.mpd.connect(settings.MPD_IP, settings.MPD_PORT)

    def play_next(self):
        self.connect_mpd()
        self.mpd.next()
        status, uid = self.authenticate(settings.PYMC_BLOCK)
        if str(uid) == self.uid:
            self.mpd_to_card()

    def play_previous(self):
        self.connect_mpd()
        self.mpd.previous()
        status, uid = self.authenticate(settings.PYMC_BLOCK)
        if str(uid) == self.uid:
            self.mpd_to_card()

    def start_playback(self):
        self.connect_mpd()
        status, uid = self.authenticate(settings.PYMC_BLOCK)
        if not str(uid) == self.uid:
            self.read_pymc()
            self.uid = str(uid)
            if not self.uid in self.playlists.keys():
                self.mpd_to_card()
            self.mpd.load(self.playlists[self.uid])
            self.mpd.play(self.track_number)

        else:
            self.mpd.play()

    def stop_playback(self):
        self.connect_mpd()
        self.mpd.stop()
        status, uid = self.authenticate(settings.PYMC_BLOCK)
        if str(uid) == self.uid:
            self.mpd_to_card()

    def mpd_to_card(self):
        self.connect_mpd()
        mpd_status = self.mpd.status()
        if status:
            # self.playlist_number
            self.track_number = mpd_status['song']
            self.playlist_repeat = mpd_status['repeat']
            self.playlist_shuffle = mpd_status['random']
            self.track_time = mpd_status['time']
            self.write_pymc()

    def read_playlists(self):
        try:
            with open(settings.PLAYLIST_PATH, 'r') as _in:
                self.playlists = json.load(_in)
        except:
            print('could not open playlists file')

    def write_playlists(self):
        try:
            with open(settings.PLAYLIST_PATH, 'w') as _out:
                self.playlists = json.dump(_out, self.playlists)
        except:
            print('could not write playlists file')
