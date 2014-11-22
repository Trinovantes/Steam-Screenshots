#!/bin/bash

mkdir -p html

httrack "http://steamcommunity.com/id/trinovantes/screenshots" \
    -O html/ \
    -B \
    --get-files \
    --depth=3 \
    --verbose \
    --extra-log \
    -F "Mozilla/5.0 (Linux; Android 4.4.4; Steam Screenshots Bot) Mobile Safari" \
    +http://steamcommunity.com/id/trinovantes/screenshots* \
    +http://steamcommunity.com/sharedfiles/filedetails/?id=*

ln -f html/screenshots.html html/index.html
