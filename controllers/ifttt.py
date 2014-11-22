import webapp2
import logging
import json
from datetime import datetime
from google.appengine.ext import db
from google.appengine.api import urlfetch

from models.user import User
from models.screenshot import Screenshot
import settings
import helpers
import private

#------------------------------------------------------------------------------
# Globals
#------------------------------------------------------------------------------

HEADER_CHANNEL_KEY = 'IFTTT-Channel-Key'

IFTTT_TRIGGER_FIELD_USERNAME_KEY      = 'steam_username'
IFTTT_TRIGGER_FIELD_SHOW_SPOILERS_KEY = 'show_spoilers'
IFTTT_TRIGGER_FIELD_SHOW_NSFW_KEY     = 'show_nsfw'

IFTTT_INGREDIENT_SCREENSHOT_PAGE_KEY     = 'screenshot_page'
IFTTT_INGREDIENT_SCREENSHOT_URL_KEY      = 'screenshot_url'
IFTTT_INGREDIENT_SCREENSHOT_CAPTION_KEY  = 'screenshot_caption'
IFTTT_INGREDIENT_SCREENSHOT_USERNAME_KEY = 'steam_username'
IFTTT_INGREDIENT_SCREENSHOT_GAME_KEY     = 'game'
IFTTT_INGREDIENT_META_LABEL_KEY     = 'meta'
IFTTT_INGREDIENT_META_ID_KEY        = 'id'
IFTTT_INGREDIENT_META_TIMESTAMP_KEY = 'timestamp'

IFTTT_PARAM_TRIGGERFIELDS_KEY = 'triggerFields'
IFTTT_PARAM_LIMIT_KEY         = 'limit'
IFTTT_DEFAULT_TRIGGER_LIMIT   = 50

#------------------------------------------------------------------------------
# Exception Classes
#------------------------------------------------------------------------------

class IFTTTException(Exception):
    pass

class UnsupportedEndpointException(IFTTTException):
    def __init__(self):
        self.code    = 400
        self.message = 'Unsupported endpoint'

class InvalidChannelKeyException(IFTTTException):
    def __init__(self):
        self.code    = 401
        self.message = 'Invalid Channel Key'

class InvalidTriggerFieldsException(IFTTTException):
    def __init__(self):
        self.code    = 400
        self.message = 'Invalid triggerFields'

#------------------------------------------------------------------------------
# Base ResponseHandler Class
#------------------------------------------------------------------------------

class JSONRequestHandler(webapp2.RequestHandler):
    def setResponseHeaders(self):
        self.response.headers['Content-Type'] = 'application/json; charset=utf-8'
        self.response.set_status(200)

    def checkChannelKey(self):
        if 'IFTTT-Channel-Key' not in self.request.headers:
            raise InvalidChannelKeyException()

        channel_key = self.request.headers[HEADER_CHANNEL_KEY]
        if channel_key != private.IFTTT_CHANNEL_KEY:
            raise InvalidChannelKeyException()

    def get(self, *params):
        self.checkChannelKey()
        raise UnsupportedEndpointException()

    def post(self, *params):
        self.checkChannelKey()
        raise UnsupportedEndpointException()

    def handle_exception(self, exception, debug_mode):
        if isinstance(exception, IFTTTException):
            error = {
                'errors': [
                    { 'message': exception.message }
                ]
            }
            self.setResponseHeaders()
            self.response.set_status(exception.code)
            self.response.out.write(json.dumps(error))
            logging.warning(exception.message + ' request received from ' + str(self.request.remote_addr))
        else:
            # Default handler
            webapp2.RequestHandler.handle_exception(self, exception, debug_mode)

#------------------------------------------------------------------------------
# Trigger
#------------------------------------------------------------------------------

class ScreenshotTriggerHandler(JSONRequestHandler):
    user  = None
    limit = IFTTT_DEFAULT_TRIGGER_LIMIT

    def parseTriggerFields(self):
        if not self.request.body:
            raise InvalidTriggerFieldsException()

        body = json.loads(self.request.body)
        if IFTTT_PARAM_TRIGGERFIELDS_KEY not in body:
            raise InvalidTriggerFieldsException()

        triggerFields = body[IFTTT_PARAM_TRIGGERFIELDS_KEY]
        if not triggerFields or \
        IFTTT_TRIGGER_FIELD_SHOW_SPOILERS_KEY not in triggerFields or \
        IFTTT_TRIGGER_FIELD_SHOW_NSFW_KEY not in triggerFields:
            raise InvalidTriggerFieldsException()

        username      = triggerFields[IFTTT_TRIGGER_FIELD_USERNAME_KEY]
        show_spoilers = ('yes' == triggerFields[IFTTT_TRIGGER_FIELD_SHOW_SPOILERS_KEY])
        show_nsfw     = ('yes' == triggerFields[IFTTT_TRIGGER_FIELD_SHOW_NSFW_KEY])

        # Create user if it doesn't already exist
        self.user = User.all().filter('steam_username =', username).get()
        if self.user is None:
            if is_valid_username(username):
                self.user = User(
                    steam_username      = username,
                    steam_show_spoilers = show_spoilers,
                    steam_show_nsfw     = show_nsfw
                )
                self.user.put()
            else:
                raise InvalidTriggerFieldsException()

    def parseLimit(self):
        body = json.loads(self.request.body)
        if IFTTT_PARAM_LIMIT_KEY in body:
            self.limit = int(body[IFTTT_PARAM_LIMIT_KEY])

    def post(self):
        self.checkChannelKey()
        self.parseTriggerFields()
        self.parseLimit()

        screenshots_query = Screenshot.all()
        screenshots_query.ancestor(self.user)
        screenshots_query.filter('seen_already =', False)
        if not self.user.steam_show_spoilers:
            screenshots_query.filter('is_spoiler =', False)
        if not self.user.steam_show_nsfw:
            screenshots_query.filter('is_nsfw =', False)

        screenshots     = screenshots_query.fetch(self.limit)
        screenshot_data = []
        for screenshot in screenshots:
            screenshot_data.append({
                IFTTT_INGREDIENT_SCREENSHOT_PAGE_KEY:       screenshot.url,
                IFTTT_INGREDIENT_SCREENSHOT_URL_KEY:        screenshot.src,
                IFTTT_INGREDIENT_SCREENSHOT_CAPTION_KEY:    screenshot.desc,
                IFTTT_INGREDIENT_SCREENSHOT_USERNAME_KEY:   self.user.steam_username,
                IFTTT_INGREDIENT_SCREENSHOT_GAME_KEY:       screenshot.game,
                IFTTT_INGREDIENT_META_LABEL_KEY: {
                    IFTTT_INGREDIENT_META_ID_KEY:           screenshot.screenshot_id,
                    IFTTT_INGREDIENT_META_TIMESTAMP_KEY:    int((screenshot.scraped - datetime(1970, 1, 1)).total_seconds())
                }
            })
            screenshot.seen_already = True

        # Save the seen_already flags
        db.put(screenshots)


        self.setResponseHeaders()
        self.response.out.write(json.dumps({
            # Sort by timestsamp because apparently the db query isn't sorted by scraped date
            'data': sorted(screenshot_data, reverse=True, key=lambda k: k[IFTTT_INGREDIENT_META_LABEL_KEY][IFTTT_INGREDIENT_META_TIMESTAMP_KEY])
        }))

#------------------------------------------------------------------------------
# Validation
#------------------------------------------------------------------------------

def is_valid_username(username):
    if not username:
        return False

    # First check if it's an existing user in the db
    if User.all().filter('steam_username =', username).get() is not None:
        return True

    # Then check if their Steam profile is valid
    url = helpers.get_profile_screenshot_url(username)
    page_soup = helpers.request_soup(url, False)
    return page_soup is not None and 'Error' not in page_soup.find('title').string

class ScreenshotTriggerFieldsValidationHandler(JSONRequestHandler):
    def getBodyValue(self):
        if not self.request.body:
            return None

        body = json.loads(self.request.body)
        if 'value' in body:
            return body['value']
        else:
            return None

    def post(self, trigger_field):
        if trigger_field == 'steam_username':
            self.checkChannelKey()
            self.setResponseHeaders()

            username = self.getBodyValue()
            if is_valid_username(username):
                output = {
                    'data':  {
                        'valid': True
                    }
                }
            else:
                output = {
                    'data':  {
                        'valid': False,
                        'message': str(username) + ' does not exist on Steam'
                    }
                }

            self.response.out.write(json.dumps(output))
        else:
            raise UnsupportedEndpointException()

#------------------------------------------------------------------------------
# Test
#------------------------------------------------------------------------------

class TestHandler(JSONRequestHandler):
    def post(self):
        self.checkChannelKey()
        self.setResponseHeaders()

        test_data = {
            'samples': {
                'triggers': {
                    'new_screenshot_uploaded': {
                        IFTTT_TRIGGER_FIELD_USERNAME_KEY: 'trinovantes',
                        IFTTT_TRIGGER_FIELD_SHOW_SPOILERS_KEY: 'no',
                        IFTTT_TRIGGER_FIELD_SHOW_NSFW_KEY: 'no'
                    }
                },
                'triggerFieldValidations': {
                    'new_screenshot_uploaded': {
                        'steam_username': {
                            'valid': 'trinovantes',
                            'invalid': 'trinoventes'
                        }
                    }
                }
            }
        }
        self.response.out.write(json.dumps({'data': test_data}))

#------------------------------------------------------------------------------
# Action (unsupported)
#------------------------------------------------------------------------------

class ActionHandler(JSONRequestHandler):
    pass

#------------------------------------------------------------------------------
# Server Status
#------------------------------------------------------------------------------

class StatusHandler(JSONRequestHandler):
    def get(self):
        self.checkChannelKey()
        self.setResponseHeaders()
