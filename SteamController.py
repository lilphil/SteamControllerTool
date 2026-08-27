import time
import struct
import logging

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
        log.info("Reboot to bootloader")
        b = self.Bootloader()
        log.info("Erase LPC firmware")
        b.EraseFirmware()
        log.info("Flashing %s", filename)
        b.FlashFirmware(filename)
        checksum = self.ChecksumFirmwareFile(filename, 0x2030)
        b.VerifyFirmware(checksum)
        log.info("Resetting")
        self.FirmwareMode()

    def FlashRadioFirmware(self, soft_device, application, application_address = 0):
        c = self.Ctrl()
        log.info("Starting SWD")
        c.SWDStart()
        log.info("Erase SWD")
        c.SWDErase()
        log.info("Flashing %s", soft_device)
        c.SWDFlash(soft_device,0)
        log.info("Flashing %s at offset %d", application, application_address)
        c.SWDFlash(application,application_address)
        c.SWDSave()
        log.info("Resetting")
        c.ResetSOC()
        # ResetSOC drops USB; reopen app HID so a following LPC flash can
        # RebootToBootloader on a live handle (qf -p radio-then-LPC).
        self._reopen_app(settle=4)

    def FirmwareMode(self):
        self.initial_bootloader_mode = False # If we call this directly, then we assume we have returned to normal
        self.bootloader.RebootToFirmware()
        del self.bootloader
        self.bootloader = None
        # App needs time after reset before HID is ready. Do not fail the whole
        # flash if reopen times out — verify already succeeded.
        try:
            self._reopen_app(settle=4)
        except Exception as e:
            log.warn("Could not reopen app HID after reset (flash may still be OK): %s", e)

    def BootloaderMode(self):
        if self.sc is None:
            self._reopen_app(settle=2)
        self.sc.RebootToBootloader()
        try:
            self.sc.close()
        except Exception:
            pass
        del self.sc
        self.sc = None
        time.sleep(2)
        deadline = time.time() + 15
        last_err = None
        while time.time() < deadline:
            try:
                self.bootloader = ValveSoftwareWiredControllerBootloader()
                return
            except Exception as e:
                last_err = e
                time.sleep(0.5)
        raise Exception("Could not open bootloader after reboot: %s" % last_err)
    def _reopen_app(self, settle=4):
        if self.sc is not None:
            try:
                self.sc.close()
            except Exception:
                pass
            del self.sc
            self.sc = None
        time.sleep(settle)
        deadline = time.time() + 15
        last_err = None
        while time.time() < deadline:
            try:
                self.sc = ValveSoftwareWiredController()
                return
            except Exception as e:
                last_err = e
                time.sleep(0.5)
        raise Exception("Could not reopen controller after reset: %s" % last_err)

    def ChecksumFirmwareFile(self, filename, seek):
        # crc128
        low32 = ( 1 << 32 ) - 1
        with open(filename, 'rb') as f:
            f.seek(seek)
            checksum = [0,0,0,0]
            chunks = iter(lambda: f.read(0x10), b'')
            for chunk in chunks:
                if len(chunk) < 0x10:
                    chunk = chunk + b'\x00' * (0x10 - len(chunk))
                cur_word = struct.unpack("<IIII", chunk)
                save = checksum[1] << 0x1f;
                checksum[1] = (checksum[2] << 0x1f ^ checksum[1] >> 1 ^ cur_word[1]) & low32
                checksum[2] = (cur_word[2] ^ (checksum[2] >> 1 | checksum[3] << 0x1f)) & low32
                checksum[3] = ((((checksum[0] << 0x19 ^ checksum[0]) * 4 ^ checksum[0]) * 4 ^ cur_word[3]) & 0x80000000 ^ checksum[0] << 0x1f | cur_word[3] & 0x7fffffff ^ checksum[3] >> 1) & low32
                checksum[0] = ((checksum[0] >> 1 | save) ^ cur_word[0]) & low32
            checksum_bytes = struct.pack("<IIII", checksum[0], checksum[1], checksum[2], checksum[3])
            log.debug("Checksum: %s", checksum_bytes.hex())
            return struct.unpack("<BBBBBBBBBBBBBBBB", checksum_bytes)

