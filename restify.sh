#!/bin/sh

python -m collect_text_peps ../peps --copy
cd ../peps
source venv/bin/activate
make -j
deactivate

