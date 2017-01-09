#!/bin/sh

cd ~/myrepo/pythondotorg
source venv/bin/activate
./manage.py generate_pep_pages
deactivate

cd ~/Mariatta_github/restify_me
python open_web.py