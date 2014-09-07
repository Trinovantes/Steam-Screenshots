import webapp2
import logging
import json

from google.appengine.ext import db
from google.appengine.api import urlfetch

from models.user import User
from models.screenshot import Screenshot
import settings
import helpers
import private

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
        self.response.headers['Content-Type'] = 'application/json'
        self.response.set_status(200)

    def checkChannelKey(self):
        if 'IFTTT-Channel-Key' not in self.request.headers:
            raise InvalidChannelKeyException()

        channel_key = self.request.headers['IFTTT-Channel-Key']
        if channel_key != private.ifttt_channel_key:
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
            logging.warning(exception.message + ' request received from ' + self.request.remote_addr)
        else:
            webapp2.RequestHandler.handle_exception(self, exception, debug_mode)

#------------------------------------------------------------------------------
# Trigger
#------------------------------------------------------------------------------

class TriggerHandler(JSONRequestHandler):
    steam_username = None
    show_spoilers  = False

    def parseTriggerFields(self):
        if 'triggerFields' not in self.request.headers:
            raise InvalidTriggerFieldsException()

        triggerFields = self.request.headers['triggerFields']
        if not triggerFields:
            raise InvalidTriggerFieldsException()

        self.steam_username = triggerFields['steam_username']
        show_spoilers       = triggerFields['show_spoilers']

    def post(self):
        checkChannelKey()
        parseTriggerFields()
        createNewUserIfNotExist()

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

class TriggerFieldsValidationHandler(JSONRequestHandler):
    def getBodyValue(self):
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
                        'message': username + ' does not exist on Steam'
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
        checkChannelKey()

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

#------------------------------------------------------------------------------
# Google App Engine
#------------------------------------------------------------------------------
  
application = webapp2.WSGIApplication([
    ('/ifttt/v1/triggers/new_screenshot_uploaded', TriggerHandler),
    ('/ifttt/v1/triggers/new_screenshot_uploaded/fields/(\w+)/validate', TriggerFieldsValidationHandler),
    ('/ifttt/v1/test/setup', TestHandler),
    ('/ifttt/v1/actions/.*', ActionHandler),
    ('/ifttt/v1/status', StatusHandler)
], debug = True)