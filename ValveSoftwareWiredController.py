import struct
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
    personaliseState = 0

    def __init__(self):
        self.interface = None
        super().__init__(vendor_id, product_id, 2)
        self.open()

    def __del__(self):
        self.close()

    def Info(self):
        log.info("Manufacturer: %s" % self.interface.manufacturer)
        log.info("Product: %s" % self.interface.product)
        self.send([SCProtocolId.ControllerInfoRequest])
        response = self.get()
        protoId, unk1, unk2, unk3, usb_pid, unk4, unk5, self.bootloaderRev, unk7, self.firmwareRev = struct.unpack("<BBIHHIIIBI", response[:27])
        #unk1: 0x28 or 0x23
        self.expect(response, [0x83])
        log.info('USB Pid: 0x%04X' % usb_pid)
        log.info('Bootloader Revision: 0x%08X %s' % (self.bootloaderRev, datetime.fromtimestamp(self.bootloaderRev)))
        log.info('Firmware Revision: 0x%08X %s' % (self.firmwareRev, datetime.fromtimestamp(self.firmwareRev)))

    # This doesnt work
    # def Pulse(self, side):
    #     """
    #     Triggers a Haptic vibration.

    #     Offset | Type | Name
    #     -------|------|-------
    #     0      | u8   | Haptic side (0 = right, 1 = left)
    #     1      | u16  | ??
    #     3      | u16  | ??
    #     5      | u16  | ??
    #     7      | u8   | Optional - defaults to zero if not present.
    #     """
    #     if side > 0x01:
    #         side = 0x01
    #     self.send([SCProtocolId.TriggerHapticPulse, side])

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

    def EraseRadio(self):
        self.send([SCProtocolId.SendIRCode,0x04, 0x17, 0xed, 0xfe, 0xd0])