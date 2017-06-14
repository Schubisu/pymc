from settings import *
from mpd import MPDClient
import RPi.GPIO as GPIO
import MFRC522

def read_block(blockid):


backstring = "".join([chr(c) for c in backdata]).replace(chr(0x00), "")

key = [0xFF,0xFF,0xFF,0xFF,0xFF,0xFF]
MIFAREReader = MFRC522.MFRC522()
(status, TagType) = MIFAREReader.MFRC522_Request(MIFAREReader.PICC_REQIDL)

if status == MIFAREReader.MI_OK:
    (status, uid) = MIFAREReader.MFRC522_Anticoll()
    if status == MIFAREReader.MI_OK:
        MIFAREReader.MFRC522_SelectTag(uid)
        status = MIFAREReader.MFRC522_Auth(MIFAREReader.PICC_AUTHENT1A, 8, key, uid)
        if status == MIFAREReader.MI_OK:
            MIFAREReader.MFRC522_Read(8)
            MIFAREReader.MFRC522_StopCrypto1()
        else:
            print("Authentication error")
