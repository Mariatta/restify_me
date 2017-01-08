#!/bin/sh

python3 -m collect_text_peps ../peps --copy
cd ../peps
source venv/bin/activate
make -j
deactivate
cd ~/myrepo/pythondotorg
source venv/bin/activate
./manage.py generate_pep_pages
deactivate
ECHO "done"