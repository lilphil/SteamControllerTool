#!/usr/bin/env python3
import os, sys
import logging
import time
from argparse import ArgumentParser

from SteamController import SteamController

cli = ArgumentParser()
cli.add_argument("-d","--debug", default=False, action="store_true", help = "Enable debug logging")
subparsers = cli.add_subparsers(dest="subcommand")

def argument(*name_or_flags, **kwargs):
    return (list(name_or_flags), kwargs)

def subcommand(args=[], parent=subparsers):
    def decorator(func):
        parser = parent.add_parser(func.__name__, description=func.__doc__)
        for arg in args:
            parser.add_argument(*arg[0], **arg[1])
        parser.set_defaults(func=func)
    return decorator

@subcommand()
def info(args,sc):
    ctrl = sc.Ctrl()
    if ctrl is None:
        sys.exit()
    ctrl.Info()

@subcommand([argument("filename", help="Path to LPC firmware bin")])
def flash(args,sc):
    sc.FlashLPCFirmware(args.filename)

@subcommand([argument("-o", "--offset", type=int, default=0, help="application address offset"),argument("softdevice", help="SoftDevice filename"),argument("application", help="application filename")])
def swdflash(args,sc):
    sc.FlashRadioFirmware(args.softdevice, args.application, args.offset)

@subcommand([argument("-b","--ble", default=False, action="store_true", help = "Quick flash to ble firmware"),argument("-p","--prod", default=False, action="store_true", help = "Quick flash to production firmware")])
def qf(args,sc):
    if args.prod:
        sc.FlashRadioFirmware("./fw_images/production/d0g_bootloader.bin","./fw_images/production/d0g_module.bin",1024)
        time.sleep(4)
        sc.FlashLPCFirmware("./fw_images/production/vcf_wired_controller_d0g.bin")

    elif args.ble:
        sc.FlashLPCFirmware("./fw_images/ble/vcf_wired_controller_d0g_5b0f21bd.bin")
        time.sleep(4)
        sc.FlashRadioFirmware("./fw_images/ble/s110_nrf51_8.0.0_softdevice.bin", "./fw_images/ble/vcf_wired_controller_d0g_5a0e3f348_radio.bin", 0)
    else:
        cli.print_usage()
    
if __name__ == '__main__':
    args = cli.parse_args()
    if args.debug:
        logging.basicConfig(level="DEBUG")
    else:
        logging.basicConfig(level="INFO")

    if args.subcommand is None:
        cli.print_usage()
        sys.exit()
    sc = SteamController(True)
    args.func(args,sc)