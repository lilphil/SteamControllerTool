import struct
import time
import binascii
from datetime import datetime

from constants import SCProtocolId
from USBHidDevice import USBHidDevice

vendor_id  = 0x28de
product_id = 0x1102

import logging
log = logging.getLogger(__name__)

class ValveSoftwareWiredController(USBHidDevice):
    """Steam Controller HID protocol"""

    firmwareRev = 0
    bootloaderRev = 0
    radioRev = 0
    personaliseState = 0

    def __init__(self):
        self.interface = None
        super().__init__(vendor_id, product_id, 2)
        self.open()

    def __del__(self):
        self.close()

    def Info(self):
        hid_info = self.hid_info()
        log.info("Manufacturer: %s" % hid_info.manufacturer)
        log.info("Product: %s" % hid_info.product)

        self.send([SCProtocolId.ControllerInfoRequest])
        response = self.get([0x83,0x23,00,00,00,00,00,0x01,0x02,0x11,00,00,0x02,0x03,00,00,00,0x0a,0x6d,0x92,0xd2,0x55,0x04,0x10,0x5c,0xbf,0x57,0x05,00,00,00,00,0x09,0x09])

        self.expect(response, [0x83])
        #unk1: 0x28 or 0x23
        protoId, unk1, unk2, unk3, usb_pid, unk4, unk5, self.bootloaderRev, unk7, self.firmwareRev, sep5, self.radioRev = struct.unpack("<BBIHHIIIBIBI", response[:32])

        log.info('USB Pid: 0x%04X' % usb_pid)
        log.info('Bootloader Revision: 0x%08X %s' % (self.bootloaderRev, datetime.fromtimestamp(self.bootloaderRev)))
        log.info('Firmware Revision: 0x%08X %s' % (self.firmwareRev, datetime.fromtimestamp(self.firmwareRev)))
        log.info('Radio Revision: 0x%08X %s' % (self.radioRev, datetime.fromtimestamp(self.radioRev)))
    def Pulse(self, side, high, low, repeat):
        """
        Triggers a Haptic vibration.
        Offset | Type | Name
        -------|------|-------
        0      | u8   | Must be 0x07 ??
        1      | u8   | Haptic side (0 = right, 1 = left)
        2      | u16  | Pulse high duration
        4      | u16  | Pulse low duration
        6      | u16  | Pulse repeat count
        8      | u8   | Optional - defaults to zero if not present.
        """
        if side > 0x01:
            side = 0x01
        highbytes = high.to_bytes(2, 'little')
        lowbytes = low.to_bytes(2, 'little')
        repeatbytes = repeat.to_bytes(2, 'little')
        self.send([SCProtocolId.TriggerHapticPulse, 0x07, side, highbytes[0], highbytes[1], lowbytes[0], lowbytes[1], repeatbytes[0], repeatbytes[1]])

    def Jingle(self, index = None):
        """
		index -- Index of song to play:
			 0 = Warm and Happy
			 1 = Invader
			 2 = Controller Confirmed
			 3 = Victory!
			 4 = Rise and Shine:
			 5 = Shorty
			 6 = Warm Boot
			 7 = Next Level
			 8 = Shake It Off
			 9 = Access Denied
			10 = Deactivate
			11 = Discovery
			12 = Triumph
			13 = The Mann
		"""

        payload = [SCProtocolId.PlayAudio]
        if index is not None:
            if self.personaliseState != True:
                raise Exception("Cannot play jingle at index before entering personalise mode") 
            payload.extend([0x04, index])
        self.send(payload)

    def Brightness(self, brightness):
        if brightness > 0x64:
            brightness = 0x64
        payload = [SCProtocolId.SetSettings, 0x03, 0x2d, brightness]
        self.send(payload)

    def PersonaliseMode(self):
        self.send([SCProtocolId.SetPersonalise, 0x10, 0x00, 0x01, 0x02, 0x03, 0x04, 0x05, 0x06, 0x07, 0x08, 0x09, 0x0a, 0x0b, 0x0c, 0x0d, 0x0e, 0x0f])
        self.personaliseState = 1

    def RebootToBootloader(self):
        self.ResetSOC([0x04, 0xc0, 0xba, 0xaa, 0xec])

    def ResetSettings(self):
        self.send([SCProtocolId.ResetControllerMappings])
        self.send([SCProtocolId.SetSettingsDefaultValues])
        self.send([SCProtocolId.SetSettings, 0x03, 0x18, 0x01])

    # def ValveMode(self):
    #     self.send([SCProtocolId.ValveMode, 0x87, 0x03, 0x08, 0x07, 0x00])

    # These methods only work on BLE host firmware

    def SWDStart(self):
        self.send([SCProtocolId.SendIRCode,0x04, 0x17, 0xed, 0xfe, 0xd0])
        while (self.expect(self.get([0x94, 0x06, 0x00, 0x00, 0xfc, 0x03]), [0x94, 0x06, 0x00, 0x00, 0xfc, 0x03], [0x94, 0x06, 0x00, 0x00, 0x00, 0x00, 0x02])):
            time.sleep(0.1)

    def SWDErase(self):
        self.send([SCProtocolId.SWDErase])
        while (self.expect(self.get([0x94, 0x06, 0x00, 0x00, 0x01, 0x00]), [0x94, 0x06, 0x00, 0x00, 0x01, 0x00], [0x94, 0x06, 0x00, 0x00, 0x00, 0x00, 0x02])):
            time.sleep(0.1)

    def SWDSave(self):
        self.send([SCProtocolId.SWDSave])

    def SWDFlash(self,filename,start_address):
        with open(filename, 'rb') as f:
            f.seek(0)
            chunk_size = 0x38
            chunks = iter(lambda: f.read(chunk_size), b'')
            for idx, chunk in enumerate(chunks):
                log.debug("File: %s | Chunk: %x", filename,idx)
                if not log.isEnabledFor(logging.DEBUG):
                    print(".", end="",flush=True)
                length = len(chunk)
                # TODO find out what the random number is. A checksum?
                random_number = 0
                if length < chunk_size:
                    log.debug("Last chunk")
                    if filename.endswith("d0g_bootloader.bin"):
                        random_number = 0x360
                    elif filename.endswith("d0g_module.bin"):
                        random_number = 0xce4
                    elif filename.endswith("s110_nrf51_8.0.0_softdevice.bin"):
                        random_number = 0x67f0
                    elif filename.endswith("vcf_wired_controller_d0g_5a0e3f348_radio.bin"):
                        random_number = 0x6a44
                address = struct.unpack("BBBB",((idx * length)+start_address+random_number).to_bytes(4, 'little'))
                # 4 bytes of address location 38*n
                payload = [SCProtocolId.FlashSWD, length+4]
                payload.extend(address)
                payload.extend(chunk)
                self.send(payload)
                # Wait for "ready": 0x60,0x09, while "not ready":0x00, 0x02
                while(self.expect(self.get(), [0x94, 0x06, 0x00, 0x00, 0x60, 0x09], [0x94, 0x06, 0x00, 0x00, 0x00, 0x00, 0x02])):
                    time.sleep(0.01)
            print("")
