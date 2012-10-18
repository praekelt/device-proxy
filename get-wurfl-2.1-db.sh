#!/bin/bash
wget -c "http://mirror.transact.net.au/pub/sourceforge/w/project/wu/wurfl/WURFL/2.1.1/wurfl-2.1.zip"
unzip -o "wurfl-2.1.zip" "wurfl.xml"
wurfl2python.py -o "devproxy/handlers/wurfl_handler/wurfl_devices.py" "wurfl.xml"