from google.appengine.ext import db

class User(db.Model):
    created             = db.DateTimeProperty(auto_now_add=True)
    last_updated        = db.DateTimeProperty(auto_now=True)
    steam_username      = db.StringProperty(required=False)
    steam_show_spoilers = db.BooleanProperty(default=False)