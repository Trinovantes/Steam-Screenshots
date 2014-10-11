from google.appengine.ext import db
from user import User

class Screenshot(db.Model):
    screenshot_id = db.StringProperty(required=True)
    scraped       = db.DateTimeProperty(auto_now_add=True)
    date_taken    = db.DateTimeProperty(required=True)
    url           = db.LinkProperty(required=True)
    src           = db.LinkProperty(required=True)
    desc          = db.StringProperty(required=False)
    game          = db.TextProperty(required=False)
    is_spoiler    = db.BooleanProperty(default=False)
    is_nsfw       = db.BooleanProperty(default=False)
    seen_already  = db.BooleanProperty(default=False)