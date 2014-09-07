from google.appengine.ext import db
from user import User

class Screenshot(db.Model):
    screenshot_id    = db.StringProperty(required=True)
    created          = db.DateTimeProperty(auto_now_add=True)
    url              = db.LinkProperty(required=True)
    src              = db.LinkProperty(required=True)
    desc             = db.StringProperty(required=False)
    game             = db.TextProperty(required=False)
    contains_spolier = db.BooleanProperty(default=False)
    seen_already     = db.BooleanProperty(default=False)