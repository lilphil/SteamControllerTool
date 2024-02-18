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
    #ctrl.Pulse(0,65535,65535,2)
    #sc.FlashLPCFirmware("./fw_images/ble/vcf_wired_controller_d0g_5b0f21bd.bin")
    #time.sleep(4)

    # Prod
    #sc.FlashRadioFirmware("./fw_images/production/d0g_bootloader.bin","./fw_images/production/d0g_module.bin",1024)
    #time.sleep(4)
    #sc.FlashLPCFirmware("./fw_images/production/vcf_wired_controller_d0g.bin")

    # BLE
    sc.FlashLPCFirmware("./fw_images/ble/vcf_wired_controller_d0g_5b0f21bd.bin")
    time.sleep(4)
    sc.FlashRadioFirmware("./fw_images/ble/s110_nrf51_8.0.0_softdevice.bin", "./fw_images/ble/vcf_wired_controller_d0g_5a0e3f348_radio.bin", 0)

