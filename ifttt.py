import webapp2
import logging
import json

from google.appengine.ext import db

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

class InvalidTriggerFieldException(IFTTTException):
    def __init__(self):
        self.code    = 400
        self.message = 'Invalid triggerFields'

#------------------------------------------------------------------------------
# Base ResponseHandler Class
#------------------------------------------------------------------------------

class JSONRequestHandler(webapp2.RequestHandler):
    def setResponseHeaders(self):
        self.response.headers['Content-Type'] = 'application/json'

    def checkChannelKey(self):
        channel_key = self.request.headers['IFTTT-Channel-Key']
        if channel_key != private.ifttt_channel_key:
            logging.warning('Received request invalid channel key from ' + self.request.remote_addr)
            raise InvalidChannelKeyException()

    def get(self):
        self.checkChannelKey()
        raise UnsupportedEndpointException()

    def post(self):
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
        else:
            webapp2.RequestHandler.handle_exception(self, exception, debug_mode)

#------------------------------------------------------------------------------
# Trigger
#------------------------------------------------------------------------------

class Trigger(JSONRequestHandler):
    steamUsername = None

    def parseTriggerFields(self):
        if 'triggerFields' not in self.request.headers:
            raise InvalidTriggerFieldException()

        triggerFields = self.request.headers['triggerFields']
        if not triggerFields:
            raise InvalidTriggerFieldException()

        self.steamUsername = triggerFields['steam_username']

    def createNewUserIfNotExist(self):
        pass

    def post(self):
        checkChannelKey()
        parseTriggerFields()
        createNewUserIfNotExist()

#------------------------------------------------------------------------------
# Validation
#------------------------------------------------------------------------------

class ValidateTriggerFields(JSONRequestHandler):
    def post(self):
        pass

#------------------------------------------------------------------------------
# Test
#------------------------------------------------------------------------------

class Test(JSONRequestHandler):
    def post(self):
        checkChannelKey()

#------------------------------------------------------------------------------
# Action (unsupported)
#------------------------------------------------------------------------------

class Action(JSONRequestHandler):
    pass

#------------------------------------------------------------------------------
# Server Status
#------------------------------------------------------------------------------

class Status(JSONRequestHandler):
    def get(self):
        self.checkChannelKey()
        self.setResponseHeaders()

#------------------------------------------------------------------------------
# Google App Engine
#------------------------------------------------------------------------------
  
application = webapp2.WSGIApplication([
    ('/ifttt/v1/test/setup', Test),
    ('/ifttt/v1/triggers/new_screenshot_uploaded', Trigger),
    ('/ifttt/v1/triggers/new_screenshot_uploaded/fields/(\w+])/validate', ValidateTriggerFields),
    ('/ifttt/v1/actions/.*', Action),
    ('/ifttt/v1/status', Status)
], debug = True)