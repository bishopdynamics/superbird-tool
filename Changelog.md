# Changelog

## 0.0.6
* options that require USB Burn Mode will now attempt to enter USB Burn Mode automatically
* added `--restore_partition` to restore individual partitions from file
* added `--restore_device` to restore whole device from a folder
  * expects files: `bootloader.dump, env.dump, fip_a.dump, fip_b.dump, logo.dump, dtbo_a.dump, dtbo_b.dump, vbmeta_a.dump,vbmeta_b.dump, boot_a.dump, boot_b.dump, misc.dump, settings.ext4, system_a.ext2, system_b.ext2`
  * if the dump file `data.ext4` is missing, or is actually empty (all zeros), will just wipe the data partition to save time
* corrected `bootloader` partition size. 
  * The partition is 4MB, but device will only accept up to 2MB when writing
  * partition is zero-padded and the actual bootloader is about 1.3MB
  * starting with this version, `--dump_partition` and `--dump_device` will produce 2MB dumps of `bootloader` partition
  * `--restore_partition` and `--restore_device`, if they find a 4MB `bootloader.dump` will only restore first 2MB of it
* fixed issue where `bootloader` dumps started with 512 Bytes of padding
* option `--dump_device` will convert env.dump into env.txt (keeping both)

## 0.0.5
* Added boot slot selection to `--boot_adb_kernel` & `--disable_avb`.

## 0.0.4
* fixed #2 & #4 - wrong encoding when sending env to device

## 0.0.3
* added `--enable_burn_mode_button` thanks to lmore337!

## 0.0.2 November 1, 2022

* added `--restore_stock_env` - wipe uboot env partition, then restore it to stock values by importing `stock_env.txt`
* added `--send_env` <env.txt> - send given `env.txt`, import it into the existing env. Will NOT wipe first, just overwrite
* added `--send_full_env` <env.txt> - wipe uboot env partition, then import the given `env.txt`
* added `--convert_env_dump` <env.dump> - convert a partition dump file, into a readable `env.txt` which you can edit
* added `--get_env` <env.txt> - dump the device env partition and convert it to `env.txt` 


## 0.0.1 - October 20, 2022
* initial release
* fixed issue #1: not sending env with --boot_adb_kernel