httrack "http://steamcommunity.com/id/trinovantes/screenshots" \
    -O html/ \
    -g \
    -B \
    --depth=3 \
    -mime:* \
    +mime:text/html \
    -* \
    +http://steamcommunity.com/sharedfiles/filedetails/?id=* \
    +http://steamcommunity.com/id/trinovantes/screenshots* \
    -F "Mozilla/5.0 (Linux; Android 4.2; Nexus 4 Build/JVP15Q) Chrome/18.0.1025.166 Mobile Safari/535.19" 

ln html/screenshots.html html/index.html