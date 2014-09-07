import os
import webapp2
import logging
import json
import urlparse
import datetime

from google.appengine.ext import db
from google.appengine.api import urlfetch
from google.appengine.api import taskqueue

import sys # Enable loading from libs folder
sys.path.insert(0, 'libs')
from bs4 import BeautifulSoup

from models.user import User
from models.screenshot import Screenshot
import settings

#------------------------------------------------------------------------------
# Steam Scraper
#------------------------------------------------------------------------------

def request_soup(url):
    logging.debug('Getting soup of ' + url)

    result = urlfetch.fetch(
        url,
        headers = {'User-Agent': settings.user_agent}
    )
    if result.status_code == 200:
        return BeautifulSoup(result.content)
    else:
        logging.error('Received ' +  str(result.status_code) + ' error from ' + url)
        return None      

class SteamScraper:
    user          = None
    base_url      = None
    next_page_url = None

    def __init__(self, user):
        self.user          = user
        self.base_url      = settings.steam_base_url + '/id/' + self.user.steam_username + '/screenshots/'
        self.next_page_url = self.base_url

    def fix_url(self, url):
        if 'http' not in url: # when debugging, the urls are relative instead of absolute
            url = self.base_url + url
        return url

    def finish_user(self):
        self.user.last_scraped = datetime.datetime.now()
        self.user.put()
        # clean up so we don't accidently do anything after user's last_scraped property is updated
        self.user          = None
        self.base_url      = None
        self.next_page_url = None

    def process(self):
        logging.info('Starting to process \'' + self.user.steam_username + '\' last_scraped:' + self.user.last_scraped.strftime('%Y-%m-%d %H:%M:%S.%f'))
        while self.next_page_url is not None:
            self.process_list_page(self.next_page_url)

        self.finish_user()

    def process_list_page(self, list_url):
        page_soup = request_soup(list_url)
        if page_soup is None:
            self.next_page_url = None
            return

        screenshot_links = page_soup.find_all('a', class_='userScreenshotLink')

        # get next page's link
        next_page_arrow = page_soup.find('img', class_='pagingRightArrowImg')
        if next_page_arrow is None:
            self.next_page_url = None
        else:
            self.next_page_url = self.fix_url(next_page_arrow.parent['href'])
            
        # iterate over this page's screenshots
        for link in screenshot_links: # TODO batch
            screenshot_url = self.fix_url(link['href'])
            self.process_screenshot_page(screenshot_url)

    def process_screenshot_page(self, screenshot_url):
        parsed_url = urlparse.urlparse(screenshot_url)
        screenshot_id   = urlparse.parse_qs(parsed_url.query)['id'][0]

        # first check if screenshot exists
        if Screenshot.all().filter('screenshot_id =', screenshot_id).get() is not None:
            return

        page_soup = request_soup(screenshot_url)
        if page_soup is None:
            return

        screenshot_src  = page_soup.find('img', class_='userScreenshotImg')['src']
        screenshot_desc = page_soup.find('a', class_='secondarynav_pageTitleHeader').string.strip()
        screenshot_game = page_soup.find(id='gameName').find('a', class_='itemLink').string.strip()

        s = Screenshot(
            owner         = self.user,
            screenshot_id = screenshot_id,
            url           = screenshot_url,
            src           = screenshot_src,
            desc          = screenshot_desc,
            game          = screenshot_game
        )
        result = s.put()
        if result is db.TransactionFailedError:
            logging.error('Failed to save screenshot for ' + self.user.steam_username + ' id:' + screenshot_id)
        else:
            logging.debug('Successfully saved screenshot for ' + self.user.steam_username + ' id:' + screenshot_id)

#------------------------------------------------------------------------------
# Google App Engine
#------------------------------------------------------------------------------

class ScraperTaskHandler(webapp2.RequestHandler):
    def post(self):
        steam_username = self.request.get('steam_username')
        user = User.all().filter('steam_username =', steam_username).get()
        scraper = SteamScraper(user)
        scraper.process()

class ScraperSchedulerHandler(webapp2.RequestHandler):
    def get(self):
        if settings.debug:
            test_user = User.all().filter('steam_username =', 'trinovantes').get()
            if test_user is None:
                test_user = User(steam_username = 'trinovantes')
                test_user.put()

            users = [test_user]
        else:
            more_than_a_day_ago = datetime.now() - timedelta(seconds=-settings.delay_seconds)
            users = User.all().query('last_scraped <', more_than_a_day_ago)

        if users is not None:
            logging.info('Scheduling scrapper on ' + str(len(users)) + ' user(s)')
            queue = taskqueue.Queue('scraper-queue')
            for user in users:
                queue.add(url='/scraper/run', params={'steam_username': user.steam_username})


application = webapp2.WSGIApplication([
    ('/scraper/run',       ScraperTaskHandler),
    ('/scraper/scheduler', ScraperSchedulerHandler)
], debug = settings.debug)

if __name__ == '__main__':
    run_wsgi_app(application)