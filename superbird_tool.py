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
import tempfile

from pathlib import Path

from uboot_env import read_environ

from superbird_device import SuperbirdDevice
from superbird_device import find_device, check_device_mode, enter_burn_mode

VERSION = '0.0.9'

# this method chosen specifically because it works correctly when bundled using nuitka --onefile
IMAGES_PATH = Path(os.path.dirname(__file__)).joinpath('images')


def convert_env_dump(env_dump:str, env_file:str):
    """ convert a dumped env partition image into a human-readable text file """
    print(f'Converting partition dump: {env_dump} to textfile: {env_file}')
    (environ, _length, _crc) = read_environ(env_dump)
    with open(env_file, 'w', encoding='utf-8') as oef:
        lines = []
        for key, value in environ.items():
            lines.append(f'{key}={value}\n')
        oef.writelines(lines)


if __name__ == '__main__':
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
    argument_parser.add_argument('--boot_adb_kernel', action='store', type=str, nargs=1, metavar=('BOOT_SLOT'), help='boot a kernel with adb enabled on chosen slot (A or B)(not persistent)')
    argument_parser.add_argument('--enable_uart_shell', action='store_true', help='enable UART shell')
    argument_parser.add_argument('--disable_avb2', action='store', type=str, nargs=1, metavar=('BOOT_SLOT'), help='disable A/B booting, lock to chosen slot(A or B)')
    argument_parser.add_argument('--enable_burn_mode', action='store_true', help='enable USB Burn Mode at every boot (when connected to USB host)')
    argument_parser.add_argument('--enable_burn_mode_button', action='store_true', help='enable USB Burn Mode if preset button 4 is held while booting (when connected to USB host)')
    argument_parser.add_argument('--disable_burn_mode', action='store_true', help='Disable USB Burn Mode at every boot (when connected to USB host)')
    argument_parser.add_argument('--disable_charger_check', action='store_true', help='disable check for valid charger at boot')
    argument_parser.add_argument('--enable_charger_check', action='store_true', help='enable check for valid charger at boot')
    argument_parser.add_argument('--dump_device', action='store', type=str, nargs=1, metavar=('OUTPUT_FOLDER'), help='Dump all partitions to a folder')
    argument_parser.add_argument('--restore_device', action='store', type=str, nargs=1, metavar=('INPUT_FOLDER'), help='Restore all partitions from a folder')
    argument_parser.add_argument('--dump_partition', action='store', type=str, nargs=2, metavar=('PARTITION_NAME', 'OUTPUT_FILE'), help='Dump a partition to a file')
    argument_parser.add_argument('--restore_partition', action='store', type=str, nargs=2, metavar=('PARTITION_NAME', 'INPUT_FILE'), help='Restore a partition from a dump file')
    argument_parser.add_argument('--restore_stock_env', action='store_true', help='wipe env, then restore default env values from stock_env.txt')
    argument_parser.add_argument('--send_env', action='store', type=str, nargs=1, metavar=('ENV_TXT'), help='import contents of given env.txt file (without wiping)')
    argument_parser.add_argument('--send_full_env', action='store', type=str, nargs=1, metavar=('ENV_TXT'), help='wipe env, then import contents of given env.txt file')
    argument_parser.add_argument('--convert_env_dump', action='store', type=str, nargs=2, metavar=('ENV_DUMP', 'OUTPUT_TXT'), help='convert a local dump of env partition into text format')
    argument_parser.add_argument('--get_env', action='store', type=str, nargs=1, metavar=('ENV_TXT'), help='dump device env partition, and convert it to env.txt format')

    args = argument_parser.parse_args()

    if len(sys.argv) <= 1:
        argument_parser.print_help()
        sys.exit()

    if platform.system() == 'Linux':
        if os.geteuid() != 0:
            print('Need to run as root!')
            sys.exit(1)

    # First check options that do not need the device

    if args.find_device:
        find_device()
        sys.exit()
    elif args.convert_env_dump:
        ENV_DUMP = args.convert_env_dump[0]
        ENV_FILE = args.convert_env_dump[1]
        convert_env_dump(ENV_DUMP, ENV_FILE)
        sys.exit()

    # Now get the device, and check options that need it
    START_TIME = time.time()
    dev = SuperbirdDevice()

    if args.bulkcmd:
        dev = enter_burn_mode(dev)
        if dev is not None:
            BULKCMD_STRING = args.bulkcmd[0]
            dev.bulkcmd(BULKCMD_STRING)
    elif args.boot_adb_kernel:
        dev = enter_burn_mode(dev)
        if dev is not None:
            SLOT = args.boot_adb_kernel[0]
            if SLOT.lower() not in ['a', 'b']:
                print('Invalid slot provided, using slot a')
                SLOT = 'a'
            print('Booting adb kernel on slot', SLOT)
            if SLOT.lower() == 'a':
                FILE_ENV = str(IMAGES_PATH.joinpath('env_a.txt'))
            elif SLOT.lower() == 'b':
                FILE_ENV = str(IMAGES_PATH.joinpath('env_b.txt'))
            FILE_KERNEL = str(IMAGES_PATH.joinpath('superbird.kernel.img'))
            FILE_INITRD = str(IMAGES_PATH.joinpath('superbird.initrd.img'))
            dev.boot(FILE_ENV, FILE_KERNEL, FILE_INITRD)
    elif args.enable_uart_shell:
        dev = enter_burn_mode(dev)
        if dev is not None:
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
        dev = enter_burn_mode(dev)
        if dev is not None:
            SLOT = args.disable_avb2[0]
            if SLOT.lower() not in ['a', 'b']:
                print('Invalid slot provided, using slot a')
                SLOT = 'a'
            print('Disabling A/B booting locking to slot:', SLOT)

            dev.bulkcmd('amlmmc env')
            dev.bulkcmd(r'setenv storeargs ${storeargs} setenv avb2 0\;')
            dev.bulkcmd('setenv initargs init=/sbin/pre-init')
            dev.bulkcmd(r'setenv initargs "${initargs} ramoops.pstore_en=1"')
            dev.bulkcmd(r'setenv initargs "${initargs} ramoops.record_size=0x8000"')
            dev.bulkcmd(r'setenv initargs "${initargs} ramoops.console_size=0x4000"')
            dev.bulkcmd(r'setenv initargs "${initargs} rootfstype=ext4"')
            dev.bulkcmd(r'setenv initargs "${initargs} console=ttyS0,115200n8"')
            dev.bulkcmd(r'setenv initargs "${initargs} no_console_suspend"')
            dev.bulkcmd(r'setenv initargs "${initargs} earlycon=aml-uart,0xff803000"')
            if SLOT.lower() == 'a':
                dev.bulkcmd(r'setenv initargs "${initargs} ro root=/dev/mmcblk0p14"')
                dev.bulkcmd('setenv active_slot _a')
                dev.bulkcmd('setenv boot_part boot_a')
            elif SLOT.lower() == 'b':
                dev.bulkcmd(r'setenv initargs "${initargs} ro root=/dev/mmcblk0p15"')
                dev.bulkcmd('setenv active_slot _b')
                dev.bulkcmd('setenv boot_part boot_b')
            dev.bulkcmd('env save')
    elif args.enable_burn_mode:
        dev = enter_burn_mode(dev)
        if dev is not None:
            print('Enabling USB Burn Mode at every boot (if USB host connected)')
            dev.bulkcmd('amlmmc env')
            dev.bulkcmd(r'setenv storeargs "${storeargs} run update\;"')
            dev.bulkcmd('env save')
            print('Every time the device boots, if usb is connected it will boot into USB Burn Mode')
    elif args.enable_burn_mode_button:
        dev = enter_burn_mode(dev)
        if dev is not None:
            print('Enabling USB Burn Mode at boot if preset button 4 is held')
            dev.bulkcmd('amlmmc env')
            dev.bulkcmd(r'setenv storeargs "${storeargs} if gpio input GPIOA_3; then run update; fi;"')
            dev.bulkcmd('env save')
            print('Every time the device boots, if usb is connected AND preset button 4 is held, it will boot into USB Burn Mode')
    elif args.disable_burn_mode:
        dev = enter_burn_mode(dev)
        if dev is not None:
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
        dev = enter_burn_mode(dev)
        if dev is not None:
            PARTITION_NAME = args.dump_partition[0]
            OUTFILE = args.dump_partition[1]
            dev.dump_partition(PARTITION_NAME, OUTFILE)
            print(f'dumped partition to {OUTFILE}')
    elif args.restore_partition:
        dev = enter_burn_mode(dev)
        if dev is not None:
            PARTITION_NAME = args.restore_partition[0]
            INFILE = args.restore_partition[1]
            dev.restore_partition(PARTITION_NAME, INFILE)
            print(f'restored partition from {INFILE}')
    elif args.dump_device:
        dev = enter_burn_mode(dev)
        if dev is not None:
            FOLDER_NAME = args.dump_device[0]
            print(f'dumping entire device to {FOLDER_NAME}')
            shutil.rmtree(FOLDER_NAME, ignore_errors=True)
            os.mkdir(FOLDER_NAME)
            dev.dump_partition('bootloader', f'{FOLDER_NAME}/bootloader.dump')
            dev.dump_partition('env', f'{FOLDER_NAME}/env.dump')
            # convert dumped env to txt version, for ease of access, 
            #   and so it is present when restoring later
            convert_env_dump(f'{FOLDER_NAME}/env.dump', f'{FOLDER_NAME}/env.txt')
            dev.dump_partition('fip_a', f'{FOLDER_NAME}/fip_a.dump')
            dev.dump_partition('fip_b', f'{FOLDER_NAME}/fip_b.dump')
            dev.dump_partition('logo', f'{FOLDER_NAME}/logo.dump')
            dev.dump_partition('dtbo_a', f'{FOLDER_NAME}/dtbo_a.dump')
            dev.dump_partition('dtbo_b', f'{FOLDER_NAME}/dtbo_b.dump')
            dev.dump_partition('vbmeta_a', f'{FOLDER_NAME}/vbmeta_a.dump')
            dev.dump_partition('vbmeta_b', f'{FOLDER_NAME}/vbmeta_b.dump')
            dev.dump_partition('boot_a', f'{FOLDER_NAME}/boot_a.dump')
            dev.dump_partition('boot_b', f'{FOLDER_NAME}/boot_b.dump')
            dev.dump_partition('misc', f'{FOLDER_NAME}/misc.dump')
            dev.dump_partition('settings', f'{FOLDER_NAME}/settings.ext4')
            dev.dump_partition('system_a', f'{FOLDER_NAME}/system_a.ext2')
            dev.dump_partition('system_b', f'{FOLDER_NAME}/system_b.ext2')
            dev.dump_partition('data', f'{FOLDER_NAME}/data.ext4')
            print('device dump complete')
    elif args.restore_device:
        dev = enter_burn_mode(dev)
        if dev is not None:
            # NOTE: here we do NOT touch bootloader partition
            FOLDER_NAME = args.restore_device[0]
            print(f'restoring entire device from dumpfiles in {FOLDER_NAME}')
            FILE_LIST = [
                'fip_a.dump', 'fip_b.dump', 'logo.dump', 'dtbo_a.dump', 'dtbo_b.dump', 'vbmeta_a.dump',
                'vbmeta_b.dump', 'boot_a.dump', 'boot_b.dump', 'misc.dump', 'settings.ext4', 'system_a.ext2', 'system_b.ext2',
            ]
            for part_name in FILE_LIST:
                if not os.path.isfile(f'{FOLDER_NAME}/{part_name}'):
                    print(f'Error: missing expected dump file: {FOLDER_NAME}/{part_name}')
                    sys.exit(1)
            # we use the .txt instead of .dump because sometimes the partition size does not line up perfectly
            #   also probably the safer way to interact with env partition
            #   if txt version does not exist, we create it for you
            if not os.path.isfile(f'{FOLDER_NAME}/env.txt'):
                if not os.path.isfile(f'{FOLDER_NAME}/env.dump'):
                    print(f'Error: missing expected dump file: {FOLDER_NAME}/env.dump')
                    sys.exit(1)
                convert_env_dump(f'{FOLDER_NAME}/env.dump', f'{FOLDER_NAME}/env.txt')
            print('Wiping env partition')
            dev.bulkcmd('amlmmc env')
            dev.bulkcmd('amlmmc erase env')
            dev.send_env_file(f'{FOLDER_NAME}/env.txt')
            dev.bulkcmd('env save')
            dev.restore_partition('fip_a', f'{FOLDER_NAME}/fip_a.dump')
            dev.restore_partition('fip_b', f'{FOLDER_NAME}/fip_b.dump')
            dev.restore_partition('logo', f'{FOLDER_NAME}/logo.dump')
            dev.restore_partition('dtbo_a', f'{FOLDER_NAME}/dtbo_a.dump')
            dev.restore_partition('dtbo_b', f'{FOLDER_NAME}/dtbo_b.dump')
            dev.restore_partition('vbmeta_a', f'{FOLDER_NAME}/vbmeta_a.dump')
            dev.restore_partition('vbmeta_b', f'{FOLDER_NAME}/vbmeta_b.dump')
            dev.restore_partition('boot_a', f'{FOLDER_NAME}/boot_a.dump')
            dev.restore_partition('boot_b', f'{FOLDER_NAME}/boot_b.dump')
            dev.restore_partition('misc', f'{FOLDER_NAME}/misc.dump')
            dev.restore_partition('settings', f'{FOLDER_NAME}/settings.ext4')
            dev.restore_partition('system_a', f'{FOLDER_NAME}/system_a.ext2')
            dev.restore_partition('system_b', f'{FOLDER_NAME}/system_b.ext2')
            # handle data partition last
            if not os.path.exists(f'{FOLDER_NAME}/data.ext4'):
                print(f'did not find {FOLDER_NAME}/data.ext4, erasing data partition instead')
                dev.bulkcmd('amlmmc erase data')
            else:
                # test if data.ext4 is actually all zeros (dumped a wiped filesystem)
                #   A true stock image has that partition erased, and it gets formatted at first boot
                #   if this dump is from stock, then we can save time by just erasing that partition
                TEST_CHUNK = None
                with open(f'{FOLDER_NAME}/data.ext4', 'rb') as daf:
                    # read the first 1024KB
                    TEST_CHUNK = daf.read(1024 * 1024)
                try:
                    DECODED_CHUNK = TEST_CHUNK.decode('ascii').strip('\x00')
                except Exception:
                    # since it is not really ascii, decoding will only work if all the
                    # bytes are within the appropriate range for ascii
                    # however, if it fails to decode, then it is definitely NOT all zeroed out
                    DECODED_CHUNK = '42' # just needs to not be empty
                if DECODED_CHUNK == '':
                    print(f'The first 1MB of {FOLDER_NAME}/data.ext4 are null, erasing data partition instead')
                    dev.bulkcmd('amlmmc erase data')
                else:
                    dev.restore_partition('data', f'{FOLDER_NAME}/data.ext4')
            # always do bootloader last
            dev.restore_partition('bootloader', f'{FOLDER_NAME}/bootloader.dump')
            dev.bulkcmd('reset')
            print('device restore complete')
    elif args.disable_charger_check:
        dev = enter_burn_mode(dev)
        if dev is not None:
            print('Disabling check for valid charger')
            # normally, bootcmd=run check_charger
            #   if it detects OK charger, it then calls: run storeboot
            #   so we can skip the check by changing bootcmd to just call: run storeboot
            dev.bulkcmd('amlmmc env')
            dev.bulkcmd('setenv bootcmd "run storeboot"')
            dev.bulkcmd('env save')
            print('The device will not check for valid charger')
    elif args.enable_charger_check:
        dev = enter_burn_mode(dev)
        if dev is not None:
            dev.bulkcmd('amlmmc env')
            dev.bulkcmd('setenv bootcmd "run check_charger"')
            dev.bulkcmd('env save')
            print('The device will now check for valid charger, requiring you to press menu button to bypass')
    elif args.burn_mode:
        if check_device_mode('usb'):
            print('Entering USB Burn Mode')
            dev.bl2_boot(str(IMAGES_PATH.joinpath('superbird.bl2.encrypted.bin')), str(IMAGES_PATH.joinpath('superbird.bootloader.img')))
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
    elif args.restore_stock_env:
        ENV_FILE = 'stock_env.txt'
        dev = enter_burn_mode(dev)
        if dev is not None:
            print('Restoring env by first wiping env, then importing stock_env.txt')
            dev.bulkcmd('amlmmc env')
            dev.bulkcmd('amlmmc erase env')
            dev.send_env_file(ENV_FILE)
            dev.bulkcmd('env save')
    elif args.send_env:
        ENV_FILE = args.send_env[0]
        dev = enter_burn_mode(dev)
        if dev is not None:
            # Do not wipe env partition first, just import values from given file
            print(f'Importing the contents of {ENV_FILE}')
            dev.bulkcmd('amlmmc env')
            dev.send_env_file(ENV_FILE)
            dev.bulkcmd('env save')
    elif args.send_full_env:
        ENV_FILE = args.send_full_env[0]
        dev = enter_burn_mode(dev)
        if dev is not None:
            # wipe the env partition, then import from given file
            print('Wiping env partition')
            dev.bulkcmd('amlmmc env')
            dev.bulkcmd('amlmmc erase env')
            print(f'Importing the contents of {ENV_FILE}')
            dev.send_env_file(ENV_FILE)
            dev.bulkcmd('env save')
    elif args.get_env:
        ENV_FILE = args.get_env[0]
        dev = enter_burn_mode(dev)
        if dev is not None:
            with tempfile.NamedTemporaryFile() as TEMP_FILE:
                print(f'Getting current env and writing to text file: {ENV_FILE}')
                dev.dump_partition('env', TEMP_FILE.name)
                convert_env_dump(TEMP_FILE.name, ENV_FILE)

    END_TIME = time.time()
    TIME_DELTA = END_TIME - START_TIME
    print(f'Operation took: {str(TIME_DELTA)}')

    sys.exit()
