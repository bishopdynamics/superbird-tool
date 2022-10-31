#!/usr/bin/env python3
"""
Wrapper for performing tasks on superbird device
"""
# pylint: disable=line-too-long,broad-except

import sys
import time
import traceback
import platform

try:
    from pyamlboot import pyamlboot
    from usb.core import USBTimeoutError, USBError
    import usb.core
except ImportError:
    print("""
    ###########################################################################################

    Error while importing pyamlboot!
    """)
    if platform.system() == 'Darwin':
        print("""
        on macOS, you must install python3 and libusb from homebrew, 
        and execute using that version of python
            brew install python3 libusb
            /opt/homebrew/bin/python3 -m pip install git+https://github.com/superna9999/pyamlboot
            /opt/homebrew/bin/python3 superbird_tool.py
        root is not needed on macOS
        """)
    elif platform.system() == 'Linux':
        print("""
        on Linux, you just need to install pyamlboot
        root is needed on Linux, unless you fiddle with udev rules, 
        which means the pip package also needs to be installed as root
            sudo python3 -m pip install git+https://github.com/superna9999/pyamlboot
            sudo ./superbird_tool.py
        """)
    else:
        print("""
        on Windows, you need to download and install python3 from https://www.python.org/downloads/windows/
        and execute using "python" instead of "python3"
            python -m pip install git+https://github.com/superna9999/pyamlboot
            python superbird_tool.py
        """)
    print("""
    You need to install pyamlboot from github because the current pypy package is too old
    
    ############################################################################################
    """)
    sys.exit(1)

from superbird_partitions import SUPERBIRD_PARTITIONS

def find_device():
    """ Find a superbird device and return its mode
        modes: normal, usb, usb-burn
    """
    found_devices = usb.core.find(idVendor=0x18d1, idProduct=0x4e40)
    if found_devices is not None:
        dev_product = found_devices[0].device.product
        print('Found device booted normally, with USB Gadget (adb/usbnet) enabled')
        return 'normal'
    found_devices = usb.core.find(idVendor=0x1b8e, idProduct=0xc003)
    if found_devices is not None:
        dev_product = found_devices[0].device.product
        if dev_product is None:
            print('Found device booted in USB Burn Mode (ready for commands)')
            return 'usb-burn'
        elif dev_product == 'GX-CHIP':
            print('Found device booted in USB Mode (buttons 1 & 4 held at boot)')
            return 'usb'
    print('No device found!')
    return 'not-found'

def check_device_mode(mode:str):
    """ confirm if device is in the mode we need """
    dev_mode = find_device()
    if dev_mode != mode:
        print('Device is not booted to the correct mode!')
        if mode == 'usb':
            print('     need to power on while holding buttons 1 & 4 to enter USB Mode')
        elif mode == 'usb-burn':
            print('     need to boot into USB Burn Mode')
        elif mode == 'normal':
            print('     need to boot up normally first')
        return False
    return True

class SuperbirdDevice:
    """ convenience wrapper for superbird device """
    ADDR_BL2 = 0xfffa0000
    ADDR_KERNEL = 0x01080000
    ADDR_INITRD = 0x13000000
    ADDR_TMP = 0x13000000
    # commands which cause a usb timeout when reading response
    #   for any other commands, we raise an exception if they cause a timeout
    TIMEOUT_COMMANDS = ['booti', 'bootm', 'bootp', 'mw.b', 'reset', 'reboot']
    PARTITIONS = SUPERBIRD_PARTITIONS
    PART_SECTOR_SIZE = 512  # bytes, size of sectors used in partition table

    def __init__(self) -> None:
        try:
            self.device = pyamlboot.AmlogicSoC()
        except ValueError:
            print('Device not found, is it in usb burn mode?')
            sys.exit(1)
        except USBError as exu:
            if exu.errno == 13:
                # [Errno 13] Access denied (insufficient permissions)
                print(f'{exu}, need to run as root')
                sys.exit(1)
            else:
                print(f'Error: {exu}')
                print(traceback.format_exc())
                sys.exit(1)
        else:
            if not hasattr(self.device, 'bulkCmd'):
                self.print('Detected an old version of pyamlboot which lacks AmlogicSoC.bulkCmd')
                self.print('Need to install from the github master branch')
                self.print(' need to uninstall the current version, then install from github')
                self.print('  python3 -m pip uninstall pyamlboot')
                self.print('  python3 -m pip install git+https://github.com/superna9999/pyamlboot')
                sys.exit(1)

    @staticmethod
    def decode(response):
        """ decode a response """
        return response.tobytes().decode("utf-8")

    @staticmethod
    def print(message:str):
        """ print a message to console
            on Windows, need to flush after printing
            or nothing will show up until script is complete
        """
        print(message)
        sys.stdout.flush()

    def bulkcmd(self, command:str, ignore_timeout=False, silent=False):
        """ perform a bulkcmd, separated by semicolon """
        if not silent:
            self.print(f' executing bulkcmd: "{command}"')
        try:
            response = self.device.bulkCmd(command)
            if not silent:
                self.print(f'  result: {self.decode(response)}')
            if 'failed' in self.decode(response):
                raise Exception(f'Bulkcmd failed: {command}')
        except USBTimeoutError:
            # if you use booti or mw.b, it wont return, thus will raise USBTimeoutError
            if [word for word in self.TIMEOUT_COMMANDS if word in command] or ignore_timeout:
                if not silent:
                    self.print('  ...')
            else:
                self.print(' Error: bulkcmd timed out!')
                self.print(' This can happen if the device ends up in a strange state, like as the result of a previously failed command')
                self.print(' Try power cycling the device by pulling the cable, and then boot up and try again')
                self.print('    If the device is connected through a USB hub, try connecting it directly to a port on your machine')
                sys.exit(1)
        except USBError:
            # on Windows, raises USBError instead of USBTimeoutError
            if [word for word in self.TIMEOUT_COMMANDS if word in command] or ignore_timeout:
                if not silent:
                    self.print('  ...')
            else:
                self.print(' Error: bulkcmd timed out!')
                self.print(' This can happen if the device ends up in a strange state, like as the result of a previously failed command')
                self.print(' Try power cycling the device by pulling the cable, and then boot up and try again')
                self.print('    If the device is connected through a USB hub, try connecting it directly to a port on your machine')
                sys.exit(1)

    def write(self, address:int, data, chunk_size=8):
        """ write data to an address """
        self.print(f' writing to: {hex(address)}')
        self.device.writeLargeMemory(address, data, chunk_size, True)

    def send_env(self, env_string:str):
        """ send given env string to device, space-separated kernel args on one line """
        env_size = len(env_string.encode('utf-8'))
        self.print('initializing env subsystem')
        self.bulkcmd('amlmmc env')  # initialize env subsystem
        self.print(f'sending env ({env_size} bytes)')
        self.write(self.ADDR_TMP, env_string.encode('utf-8'))  # write env string somewhere
        self.bulkcmd(f'env import -t {hex(self.ADDR_TMP)} {hex(env_size)}')  # read env from string

    def send_env_file(self, env_file:str):
        """ read env.txt, then send it to device """
        env_data = ''
        with open(env_file, 'r', encoding='utf-8') as envf:
            env_data = envf.read()
        self.send_env(env_data)

    def send_file(self, filepath:str, address:int):
        """ write given file to device memory at given address """
        self.print(f'writing {filepath} at {hex(address)}')
        file_data = None
        with open(filepath, 'rb') as flp:
            file_data = flp.read()
        self.write(address, file_data, chunk_size=512)

    def bl2_boot(self, bl2_file:str, bootloader_file:str):
        """ send a bl2 and then chain a uboot image with it """
        self.send_file(bl2_file, self.ADDR_BL2)
        self.device.run(self.ADDR_BL2)
        data = None
        with open(bootloader_file, 'rb') as blf:
            data = blf.read()
        time.sleep(2)

        prev_length = -1
        prev_offset = -1
        seq = 0
        while True:
            (length, offset) = self.device.getBootAMLC()

            if length == prev_length and offset == prev_offset:
                self.print("[BL2 END]")
                break

            prev_length = length
            prev_offset = offset

            self.print(f'AMLC dataSize={length}, offset={offset}, seq={seq}')
            self.device.writeAMLCData(seq, offset, data[offset:offset+length])
            self.print("[DONE]")

            seq = seq + 1

    def boot(self, env_file:str, kernel:str, initrd:str):
        """ boot using given env.txt, kernel, kernel address, and initrd, intitrd_address """
        self.print(f'Booting {env_file}, {kernel}, {initrd}')
        self.send_env_file(env_file)
        self.send_file(kernel, self.ADDR_KERNEL)
        self.send_file(initrd, self.ADDR_INITRD)
        self.print('Booting kernel with initrd')
        self.bulkcmd(f'booti {hex(self.ADDR_KERNEL)} {hex(self.ADDR_INITRD)}')

    def read_memory(self, address, length):
        """Read some data from memory"""
        data = None
        offset = 0
        while length:
            if length >= 64:
                read_data = self.device.readSimpleMemory(address + offset, 64).tobytes()
                if data is not None:
                    data = data + read_data
                else:
                    data = read_data
                length = length - 64
                offset = offset + 64
            else:
                read_data = self.device.readSimpleMemory(address + offset, length).tobytes()
                if data is not None:
                    data = data + read_data
                else:
                    data = read_data
                break
        return data

    def dump_partition(self, part_name:str, outfile:str,):
        """ dump given partition to a file
                we cannot access the mmc directly,
                but we can read from mmc into memory,
                so we read it into memory, then read it from memory and append it to file, one chunk at a time
                this is excruciatingly slow, compared to dumping using the offical amlogic tool, about 500KB/s, roughly 110 minutes to dump
        """
        chunk_size = 256 * self.PART_SECTOR_SIZE  # 256 sectors seems to be the sweet spot based on time trials
        if part_name not in self.PARTITIONS:
            raise ValueError(f'Invalid partition name: {part_name}')
        # part_offset = self.PARTITIONS[part_name]['offset']
        part_size = self.PARTITIONS[part_name]['size'] * self.PART_SECTOR_SIZE
        self.bulkcmd('amlmmc env', silent=True)  # initialize amlmmc subsystem
        time.sleep(0.2)
        # first we try to read the LAST chunk into memory, to see if it exceeds the bounds of the partition
        print(f'validating partition size:{hex(part_size)}')
        try:
            self.bulkcmd(f'amlmmc read {part_name} {hex(self.ADDR_TMP)} {hex(part_size - chunk_size)} {hex(chunk_size)}', silent=True)
        except Exception as extest:
            if part_name == 'data':
                part_size = self.PARTITIONS[part_name]['size_alt'] * self.PART_SECTOR_SIZE
                print(f'Failed while fetching last chunk of partition: {part_name}, trying alternate size: {hex(part_size)}')
                print(f'validating partition size:{hex(part_size)}')
                try:
                    self.bulkcmd(f'amlmmc read {part_name} {hex(self.ADDR_TMP)} {hex(part_size - chunk_size)} {hex(chunk_size)}', silent=True)
                except Exception as extestt:
                    print(f'Failed while testing last chunk of partition: {part_name}, is partition size {hex(part_size)} correct? error: {extestt}')
                    sys.exit(1)
            else:
                print(f'Failed while testing last chunk of partition: {part_name}, is partition size {hex(part_size)} correct? error: {extest}')
                sys.exit(1)
        time.sleep(0.2)
        # now we are ready to actually dump the partition
        open(outfile, 'wb').close()  # empty the file
        with open(outfile, 'ab') as ofl:
            offset = 0
            first_chunk = True
            last_chunk = False
            remaining = part_size
            while remaining:
                if first_chunk:
                    first_chunk = False
                else:
                    sys.stdout.write("\x1b[1A\x1b[2K")  # move cursor up one line, and delete that whole line
                if remaining <= chunk_size:
                    chunk_size = remaining
                    last_chunk = True
                progress = round((offset / part_size) * 100)
                self.print(f'dumping partition: "{part_name}" offset: {hex(offset)} chunk_size: {chunk_size / 1024}KB, into file: {outfile} progress: {progress}%')
                self.bulkcmd(f'amlmmc read {part_name} {hex(self.ADDR_TMP)} {hex(offset)} {hex(chunk_size)}', silent=True)
                time.sleep(0.2)
                rdata = self.read_memory(self.ADDR_TMP, chunk_size)
                ofl.raw.write(rdata)
                ofl.flush()
                time.sleep(0.2)
                if last_chunk:
                    break
                offset += chunk_size
                remaining -= chunk_size
