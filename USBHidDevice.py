import hid
import logging

from constants import SCProtocolId

log = logging.getLogger(__name__)

class USBHidDevice:
    def __init__(self, vendor_id, product_id, interface_number):
        self.interface = None
        self.vid = vendor_id
        self.pid = product_id
        self.interface_number = interface_number

    def open(self):
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

    def send(self, data):
        request_data = [0x00] * 65 # First byte is Report ID
        request_data[1:len(data) + 1] = data
        request_packet = bytes(request_data)
        log.debug("Request:  %s" % request_packet[1:].hex())
        self.interface.send_feature_report(request_packet)

    def get(self):
        response_packet = self.interface.get_feature_report(0x00, 65)
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
                if bytes[index] != item:
                    match = False
            if match:
                return argindex
        raise Exception("Unexpected response")

    def ResetSOC(self, data = None):
        payload = [SCProtocolId.ResetSOC]
        if data is not None:
            payload.extend(data)
        self.send(payload)
