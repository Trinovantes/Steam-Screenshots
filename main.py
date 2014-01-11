import sys
sys.path.insert(0, 'libs')
from bs4 import BeautifulSoup

import facebook
import os
import jinja2
import urllib2
import webapp2
import keys

from google.appengine.ext import db
from webapp2_extras import sessions


config = {}
config['webapp2_extras.sessions'] = dict(secret_key='')


class User(db.Model):
    id           = db.StringProperty(required=True)
    created      = db.DateTimeProperty(auto_now_add=True)
    updated      = db.DateTimeProperty(auto_now=True)
    name         = db.StringProperty(required=True)
    profile_url  = db.StringProperty(required=True)
    access_token = db.StringProperty(required=True)


class BaseHandler(webapp2.RequestHandler):
    @property
    def current_user(self):
        if self.session.get("user"):
            return self.session.get("user")
        else:
            cookie = facebook.get_user_from_cookie(self.request.cookies, keys.FB_APP_ID, keys.FB_APP_SECRET)
            if cookie:
                user = User.get_by_key_name(cookie["uid"])
                if not user:
                    graph = facebook.GraphAPI(cookie["access_token"])
                    profile = graph.get_object("me")
                    user = User(
                        key_name=str(profile["id"]),
                        id=str(profile["id"]),
                        name=profile["name"],
                        profile_url=profile["link"],
                        access_token=cookie["access_token"]
                    )
                    user.put()
                elif user.access_token != cookie["access_token"]:
                    user.access_token = cookie["access_token"]
                    user.put()

                self.session["user"] = dict(
                    name         =user.name,
                    profile_url  =user.profile_url,
                    id           =user.id,
                    access_token =user.access_token
                )
                return self.session.get("user")

        return None

    def dispatch(self):
        self.session_store = sessions.get_store(request=self.request)
        try:
            webapp2.RequestHandler.dispatch(self)
        finally:
            self.session_store.save_sessions(self.response)

    @webapp2.cached_property
    def session(self):
        return self.session_store.get_session()


class HomeHandler(BaseHandler):
    def get(self):
        template = jinja_environment.get_template('index.html')
        self.response.out.write(template.render(dict(
            facebook_app_id = keys.FB_APP_ID,
            current_user    = self.current_user
        )))

    def post(self):
        url       = self.request.get('url')
        file      = urllib2.urlopen(url)
        graph     = facebook.GraphAPI(self.current_user['access_token'])
        response  = graph.put_photo(file, "Test Image")
        photo_url = ("http://www.facebook.com/photo.php?fbid={0}".format(response['id']))
        self.redirect(str(photo_url))


class LogoutHandler(BaseHandler):
    def get(self):
        if self.current_user is not None:
            self.session['user'] = None
        self.redirect('/')


jinja_environment = jinja2.Environment(
    loader=jinja2.FileSystemLoader(os.path.join(os.path.dirname(__file__), 'views')),
    extensions=['jinja2.ext.autoescape'],
    autoescape=True)

application = webapp2.WSGIApplication([('/', HomeHandler),], debug=True, config=config)