import time
import binascii
import struct

from constants import SCProtocolId
from USBHidDevice import USBHidDevice

vendor_id  = 0x28de
product_id = 0x1002

import logging
log = logging.getLogger(__name__)

class ValveSoftwareWiredControllerBootloader(USBHidDevice):
    """Steam Controller Bootloader HID protocol"""

    def __init__(self):
        self.interface = None
        super().__init__(vendor_id, product_id, 0)
        self.open()

    def __del__(self):
        self.close()

    def RebootToFirmware(self):
        self.ResetSOC()

    def VerifyFirmware(self, checksum):
        """
        Must call verify with the correct checksum after flashing, or the bootloader will not save it
        Its only possible to verify firmware directly after a flash, otherwise it will always return failure
        """
        payload = [SCProtocolId.VerifyLPCFirmware,0x10]
        payload.extend(checksum)
        self.send(payload)
        time.sleep(0.1)
        response = self.get()
        try:
            self.expect(response, [0x94, 0x02, 0x00]) # Possibly [0x94, 0x02, 0x01] is fail 
        except:
            raise Exception("Failed to verify firmware checksum")

    def EraseFirmware(self):
        self.send([SCProtocolId.EraseLPCFirmware], 0)
        time.sleep(0.1)
        response = self.get()
        protoId, protoResp = struct.unpack("<BB", response[:2])
        self.expect(response, [0x94, 0x02])

    def FlashFirmware(self, filename):
        # Should check for full buffer at end of read, if not fill remaining bytes with -1
        with open(filename, 'rb') as f:
            f.seek(0x2000)
            chunks = iter(lambda: f.read(0x32), b'')
            for chunk in chunks:
                print(".", end="",flush=True)
                length = len(chunk)
                log.debug(binascii.hexlify(chunk))
                payload = [SCProtocolId.FlashLPCFirmware, length]
                payload.extend(chunk)
                self.send(payload)
            print("")
        time.sleep(0.2)


        