#!/usr/bin/env bash
set -eu
cd "$(dirname "$0")"
python -m pip install -r requirements.txt
python cut/manage.py check --deploy --fail-level ERROR
python cut/manage.py collectstatic --noinput
