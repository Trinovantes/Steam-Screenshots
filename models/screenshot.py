from google.appengine.ext import db

class Screenshot(db.Model):
    def __init__(self, url, src, desc, game):
        self.url  = url
        self.src  = src
        self.desc = desc
        self.game = game