#!/usr/bin/env python3
"""
https://chromium.googlesource.com/chromiumos/platform/uboot-env

# This script allows listing, reading environment variables for
# u-boot, that usually live in an area of a block device (NVRAM, e.g. NAND or
# NOR flash).
# The u-boot environment variable area is a crc (4 bytes) followed by all
# environment variables as "key=value" strings (\0-terminated) with \0\0
# (empty string) to indicate the end.
"""
# pylint: disable=line-too-long,broad-except


# Copyright (c) 2010 The Chromium OS Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found below

# // Copyright (c) 2010 The Chromium OS Authors. All rights reserved.
# //
# // Redistribution and use in source and binary forms, with or without
# // modification, are permitted provided that the following conditions are
# // met:
# //
# //    * Redistributions of source code must retain the above copyright
# // notice, this list of conditions and the following disclaimer.
# //    * Redistributions in binary form must reproduce the above
# // copyright notice, this list of conditions and the following disclaimer
# // in the documentation and/or other materials provided with the
# // distribution.
# //    * Neither the name of Google Inc. nor the names of its
# // contributors may be used to endorse or promote products derived from
# // this software without specific prior written permission.
# //
# // THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
# // "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
# // LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR
# // A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT
# // OWNER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL,
# // SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT
# // LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE,
# // DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY
# // THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
# // (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
# // OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.


# bishopdynamics, November 2022:
#   I made a number of modifications, and modernizations,
#   to bring it to python3, and satisfy my linter
#   and removed anything I was not going to use

import binascii
import struct


def read_environ(file):
    """ Reads the u-boot environment variables from a partition dump file.
        returns a tuple containing: env as a dict, length of data in file, wether crc match
    """
    data = None
    with open(file, "rb") as evf:
        data = evf.read()
    (crc,) = struct.unpack("I", data[0:4])
    real_data = data[4:]
    real_crc = binascii.crc32(real_data) & 0xffffffff
    environ = {}
    for segment in real_data.decode('ascii').split("\x00"):
        if not segment:
            break
        key, value = segment.split('=', 1)
        environ[key] = value
    return (environ, len(data), crc == real_crc)
