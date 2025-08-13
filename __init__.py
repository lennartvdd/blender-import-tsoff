# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Lennart van den Dool
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:

bl_info = {
    "name": "Import Triangle Splatting OFF",
    "author": "Lennart van den Dool",
    "version": (1, 2, 0),
    "blender": (3, 0, 0),
    "location": "File > Import > Triangle Splatting OFF",
    "description": "Import OFF/COFF/NOFF and Triangle Splatting variants with per-face/vertex color and automatic material hookup (alpha + additive emission).",
    "category": "Import-Export",
}

from .import_ts_off import register, unregister
