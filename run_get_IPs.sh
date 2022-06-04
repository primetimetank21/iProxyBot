#!/bin/bash
rm -rf ip_env
python3 -m venv ip_env
. ip_env/bin/activate
pip install -r requirements.txt 1>/dev/null 2>/dev/null
python3 get_IPs.py
deactivate
