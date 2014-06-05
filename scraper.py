import os
import urllib2
import webapp2
import logging
import json
import urlparse
import datetime

# Enable loading from libs folder
import sys
sys.path.insert(0, 'libs')

from bs4 import BeautifulSoup
from google.appengine.ext import db
from models.user import User
from models.screenshot import Screenshot
import settings

#------------------------------------------------------------------------------
# Steam Scraper
#------------------------------------------------------------------------------

def request_soup(url):
    logging.debug("Getting soup of " + url)
    request  = urllib2.Request(url, '', {'User-Agent': settings.user_agent}) 
    htmlText = urllib2.urlopen(request).read()
    return BeautifulSoup(htmlText)

class SteamScraper:
    current_user  = None
    next_page_url = None

    def process(self, user):
        self.user    = user
        current_time = datetime.datetime.now()
        last_scraped = self.user.last_scraped

        if (current_time - last_scraped).seconds > settings.delay_seconds:
            next_page_url = settings.steam_base_url + '/id/' + self.user.steam_username + '/screenshots/'
            logging.debug("Starting to process \"" + user.steam_username + "\" last_scraped:" + last_scraped.strftime("%Y-%m-%d %H:%M:%S.%f"))
            while next_page_url is not None:
                self.process_list_page(next_page_url)

            return True
        else:
            logging.debug("Did not need to process \"" + user.steam_username + "\" last_scraped:" + last_scraped.strftime("%Y-%m-%d %H:%M:%S.%f"))
            return False

    def process_list_page(self, list_url):
        page_soup        = request_soup(list_url)
        screenshot_links = page_soup.find_all('a', class_='userScreenshotLink')

        # get next page's link
        next_page_arrow = page_soup.find('img', class_='pagingRightArrowImg')
        if next_page_arrow is None:
            next_page_url = None
        else:
            next_page_arrow.parent['href']

        # iterate over this page's screenshots
        for link in screenshot_links:
            screenshot_url = link['href']
            self.process_screenshot_page(screenshot_url)

    def process_screenshot_page(self, screenshot_url):
        page_soup  = request_soup(screenshot_url)
        parsed_url = urlparse.urlparse(screenshot_url)

        screenshot_src  = page_soup.find('img', class_='userScreenshotImg')['src']
        screenshot_desc = page_soup.find('a', class_='secondarynav_pageTitleHeader').string.strip()
        screenshot_game = page_soup.find(id='gameName').find('a', class_='itemLink').string.strip()

        s = Screenshot(
            owner         = self.user,
            screenshot_id = urlparse.parse_qs(parsed_url.query)['id'],
            url           = screenshot_url,
            src           = screenshot_src,
            desc          = screenshot_desc,
            game          = screenshot_game
        )
        result = s.put()
        if result is TransactionFailedError:
            logging.error("Failed to save screenshot for " + self.user.steam_username + " id:" + screenshot_id)
        else:
            logging.debug("Successfully saved screenshot for " + self.user.steam_username + " id:" + screenshot_id)

#------------------------------------------------------------------------------
# Google App Engine
#------------------------------------------------------------------------------

class ScraperHandler(webapp2.RequestHandler):
    def get(self):
        if settings.debug:
            users = [User(steam_username = "trinovantes")]
        else:
            users = User.all()

        logging.debug("Running scrapper on " + str(len(users)) + " users")

        for user in users:
            scraper = SteamScraper()
            scraper.process(user)


application = webapp2.WSGIApplication([(
    '/cron/scraper', ScraperHandler
)], debug = settings.debug)

if __name__ == '__main__':
    run_wsgi_app(application)