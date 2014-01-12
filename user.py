from google.appengine.ext import db

class User(db.Model):
    id                  = db.StringProperty(required=True)
    created             = db.DateTimeProperty(auto_now_add=True)
    updated             = db.DateTimeProperty(auto_now=True)
    name                = db.StringProperty(required=True)
    profile_url         = db.StringProperty(required=True)
    access_token        = db.StringProperty(required=True)
    steam_username      = db.StringProperty(required=False)
    steam_show_spoilers = db.BooleanProperty(default=False)
    last_scraped        = db.DateTimeProperty(auto_now=True)