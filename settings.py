import os

default_user_agent = 'Mozilla/5.0 (Linux; Steam Screenshots Bot)'
mobile_user_agent  = 'Mozilla/5.0 (Linux; Android 4.4.4; Steam Screenshots Bot) Mobile Safari'
steam_base_url     = 'http://steamcommunity.com'
delay_seconds      = 12 * 60 * 60

debug = 'development' in os.environ.get('SERVER_SOFTWARE', '').lower()
if (debug):
    steam_base_url = 'http://0.0.0.0:4000'
    delay_seconds  = 1
