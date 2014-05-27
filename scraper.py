import os
import urllib2
import webapp2
import datetime
import logging
import json

# Enable loading from libs folder
import sys
sys.path.insert(0, 'libs')

from bs4 import BeautifulSoup
from google.appengine.ext import db
from models.user import User
from models.screenshot import Screenshot

#------------------------------------------------------------------------------
# Steam Scraper
#------------------------------------------------------------------------------

class SteamScraper():
    USER_AGENT  = "Mozilla/5.0 (Linux; Android 4.2; Nexus 4 Build/JVP15Q) AppleWebKit/535.19 (KHTML, like Gecko) Chrome/18.0.1025.166 Mobile Safari/535.19"
    screenshots = []
    user        = None

    def getNewScreenshots(self):
        current_time = datetime.datetime.now()
        last_scraped = self.user.last_scraped

        if ((current_time - last_scraped).days > 1):
            url              = "http://steamcommunity.com/id/" + self.user.steam_username + "/screenshots/"
            request          = urllib2.Request(url, '', {'User-Agent': self.USER_AGENT}) 
            htmlText         = urllib2.urlopen(request).read()
            soup             = BeautifulSoup(htmlText)
            screenshot_pages = soup.find_all('a', class_='userScreenshotLink')

            for page in screenshot_pages:
                url      = page['href'];
                request  = urllib2.Request(url, '', {'User-Agent': self.USER_AGENT}) 
                htmlText = urllib2.urlopen(request).read()
                soup     = BeautifulSoup(htmlText)

                screenshot_url  = url
                screenshot_src  = soup.find('img', class_='userScreenshotImg')['src']
                screenshot_desc = soup.find('a', class_='secondarynav_pageTitleHeader').string.strip()
                screenshot_game = soup.find(id='gameName').find('a', class_='itemLink').string.strip()

                screenshots.append(Screenshot(screenshot_url, screenshot_src, screenshot_desc, screenshot_game))
                return True # TODO
        else:
            return False
        

    def process(self, user):
        self.user = user
        getNewScreenshots()
        return

#------------------------------------------------------------------------------
# Google App Engine
#------------------------------------------------------------------------------

class ScraperHandler(webapp2.RequestHandler):
    def get(self):
        users = User.all()
        for user in users:
            SteamScraper().process(user)


application = webapp2.WSGIApplication([(
    '/cron/scraper', ScraperHandler
)], debug=True)

if __name__ == '__main__':
    run_wsgi_app(application)