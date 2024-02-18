import hid
import logging
import time

from constants import SCProtocolId

log = logging.getLogger(__name__)

class USBHidDevice:
    def __init__(self, vendor_id, product_id, interface_number):
        self.interface = None
        self.vid = vendor_id
        self.pid = product_id
        self.interface_number = interface_number
        self.simulate = False

    def open(self):
        if self.simulate:
            log.debug("Open would have tried to open %x %x", self.vid, self.pid)
            return
        interfaces = [i for i in hid.enumerate(self.vid, self.pid) if i['interface_number'] == self.interface_number]
        if len(interfaces) == 0:
            raise Exception("No device found")

        self.interface = hid.Device(path=interfaces[0]['path'])

    def close(self):
        if self.interface is not None:
            try:
                self.interface.close()
            except:
                log.warn("Failed to close interface")

    def hid_info(self):
        info = type('HidInfo', (object,), {})
        if self.simulate:
            info.manufacturer = "Simulated HID manufacturer"
            info.product = "Simulated HID product"
        else:
            info.manufacturer = self.interface.manufacturer
            info.product =  self.interface.product
        return info
        
    def send(self, data):
        request_data = [0x00] * 65 # First byte is Report ID
        request_data[1:len(data) + 1] = data
        request_packet = bytes(request_data)
        log.debug("Request:  %s" % request_packet[1:].hex())
        if self.simulate:
            return
        self.interface.send_feature_report(request_packet)

    def get(self, simulated = 0x00):
        if self.simulate:
            response = bytes(simulated)
        else:
            # If we get a blank response, try a few more times
            for _ in range(15):
                response_packet = self.interface.get_feature_report(0x00, 65)
                if len(response_packet) > 0:
                    break
                time.sleep(0.1)
            
            response = response_packet[1:]
        log.debug("Response: %s" % response.hex())
        return response

    def expect(self, bytes, *args):
        """
        Takes a variable argument list of arrays of bytes
        """
        for argindex, expected in enumerate(args):
            match = True
            for index, item in enumerate(expected):
                if len(bytes) == 0 or len(bytes) < index:
                    match = False
                    break
                if bytes[index] != item:
                    match = False
            if match:
                return argindex
        if self.simulate:
            log.info("Unexpected response ignored in simulation mode")
            return -1
        else:
            raise Exception("Unexpected response")

    def ResetSOC(self, data = None):
        payload = [SCProtocolId.ResetSOC]
        if data is not None:
            payload.extend(data)
        self.send(payload)
