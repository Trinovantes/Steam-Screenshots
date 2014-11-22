from google.appengine.api import urlfetch

import sys
sys.path.insert(0, 'libs') # Add /libs/ folder to $PATH
from bs4 import BeautifulSoup

import settings
import logging

#------------------------------------------------------------------------------

def get_profile_screenshot_url(username):
    return settings.steam_base_url + '/id/' + username + '/screenshots/'

def request_soup(url, use_mobile_user_agent=True):
    if use_mobile_user_agent:
        user_agent = settings.mobile_user_agent
    else:
        user_agent = settings.default_user_agent

    result = urlfetch.fetch(
        url,
        headers = {'User-Agent': user_agent}
    )

    if result.status_code == 200:
        return BeautifulSoup(result.content)
    else:
        logging.error('Received ' +  str(result.status_code) + ' error from ' + url)
        return None
