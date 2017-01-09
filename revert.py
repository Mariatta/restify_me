#!/usr/bin/env python

import os, shutil

files = os.listdir('./backups/')
for filename in files:
    print(filename)
    backed_up = os.path.join("./backups", filename)
    origin = os.path.join("../peps", filename)
    shutil.copy(backed_up, origin)
    print(f"reverted {origin}")