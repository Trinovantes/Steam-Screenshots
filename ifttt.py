import webapp2
import json

#------------------------------------------------------------------------------
# Base ResponseHandler Class
#------------------------------------------------------------------------------

class JSONRequestHandler(webapp2.RequestHandler):
    def setResponseHeaders(self):
        self.response.headers['Content-Type'] = 'application/json'

    def setResponseAsUnsupported(self):
        error = {
            "errors": [
                { "message": "Unsupported endpoint" }
            ]
        }

        self.response.set_status(400)
        self.response.out.write(json.dumps(error))

    def get(self):
        self.setResponseHeaders();
        self.setResponseAsUnsupported();

    def post(self):
        self.setResponseHeaders();
        self.setResponseAsUnsupported();

#------------------------------------------------------------------------------
# Trigger
#------------------------------------------------------------------------------

class Trigger(JSONRequestHandler):
    steamUsername = None

#------------------------------------------------------------------------------
# Action
#------------------------------------------------------------------------------

class Action(JSONRequestHandler):
    pass

#------------------------------------------------------------------------------
# Server Status
#------------------------------------------------------------------------------

class Status(JSONRequestHandler):
    def get(self):
        self.setResponseHeaders();

#------------------------------------------------------------------------------
# Google App Engine
#------------------------------------------------------------------------------
  
application = webapp2.WSGIApplication([
    ('/ifttt/v1/triggers/.*', Trigger),
    ('/ifttt/v1/actions/.*', Action),
    ('/ifttt/v1/status', Status)
], debug = True)