# Cross-Platform Spotify Car Thing (superbird) hacking toolkit

This toolkit re-implements most of the functionality from [frederic's scripts](https://github.com/frederic/superbird-bulkcmd).
The key difference here, is that this tool uses [`pyamlboot`](https://github.com/superna9999/pyamlboot) instead of the proprietary `update` binary from Amlogic, 
which allows it to work on many more platforms!

Everything in [`images/`](images/) came directly from [frederic's repo](https://github.com/frederic/superbird-bulkcmd).

The purpose of this tool is to provide useful, working examples for how to use `pyamlboot` to perform development-related tasks on the Spotify Car Thing.

Contributions are welcome. This code is unlicensed: you can do whatever you want with it.
 `pyamlboot` is Apache-2.0, `libusb` is LGPL-2.1

A [Changelog can be found here](Changelog.md)

## Warranty and Liability

None. You definitely can mess up your device in ways that are difficult to recover. I cannot promise a bug in this script will not brick your device.
By using this tool, you accept responsibility for the outcome. 

I highly recommend connecting to the UART console, [frederic's repo](https://github.com/frederic/superbird-bulkcmd) has some good pictures showing where the pads are.

Make backups.

## One Big Caveat
This tool tries to replace the proprietary `update` binary from Amlogic, and it covers enough functionality to be useful for superbird.
However, dumping partitions is MUCH slower.

The original tool from Amlogic manages to read directly from the mmc, without having to first read it into memory, 
so it is a lot faster at about `12MB/s` or about 7 minutes to dump all partitions.
Unfortunately, we cannot currently replicate this method using `pyamlboot`.

Instead, to dump partitions we first have to tell the device to read a chunk (128KB) into memory, and then we can read it from memory out to a file, one chunk at a time.
The copy rate for reading is about `545KB/s`, and in my testing on Ubuntu x86_64 it takes about 110 minutes to dump all partitions!

The same thing must be done in reverse to restore a partition, but writing is much faster, and we can use larger chunks (512KB), 
so copy rate for writing is about `4.9MB/s`, and it takes about 17 minutes to write all partitions.

Partitions 2MB and smaller can be written in a single chunk, but using 2MB chunks for larger partitions eventually fails about 300MB through; I have not yet figured out why.
In the meantime, it seems that 512KB chunks work well for larger partitions.

## Supported Platforms

The only requirements to run this are:
1. python3
2. libusb
3. pyamlboot from [github master branch](https://github.com/superna9999/pyamlboot)

You need to install pyamlboot from [github master branch](https://github.com/superna9999/pyamlboot) because the current pypy package is too old,
and is missing `bulkcmd` functionality.

### macOS
Tested on `aarch64` and `x86_64`

On macOS, you must install `python3` and `libusb` from homebrew, and execute using that version of python
```bash
brew install python3 libusb
/opt/homebrew/bin/python3 -m pip install git+https://github.com/superna9999/pyamlboot
/opt/homebrew/bin/python3 superbird_tool.py
```
`root` is not needed on macOS

### Linux
Tested on `aarch64` and `x86_64`

On Linux, you just need to install pyamlboot.
However, `root` is needed on Linux, unless you fiddle with udev rules, which means the pip package also needs to be installed as `root`
```bash
sudo python3 -m pip install git+https://github.com/superna9999/pyamlboot
sudo ./superbird_tool.py
```

### Windows

Tested on `x86_64`

On Windows, you need to download and install python3 (recommend 3.10.8) from [python.org](https://www.python.org/downloads/windows/) and execute using `python` instead of `python3`. 
```bash
python -m pip install git+https://github.com/superna9999/pyamlboot
python superbird_tool.py
```
If you're getting a device not found error despite the car thing showing up in device manager, you may need libusb. Here's how to install it:
1. Download `libusb-1.0.26-binaries.7z` from here: https://github.com/libusb/libusb/releases
2. Extract all the files then go into the VS2015 folder that matches your CPU architecture
3. Go into the dll folder then copy libusb-1.0.dll to a folder where you can work with it.
4. Just to be safe, run the file thru VirusTotal or a similar service and make sure the SHA256 hash matches this: `1dac95d1eafcba057cf3df73dcf419bc14f4167ef4ac92fe1f8fdcab4278b6f4`
5. If it matches, just copy the file to `C:\Windows\System32` then try running superbird-tool again.

## Usage
```
Options cannot be combined; do one thing at a time :)

options:
  -h, --help            show this help message and exit
  --find_device         find superbird device and show its current boot mode
  --burn_mode           enter USB Burn Mode (if currently in USB Mode)
  --continue_boot       continue booting normally (if currently in USB Burn Mode)
  --bulkcmd COMMAND     run a uboot command on the device
  --boot_adb_kernel BOOT_SLOT
                        boot a kernel with adb enabled on chosen slot (A or B)(not persistent)
  --enable_uart_shell   enable UART shell
  --disable_avb2 BOOT_SLOT
                        disable A/B booting, lock to chosen slot(A or B)
  --enable_burn_mode    enable USB Burn Mode at every boot (when connected to USB host)
  --enable_burn_mode_button
                        enable USB Burn Mode if preset button 4 is held while booting (when connected to USB host)
  --disable_burn_mode   Disable USB Burn Mode at every boot (when connected to USB host)
  --disable_charger_check
                        disable check for valid charger at boot
  --enable_charger_check
                        enable check for valid charger at boot
  --dump_device OUTPUT_FOLDER
                        Dump all partitions to a folder
  --restore_device INPUT_FOLDER
                        Restore all partitions from a folder
  --dump_partition PARTITION_NAME OUTPUT_FILE
                        Dump a partition to a file
  --restore_partition PARTITION_NAME INPUT_FILE
                        Restore a partition from a dump file
  --restore_stock_env   wipe env, then restore default env values from stock_env.txt
  --send_env ENV_TXT    import contents of given env.txt file (without wiping)
  --send_full_env ENV_TXT
                        wipe env, then import contents of given env.txt file
  --convert_env_dump ENV_DUMP OUTPUT_TXT
                        convert a local dump of env partition into text format
  --get_env ENV_TXT     dump device env partition, and convert it to env.txt format
```

## Boot Modes
There are four possible boot modes

### USB Mode
This is what you get if you hold buttons 1 & 4 while plugging in the device.

The UART console will print: 
```
G12A:BL:0253b8:61aa2d;FEAT:F0F821B0:12020;POC:D;RCY:0;USB:0;
```

In this mode, the device shows up on USB as: `1b8e:c003 Amlogic, Inc. GX-CHIP`

### USB Burn Mode
This is a special uboot image, which we can interact with via usb.

The UART console output will typicaly end with:
```
U-Boot 2015.01 (Jan 21 2022 - 08:55:34 - v1.0-57-gec3ec936c2)

DRAM:  512 MiB
Relocation Offset is: 16e42000
InUsbBurn
[MSG]sof
Set Addr 11
Get DT cfg
Get DT cfg
set CFG
``` 
Which indicates it is ready to receive commands

In this mode, the device shows up on USB as: `1b8e:c003 Amlogic, Inc.`

### Normal Bootup
If USB Burn mode is not enabled at every boot, or if you use `--continue_boot`, the device will boot up normally and launch the Spotify app.

In this mode, the device does not show up on USB.

### Normal Bootup with USB Gadget
If you use `--boot_adb_kernel`, a modified kernel and image will be uploaded to the device (non-persistent), which enables USB Gadget.

The USB Gadget can be configured to provide `adb` (like an Android phone), among other possible functionality including `rndis` for usb networking.

In this mode, the device shows up on USB as: `18d1:4e40 Google Inc. Nexus 7 (fastboot)`

Please do NOT try to use fastboot with superbird device, there is potential to brick it.

## Persistent USB Gadget with USB Networking

I have provided an [`S49usbgadget`](S49usbgadget), which can be placed on the device at `/etc/init.d/S49usbgadget` (make it executable).

This is a modified version of what [frederic provided](https://github.com/frederic/superbird-bulkcmd/blob/main/scripts/enable-adb.sh.client),
where I added a lot of comments, and added `rndis` function, to allow usb networking in addition to `adb`. 

Please read it carefully before using.

You can try this [host setup script](setup_host_usbnet.sh) to configure a Linux machine as host. 
I am using a RockPi-E with Armbian Community Kinetic 22.10 with success

## Example Usage

As an example (on Linux), here are steps to enable persistent adb and usbnet, disable a/b booting, and disable charger check, on a fresh device.

```
# starting from a fresh device

# plug in with buttons 1 & 4 held
sudo ./superbird_tool.py --find_device  # check that it is in usb mode
sudo ./superbird_tool.py --burn_mode
sudo ./superbird_tool.py --enable_burn_mode
sudo ./superbird_tool.py --disable_avb2  # disable A/B, lock to A
sudo ./superbird_tool.py --disable_charger_check

# unplug and replug without holding any buttons

sudo ./superbird_tool.py --find_device   # check that it is in usb burn mode
sudo ./superbird_tool.py --boot_adb_kernel

# device boots to spotify logo, but app does not launch

adb devices  # check that your device shows up in adb

# setup persistent USB Gadget (adb and usbnet)
adb shell mount -o remount,rw /
adb shell umount /etc/init.d/S49usbgadget
adb push S49usbgadget /etc/init.d/
adb shell chmod +x /etc/init.d/S49usbgadget
adb shell mount -o remount,ro /  # OK if this step fails
adb shell reboot

# device can take a while to reboot, just watch what the screen does and run --find_device until it shows up
sudo ./superbird_tool.py --find_device   # check that it is in usb burn mode
sudo ./superbird_tool.py --disable_burn_mode

# unplug and replug without holding any buttons
#   it should boot normally (app should launch), now with adb and usbnet enabled

ip addr  # you should see usb0 listed
```

## Known Issues
* The option `--enable_uart_shell` is really only meant to be run on a fresh device. It will rewrite `initargs` env var, removing any other changes you made like using a particular system partition every boot.
* The option `--disable_avb2` will ALSO enable the uart shell; consider using that instead.
* if you use `--disable_burn_mode`, then boot to USB Mode (hold 1 & 4), and use `--burn_mode`, followed by `--boot_adb_kernel`, it will fail with an error about device tree
  * not sure why this is happening, if you do `--enable_burn_mode`, let it boot to USB Burn Mode automatically, then use `--boot_adb_kernel`, it works fine
  * another workaround is to make USB Gadget persistent (see section above), then you do not need `--boot_adb_kernel`
* In some cases you might get a Timeout Error. This happens sometimes if a previous command failed, and you just need to power cycle the device (actually unplug and plug it back in), and try again. 
  * ALSO, avoid connecting the device through a USB hub. In my testing, I had many more timeout issues when using a hub.
  * You might need to power cycle and try again multiple times

## Making Standalone Binaries

I have provided a (very barebones) script to generate a standalone `superbird_tool` binary using `nuitka`.

You need to install `nuitka`, `zstandard` and `ordered-set` packages from pip to use it.

On Linux, you also need to install `patchelf` from your system package manager. ex: `sudo apt-get install -y patchelf`

I have not tested this much yet, just a neat idea for now.

Note that a compiled binary does not include `images/`, and will still look for them under the current working directory.

If you are making binaries, you must use python version 3.10.8, as the newer 3.11 does not work with nuitka.
