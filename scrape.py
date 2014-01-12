import sys
sys.path.insert(0, 'libs')

import keys
import facebook
import os
import urllib
import urllib2
import webapp2
import datetime
import logging
import json

from bs4 import BeautifulSoup
from google.appengine.ext import db
from user import User


class Screenshot():
    def __init__(self, url, src, desc, game):
        self.url  = url
        self.src  = src
        self.desc = desc
        self.game = game


class SteamScraper():
    USER_AGENT  = "Mozilla/5.0 (Linux; Android 4.2; Nexus 4 Build/JVP15Q) AppleWebKit/535.19 (KHTML, like Gecko) Chrome/18.0.1025.166 Mobile Safari/535.19"
    screenshots = []
    user        = None
    handler     = None

    def getNewScreenshots(self):
        current_time = datetime.datetime.now()
        last_scraped = self.user.last_scraped

        if (True):
        #if ((current_time - last_scraped).days > 1):
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

                self.screenshots.append(Screenshot(screenshot_url, screenshot_src, screenshot_desc, screenshot_game))

        return

    def postToFacebook(self):
        graph = facebook.GraphAPI(self.user.access_token)

        #screenshot = Screenshot(
        #    "http://steamcommunity.com/sharedfiles/filedetails/?id=208701145",
        #    "http://cloud-4.steampowered.com/ugc/468671739299466501/A842DBBE22E5790870D31C30613707A16F06CA49/",
        #    "Yay another dragon",
        #    "Dragon Age: Origins - Ultimate Edition"
        #)
        #screenshots.append(screenshots)

        for screenshot in self.screenshots:
            logging.info(screenshot.game)
            logging.info(screenshot.url)
            logging.info(screenshot.src)
            logging.info(screenshot.desc)

            params = dict(
                method = "POST",
                object = dict(
                    app_id      = keys.FB_APP_ID,
                    type        = "steamscreenshots:screenshot",
                    title       = screenshot.game + " Screenshot",
                    url         = screenshot.url,
                    image       = screenshot.src,
                    description = screenshot.desc
                )
            )

            #res = graph.request("me/objects/steamscreenshots:screenshot", args=params)
            #logging.info(res['id'])

            #res = graph.request("me/objects/steamscreenshots:upload", args=dict(screenshot=res['id']))
            #logging.info(res)

        return

    def process(self, handler, user):
        self.user    = user
        self.handler = handler
        self.getNewScreenshots()
        self.postToFacebook()
        return
        

class ScrapeSteamHandler(webapp2.RequestHandler):
    def get(self):
        self.response.headers['Content-Type'] = 'text/plain'

        users = User.all()
        for user in users:
            SteamScraper().process(self, user)


application = webapp2.WSGIApplication([('/cron/scrape', ScrapeSteamHandler)], debug=True)

if __name__ == '__main__':
    run_wsgi_app(application)