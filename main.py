#!/usr/bin/env python3
import os
import logging
from SteamController import SteamController

logging.basicConfig(level=os.environ.get("LOGLEVEL", "INFO"))

if __name__ == '__main__':
    sc = SteamController(True)
    ctrl = sc.Ctrl()
    if ctrl is not None:
        ctrl.Info()
    sc.Ctrl().EraseRadio()

#    sc.FlashLPCFirmware("./fw_images/production/vcf_wired_controller_d0g.bin")
