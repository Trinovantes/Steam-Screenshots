debug             = True
user_agent        = "Mozilla/5.0 (Linux; Android 4.2; Nexus 4 Build/JVP15Q) AppleWebKit/535.19 (KHTML, like Gecko) Chrome/18.0.1025.166 Mobile Safari/535.19"
steam_base_url    = "http://steamcommunity.com"
steam_page_marker = "?p="

if (debug):
    steam_base_url    = "http://0.0.0.0:4000"
    steam_page_marker = "page"