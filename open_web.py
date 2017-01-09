#!/usr/bin/env python

import webbrowser
import os

peps = os.listdir('./backups')
for pep in peps:
    pep_url = pep.replace(".txt", "")
    pep_path = f"http://localhost:8000/dev/peps/{pep_url}"
    webbrowser.open(pep_path)