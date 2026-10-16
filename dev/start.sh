#!/bin/sh
set -eu
python dev/seed.py
if [ ! -d data/.git ]; then
  git -C data init -q
  git -C data config user.name "HackBank development"
  git -C data config user.email "dev@localhost"
  git -C data add .
  git -C data commit -qm "Initial sample data"
fi
exec python -u kassa.py
