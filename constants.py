from enum import IntEnum

class SCProtocolId(IntEnum):
    # SetUnitSerial = 0xa9 0x11 - follow this with a reset soc
    SetControllerMappings = 0x80
    ClearControllerMappings = 0x81
    GetControllerMappings = 0x82
    ControllerInfoRequest = 0x83
    ResetControllerMappings = 0x85
    FactoryReset = 0x86
    SetSettings = 0x87
    SetSettingsDefaultValues = 0x8e
    TriggerHapticPulse = 0x8f
    RebootToISP = 0x90
    EraseLPCFirmware = 0x91
    FlashLPCFirmware = 0x92
    VerifyLPCFirmware = 0x93
    ResetSOC = 0x95
    EraseNRFFirmware = 0x97
    FlashNRFFirmware = 0x98
    VerifyNRFFirmware = 0x99
    TurnOffController = 0x9f
    SetHardwareVersion = 0xa0
    CalibrateTrackpads = 0xa7
    ControllerInfoRequest2 = 0xae
    CalibrateIMU = 0xb5
    PlayAudio = 0xb6
    StartFlashJingle = 0xb7
    FlashJingle = 0xb8
    EndFlashJingle = 0xb9
    GetChipID = 0xba
    ReadUID = 0xbb
    CalibrateJoystick = 0xbf
    SetPersonalise = 0xc1
    SendIRCode = 0xc6
    StopIR = 0xc7
