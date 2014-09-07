debug              = False
default_user_agent = 'Mozilla/5.0 (Linux; Steam Screenshots Bot)'
mobile_user_agent  = 'Mozilla/5.0 (Linux; Android 4.4.4; Steam Screenshots Bot) Mobile Safari'
steam_base_url     = 'http://steamcommunity.com'
delay_seconds      = 12 * 60 * 60

if (debug):
    steam_base_url = 'http://0.0.0.0:4000'
    delay_seconds  = 1