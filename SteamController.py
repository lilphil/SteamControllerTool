import time
import binascii
import pprint
import struct
import numpy as np
import logging
from ctypes import c_uint8, c_uint16, c_uint32

from ValveSoftwareWiredController import ValveSoftwareWiredController
from ValveSoftwareWiredControllerBootloader import ValveSoftwareWiredControllerBootloader

log = logging.getLogger(__name__)

class SteamController:
    """
    If you want to wait for the controller to arrive later, init with ignoreMissingController
    """
    def __init__(self, ignoreMissingController = False):
        self.bootloader = None
        self.sc = None
        # If we start up in bootloader mode, its possible that there is no firmware on the device so normal mode may not be available
        self.initial_bootloader_mode = False

        try:
            self.sc = ValveSoftwareWiredController();
        except:
            log.warn("Could not open controller in normal mode")

        if self.sc is None:
            self.initial_bootloader_mode = True
            try:
                self.bootloader = ValveSoftwareWiredControllerBootloader();
                log.warn("Controller found in bootloader mode")
            except:
                log.warn("Could not open controller in bootloader mode")

        if self.sc is None and self.bootloader is None and ignoreMissingController == False:
            raise Exception("Could not find any controller")
            
    def Bootloader(self):
        """ Bootloader should always be available in theory .. """
        if self.bootloader is None:
            log.warn("Rebooting to bootloader mode")
            self.BootloaderMode()
        return self.bootloader

    def Ctrl(self):
        """ Ctrl is not always available, check for None before use """
        if self.sc is None and self.initial_bootloader_mode == False:
            log.warn("Rebooting to normal firmware mode")
            self.FirmwareMode()
        return self.sc

    def FlashLPCFirmware(self, filename):
        b = self.Bootloader()
        b.EraseFirmware()
        b.FlashFirmware(filename)
        checksum = self.ChecksumFirmwareFile(filename, 0x2030)
        b.VerifyFirmware(checksum)
        self.FirmwareMode()

    def FlashRadioFirmware(self, soft_device, application, application_address = 0):
        c = self.Ctrl()
        c.SWDStart()
        c.SWDErase()
        c.SWDFlash(soft_device,0)
        c.SWDFlash(application,application_address)
        c.SWDSave()
        c.ResetSOC() 

    def FirmwareMode(self):
        self.initial_bootloader_mode = False # If we call this directly, then we assume we have returned to normal
        self.bootloader.RebootToFirmware()
        del self.bootloader
        self.bootloader = None
        time.sleep(2)
        self.sc = ValveSoftwareWiredController();

    def BootloaderMode(self):
        self.sc.RebootToBootloader()
        del self.sc
        self.sc = None
        time.sleep(2)
        self.bootloader = ValveSoftwareWiredControllerBootloader();

    def ChecksumFirmwareFile(self, filename, seek):
        low32 = ( 1 << 32 ) - 1
        with open(filename, 'rb') as f:
            f.seek(seek)
            checksum = [0,0,0,0]
            chunks = iter(lambda: f.read(0x10), b'')
            for chunk in chunks:
                cur_word = struct.unpack("<IIII", chunk)
                save = checksum[1] << 0x1f;
                checksum[1] = (checksum[2] << 0x1f ^ checksum[1] >> 1 ^ cur_word[1]) & low32
                checksum[2] = (cur_word[2] ^ (checksum[2] >> 1 | checksum[3] << 0x1f)) & low32
                checksum[3] = ((((checksum[0] << 0x19 ^ checksum[0]) * 4 ^ checksum[0]) * 4 ^ cur_word[3]) & 0x80000000 ^ checksum[0] << 0x1f | cur_word[3] & 0x7fffffff ^ checksum[3] >> 1) & low32
                checksum[0] = ((checksum[0] >> 1 | save) ^ cur_word[0]) & low32
            checksum_bytes = struct.pack("<IIII", checksum[0], checksum[1], checksum[2], checksum[3])
            log.debug("Checksum: %s", checksum_bytes.hex())
            return struct.unpack("<BBBBBBBBBBBBBBBB", checksum_bytes)
