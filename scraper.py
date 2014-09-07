import os
import webapp2
import logging
import json
import urlparse
import time
from datetime import timedelta
from datetime import datetime
from google.appengine.ext import db
from google.appengine.api import taskqueue

from models.user import User
from models.screenshot import Screenshot
import settings
import helpers

#------------------------------------------------------------------------------
# Globals
#------------------------------------------------------------------------------

TEST_USERNAME             = 'trinovantes'
HEADER_STEAM_USERNAME_KEY = 'steam_username'
HEADER_NEXT_PAGE_KEY      = 'current_page_url'

listing_queue    = taskqueue.Queue('listing-queue')
screenshot_queue = taskqueue.Queue('screenshot-queue')

#------------------------------------------------------------------------------
# Listing Scraper
#------------------------------------------------------------------------------

class ListingScraper:
    user = None

    def __init__(self, username):
        self.user = User.all().filter('steam_username =', username).get()

    def fix_url(self, url):
        if 'http' not in url: # When debugging, the urls are relative instead of absolute
            url = helpers.get_profile_screenshot_url(self.user.steam_username) + url
        return url

    def run(self, current_page_url):
        if self.user is None:
            logging.warning('Attempting to get listing for an empty user')
            return

        logging.info('Processing \'' + current_page_url + '\' steam_username:' + self.user.steam_username + ' last_scraped:' + self.user.last_scraped.strftime('%Y-%m-%d %H:%M:%S.%f'))
        page_soup = helpers.request_soup(current_page_url)

        # Check if we got 200 from Steam
        if page_soup is None:
            return
        
        # Iterate over this page's screenshots
        screenshot_links = page_soup.find_all('a', class_='userScreenshotLink')
        for link in screenshot_links:
            screenshot_queue.add(taskqueue.Task(
                url = '/scraper/screenshot',
                params = {
                    HEADER_STEAM_USERNAME_KEY:  self.user.steam_username,
                    HEADER_NEXT_PAGE_KEY:       self.fix_url(link['href'])
                }
            ))

        # Queue up next page or update the user's last_scraped time
        next_page_arrow = page_soup.find('img', class_='pagingRightArrowImg')
        if next_page_arrow is None:
            self.user.put()
            self.user = None # cleanup
        else:
            listing_queue.add(taskqueue.Task(
                url = '/scraper/listing', 
                params = {
                    HEADER_STEAM_USERNAME_KEY:  self.user.steam_username,
                    HEADER_NEXT_PAGE_KEY:       self.fix_url(next_page_arrow.parent['href'])
                }
            ))

class ListingScraperHandler(webapp2.RequestHandler):
    def post(self):
        username = self.request.get(HEADER_STEAM_USERNAME_KEY)
        next_page_url = self.request.get(HEADER_NEXT_PAGE_KEY)

        # If this task is queued up by the scheduler, then use the base url
        if not next_page_url:
            next_page_url = helpers.get_profile_screenshot_url(username)

        scraper = ListingScraper(username)
        scraper.run(next_page_url)

#------------------------------------------------------------------------------
# Screenshot Scraper
#------------------------------------------------------------------------------

class ScreenshotScraper:
    user = None

    def __init__(self, username):
        self.user = User.all().filter('steam_username =', username).get()

    def run(self, screenshot_page_url):
        if self.user is None:
            logging.warning('Attempting to get screenshot for an empty user')
            return

        # First check if screenshot exists in db already
        parsed_url = urlparse.urlparse(screenshot_page_url)
        screenshot_id = urlparse.parse_qs(parsed_url.query)['id'][0]
        if Screenshot.all().filter('screenshot_id =', screenshot_id).get() is not None:
            return

        # Then check if we got 200 from Steam
        page_soup = helpers.request_soup(screenshot_page_url)
        if page_soup is None:
            return

        screenshot_creation_date = page_soup.find(id='dateTaken').find_all('span')[1].string.strip()
        screenshot_creation_date = datetime.strptime(screenshot_creation_date, '%b %d, %Y @ %I:%M%p')

        #TODO Check for spoiler tag
        #TODO Check for NSFW text in desc

        screenshot_src  = page_soup.find('img', class_='userScreenshotImg')['src']
        screenshot_desc = page_soup.find('a', class_='secondarynav_pageTitleHeader').string.strip()
        screenshot_game = page_soup.find(id='gameName').find('a', class_='itemLink').string.strip()
        
        s = Screenshot(
            parent        = self.user,
            screenshot_id = screenshot_id,
            date_taken    = screenshot_creation_date,
            url           = screenshot_page_url,
            src           = screenshot_src,
            desc          = screenshot_desc,
            game          = screenshot_game
        )
        result = s.put()
        if result is db.TransactionFailedError:
            logging.error('Failed to save screenshot for ' + self.user.steam_username + ' id:' + screenshot_id)
        else:
            logging.debug('Successfully saved screenshot for ' + self.user.steam_username + ' id:' + screenshot_id)

class ScreenshotScraperHandler(webapp2.RequestHandler):
    def post(self):
        username = self.request.get(HEADER_STEAM_USERNAME_KEY)
        next_page_url = self.request.get(HEADER_NEXT_PAGE_KEY)
        scraper = ScreenshotScraper(username)
        scraper.run(next_page_url)

#------------------------------------------------------------------------------
# Scheduler
#------------------------------------------------------------------------------

class ScraperSchedulerHandler(webapp2.RequestHandler):
    def get(self):
        if settings.debug:
            test_user = User.all().filter('steam_username =', TEST_USERNAME).get()
            if test_user is None:
                test_user = User(steam_username=TEST_USERNAME)
                test_user.put()
            users = [test_user]
        else:
            more_than_a_day_ago = datetime.now() - timedelta(seconds=-settings.delay_seconds)
            users = User.all().filter('last_scraped <', more_than_a_day_ago).fetch(None)

        if users is not None:
            logging.info('Scheduling scrapper on ' + str(len(users)) + ' user(s)')
            for user in users:
                listing_queue.add(taskqueue.Task(
                    url = '/scraper/listing', 
                    params = {
                        HEADER_STEAM_USERNAME_KEY: user.steam_username
                    }
                ))


application = webapp2.WSGIApplication([
    ('/scraper/listing',    ListingScraperHandler),
    ('/scraper/screenshot', ScreenshotScraperHandler),
    ('/scraper/scheduler',  ScraperSchedulerHandler)
], debug = settings.debug)

if __name__ == '__main__':
    run_wsgi_app(application)