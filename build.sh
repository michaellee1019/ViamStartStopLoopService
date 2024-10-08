#!/bin/bash
apt-get install -y python3.11-venv
python3 -m venv .venv
. .venv/bin/activate
pip3 install -r requirements.txt
python3 -m PyInstaller --onefile --hidden-import="googleapiclient" --hidden-import="viam-wrap" src/main.py
tar -czvf dist/archive.tar.gz dist/main