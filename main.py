#!/usr/bin/env python3
import os
import logging
from SteamController import SteamController
import time
from constants import SCProtocolId

logging.basicConfig(level=os.environ.get("LOGLEVEL", "INFO"))

if __name__ == '__main__':
    sc = SteamController(True)
    ctrl = sc.Ctrl()
    if ctrl is not None:
        ctrl.Info()

    #sc.FlashLPCFirmware("./fw_images/production/vcf_wired_controller_d0g.bin")
    #sc.FlashLPCFirmware("./fw_images/ble/vcf_wired_controller_d0g_5b0f21bd.bin")
   #sc.Ctrl().FlashRadioFirmware("./fw_images/ble/s110_nrf51_8.0.0_softdevice.bin")
