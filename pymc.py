from settings import *
from mpd import MPDClient
import RPi.GPIO as GPIO
import MFRC522



class PyMC():

    # backstring = "".join([chr(c) for c in backdata]).replace(chr(0x00), "")

    self.key = [0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF]
    self.MIFAREReader = MFRC522.MFRC522()

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
        return status

    def read_block(self, blockid):
        status = self.authenticate(blockid)
        if status == self.MIFAREReader.MI_OK:
            self.MIFAREReader.MFRC522_Read(blockid)
            self.MIFAREReader.MFRC522_StopCrypto1()
        else:
            print("Authentication error")
            return 1
        return 0

    def write_block(self, blockid, content):
        status = self.authenticate(blockid)
        if status == self.MIFAREReader.MI_OK:
            self.MIFAREReader.MFRC522_Read(blockid)
            self.MIFAREReader.MFRC522_StopCrypto1()
        else:
            print("Authentication error")
            return 1
        return 0

    def play_next(self):
        pass

    def play_previous(self):
        pass

    def start_playback(self):
        pass

    def stop_playback(self):
        pass
