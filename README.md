# Steam Controller Tool

## Setup

Needs the system HIDAPI library (`libhidapi-hidraw0` on Debian/Ubuntu/Pop) and the Python `hid` package (ctypes bindings — not `hidapi` / cython-hidapi).

```bash
sudo apt install libhidapi-hidraw0
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/python ./main.py info
```

You need to get the steam firmware files, eg:

```fw_images/
├── ble
│   ├── s110_nrf51_8.0.0_softdevice.bin
│   ├── vcf_wired_controller_d0g_5a0e3f348_radio.bin
│   └── vcf_wired_controller_d0g_5b0f21bd.bin
└── production
    ├── d0g_bootloader.bin
    ├── d0g_module.bin
    └── vcf_wired_controller_d0g.bin
```

## COMMANDS

### info

Show Steam Controller hid and firmware information, use this first to check connectivity to a working remote

### flash

Flash LPC11U37F firmware

### swdflash

Flash nRF51822 firmware

### qf

"Quick flash" will use the hardcoded filenames from firmware as per the setup step if you have them.  
Usage, `qf -b` or `qf -p` for ble or production

## Steam Controller

You can recover from most issues by entering bootloader mode on the controller, hold Right Trigger and press steam button to switch on. Copy firmware to the drive that appears, but don't use standard tools, you have to copy with dd:

```sudo dd conv=nocreat,notrunc oflag=direct bs=512 if=fw_images/production/vcf_wired_controller_d0g.bin of=/media/user/CRP\ DISABLD/firmware.bin```

## BLE Firmware

Y + Steam = Bluetooth LE Pairing Mode  
B + Steam = Switch to Bluetooth LE Mode  
X + Steam = Receiver Pairing Mode  
A + Staem = Switch to dongle Mode  

https://help.steampowered.com/en/faqs/view/1796-5FC3-88B3-C85F

## Troubleshooting

 * If you keep getting errors trying to open steam controller, make sure the hid library is > 1.0 (ubuntu 24.04 python3-hid is too old at v0.9).
 * Check lsusb to make sure the controller is showing up, if it isnt check cables.
 * Make sure you have udev permissions.

---

Thanks to greggersaurus from https://github.com/greggersaurus/OpenSteamController and roblabla for their awesome reverse engineering efforts

