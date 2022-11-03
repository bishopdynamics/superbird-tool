# Changelog

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