#!/usr/bin/env python3
"""
Tool for working with Spotify Car Thing, aka superbird
"""
# pylint: disable=line-too-long,broad-except

import sys
import time
import argparse
import os
import shutil
import platform

from superbird_device import SuperbirdDevice
from superbird_device import find_device, check_device_mode

VERSION = '0.0.1'

if __name__ == "__main__":
    print(f'Spotify Car Thing (superbird) toolkit, v{VERSION}, by bishopdynamics')
    print('     https://github.com/bishopdynamics/superbird-tool')
    print('')
    argument_parser = argparse.ArgumentParser(
        description='Options cannot be combined; do one thing at a time :)'
    )
    argument_parser.add_argument('--find_device', action='store_true', help='find superbird device and show its current boot mode')
    argument_parser.add_argument('--burn_mode', action='store_true', help='enter USB Burn Mode (if currently in USB Mode)')
    argument_parser.add_argument('--continue_boot', action='store_true', help='continue booting normally (if currently in USB Burn Mode)')
    argument_parser.add_argument('--bulkcmd', action='store', type=str, nargs=1, metavar=('COMMAND'), help='run a uboot command on the device')
    argument_parser.add_argument('--boot_adb_kernel', action='store_true', help='boot a kernel with adb enabled (not persistent)')
    argument_parser.add_argument('--enable_uart_shell', action='store_true', help='enable UART shell')
    argument_parser.add_argument('--disable_avb2', action='store_true', help='disable A/B booting, lock to A')
    argument_parser.add_argument('--enable_burn_mode', action='store_true', help='enable USB Burn Mode at every boot (when connected to USB host)')
    argument_parser.add_argument('--disable_burn_mode', action='store_true', help='Disable USB Burn Mode at every boot (when connected to USB host)')
    argument_parser.add_argument('--disable_charger_check', action='store_true', help='disable check for valid charger at boot')
    argument_parser.add_argument('--enable_charger_check', action='store_true', help='enable check for valid charger at boot')
    argument_parser.add_argument('--dump_device', action='store', type=str, nargs=1, metavar=('OUTPUT_FOLDER'), help='Dump all partitions to a folder')
    argument_parser.add_argument('--dump_partition', action='store', type=str, nargs=2, metavar=('PARTITION_NAME', 'OUTPUT_FILE'), help='Dump a partition to a file')



    args = argument_parser.parse_args()

    if len(sys.argv) <= 1:
        argument_parser.print_help()
        sys.exit()

    if platform.system() == 'Linux':
        if os.geteuid() != 0:
            print('Need to run as root!')
            sys.exit(1)

    if args.find_device:
        find_device()
        sys.exit()

    dev = SuperbirdDevice()

    if args.bulkcmd:
        if check_device_mode('usb-burn'):
            BULKCMD_STRING = args.bulkcmd[0]
            dev.bulkcmd(BULKCMD_STRING)
    elif args.boot_adb_kernel:
        if check_device_mode('usb-burn'):
            FILE_ENV = 'images/env.txt'
            FILE_KERNEL = 'images/superbird.kernel.img'
            FILE_INITRD = 'images/superbird.initrd.img'
            dev.boot(FILE_ENV, FILE_KERNEL, FILE_INITRD)
    elif args.enable_uart_shell:
        if check_device_mode('usb-burn'):
            print('Enabling UART shell')
            dev.bulkcmd('amlmmc env')
            dev.bulkcmd('setenv initargs init=/sbin/pre-init')
            dev.bulkcmd(r'setenv initargs ${initargs} ramoops.pstore_en=1')
            dev.bulkcmd(r'setenv initargs ${initargs} ramoops.record_size=0x8000')
            dev.bulkcmd(r'setenv initargs ${initargs} ramoops.console_size=0x4000')
            dev.bulkcmd(r'setenv initargs ${initargs} rootfstype=ext4')
            dev.bulkcmd(r'setenv initargs ${initargs} console=ttyS0,115200n8')
            dev.bulkcmd(r'setenv initargs ${initargs} no_console_suspend')
            dev.bulkcmd(r'setenv initargs ${initargs} earlycon=aml-uart,0xff803000')
            dev.bulkcmd('env save')
    elif args.disable_avb2:
        if check_device_mode('usb-burn'):
            print('Disabling A/B booting, forever A')
            dev.bulkcmd('amlmmc env')
            dev.bulkcmd(r'setenv storeargs ${storeargs} setenv avb2 0\;')
            dev.bulkcmd('setenv initargs init=/sbin/pre-init')
            dev.bulkcmd(r'setenv initargs ${initargs} ramoops.pstore_en=1')
            dev.bulkcmd(r'setenv initargs ${initargs} ramoops.record_size=0x8000')
            dev.bulkcmd(r'setenv initargs ${initargs} ramoops.console_size=0x4000')
            dev.bulkcmd(r'setenv initargs ${initargs} rootfstype=ext4')
            dev.bulkcmd(r'setenv initargs ${initargs} console=ttyS0,115200n8')
            dev.bulkcmd(r'setenv initargs ${initargs} no_console_suspend')
            dev.bulkcmd(r'setenv initargs ${initargs} earlycon=aml-uart,0xff803000')
            dev.bulkcmd(r'setenv initargs ${initargs} ro root=/dev/mmcblk0p14')
            dev.bulkcmd('setenv active_slot _a')
            dev.bulkcmd('setenv boot_part boot_a')
            dev.bulkcmd('env save')
    elif args.enable_burn_mode:
        if check_device_mode('usb-burn'):
            print('Enabling USB Burn Mode at every boot (if USB host connected)')
            dev.bulkcmd('amlmmc env')
            dev.bulkcmd(r'setenv storeargs ${storeargs} run update\;')
            dev.bulkcmd('env save')
            print('Every time the device boots, if usb is connected it will boot into USB Burn Mode')
    elif args.disable_burn_mode:
        if check_device_mode('usb-burn'):
            print('Disabling USB Burn Mode at every boot (if USB host connected)')
            dev.bulkcmd('amlmmc env')
            dev.bulkcmd(r'setenv storeargs "setenv bootargs \${initargs} \${fs_type}"')
            dev.bulkcmd(r'setenv storeargs "${storeargs} reboot_mode_android=\${reboot_mode_android}"')
            dev.bulkcmd(r'setenv storeargs "${storeargs} logo=\${display_layer},loaded,\${fb_addr}"')
            dev.bulkcmd(r'setenv storeargs "${storeargs} fb_width=\${fb_width} fb_height=\${fb_height}"')
            dev.bulkcmd(r'setenv storeargs "${storeargs} vout=\${outputmode},enable"')
            dev.bulkcmd(r'setenv storeargs "${storeargs} panel_type=\${panel_type}"')
            dev.bulkcmd(r'setenv storeargs "${storeargs} frac_rate_policy=\${frac_rate_policy}"')
            dev.bulkcmd(r'setenv storeargs "${storeargs} osd_reverse=\${osd_reverse}"')
            dev.bulkcmd(r'setenv storeargs "${storeargs} video_reverse=\${video_reverse}"')
            dev.bulkcmd(r'setenv storeargs "${storeargs} irq_check_en=\${Irq_check_en}"')
            dev.bulkcmd(r'setenv storeargs "${storeargs} androidboot.selinux=\${EnableSelinux}"')
            dev.bulkcmd(r'setenv storeargs "${storeargs} androidboot.firstboot=\${firstboot}"')
            dev.bulkcmd(r'setenv storeargs "${storeargs} jtag=\${jtag} uboot_version=\${gitver}\;"')
            dev.bulkcmd(r'setenv storeargs "${storeargs} setenv bootargs \${bootargs} androidboot.hardware=amlogic\;"')
            dev.bulkcmd(r'setenv storeargs "${storeargs} setenv avb2 0\;"')
            dev.bulkcmd('env save')
            print('The device will now boot normally, and will NOT boot into USB Burn Mode')
    elif args.dump_partition:
        if check_device_mode('usb-burn'):
            PARTITION_NAME = args.dump_partition[0]
            OUTFILE = args.dump_partition[1]
            dev.dump_partition(PARTITION_NAME, OUTFILE)
            print(f'dumped partition to {OUTFILE}')
    elif args.dump_device:
        if check_device_mode('usb-burn'):
            FOLDER_NAME = args.dump_device[0]
            print(f'dumping entire device to {FOLDER_NAME}')
            shutil.rmtree(FOLDER_NAME, ignore_errors=True)
            os.mkdir(FOLDER_NAME)
            dev.dump_partition("bootloader", f"{FOLDER_NAME}/bootloader.dump")
            dev.dump_partition("env", f"{FOLDER_NAME}/env.dump")
            dev.dump_partition("fip_a", f"{FOLDER_NAME}/fip_a.dump")
            dev.dump_partition("fip_b", f"{FOLDER_NAME}/fip_b.dump")
            dev.dump_partition("logo", f"{FOLDER_NAME}/logo.dump")
            dev.dump_partition("dtbo_a", f"{FOLDER_NAME}/dtbo_a.dump")
            dev.dump_partition("dtbo_b", f"{FOLDER_NAME}/dtbo_b.dump")
            dev.dump_partition("vbmeta_a", f"{FOLDER_NAME}/vbmeta_a.dump")
            dev.dump_partition("vbmeta_b", f"{FOLDER_NAME}/vbmeta_b.dump")
            dev.dump_partition("boot_a", f"{FOLDER_NAME}/boot_a.dump")
            dev.dump_partition("boot_b", f"{FOLDER_NAME}/boot_b.dump")
            dev.dump_partition("misc", f"{FOLDER_NAME}/misc.dump")
            dev.dump_partition("settings", f"{FOLDER_NAME}/settings.ext4")
            dev.dump_partition("system_a", f"{FOLDER_NAME}/system_a.ext2")
            dev.dump_partition("system_b", f"{FOLDER_NAME}/system_b.ext2")
            dev.dump_partition("data", f"{FOLDER_NAME}/data.ext4")
            print('dump complete')
    elif args.disable_charger_check:
        if check_device_mode('usb-burn'):
            print('Disabling check for valid charger')
            # normally, bootcmd=run check_charger
            #   if it detects OK charger, it then calls: run storeboot
            #   so we can skip the check by changing bootcmd to just call: run storeboot
            dev.bulkcmd('amlmmc env')
            dev.bulkcmd('setenv bootcmd run storeboot')
            dev.bulkcmd('env save')
            print('The device will not check for valid charger')
    elif args.enable_charger_check:
        if check_device_mode('usb-burn'):
            dev.bulkcmd('amlmmc env')
            dev.bulkcmd('setenv bootcmd run check_charger')
            dev.bulkcmd('env save')
            print('The device will now check for valid charger, requiring you to press menu button to bypass')
    elif args.burn_mode:
        if check_device_mode('usb'):
            print('Entering USB Burn Mode')
            dev.bl2_boot('images/superbird.bl2.encrypted.bin', 'images/superbird.bootloader.img')
            print('Waiting for device...')
            time.sleep(5)  # wait for it to boot up in USB Burn Mode
            if check_device_mode('usb-burn'):
                print('Device is now in USB Burn Mode')
            else:
                print('Failed to enter USB Burn Mode!')
    elif args.continue_boot:
        if check_device_mode('usb-burn'):
            print('Continuing boot...')
            dev.bulkcmd('mw.b 0x17f89754 1')
    sys.exit()
