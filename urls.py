import webapp2

from controllers import settings
from controllers import ifttt
from controllers import scraper
from controllers import homepage

application = webapp2.WSGIApplication([
    ('/ifttt/v1/triggers/new_screenshot_uploaded',                       ifttt.ScreenshotTriggerHandler),
    ('/ifttt/v1/triggers/new_screenshot_uploaded/fields/(\w+)/validate', ifttt.ScreenshotTriggerFieldsValidationHandler),
    ('/ifttt/v1/test/setup',                                             ifttt.TestHandler),
    ('/ifttt/v1/actions/.*',                                             ifttt.ActionHandler),
    ('/ifttt/v1/status',                                                 ifttt.StatusHandler),

    ('/scraper/listing',    scraper.ListingScraperHandler),
    ('/scraper/screenshot', scraper.ScreenshotScraperHandler),
    ('/scraper/scheduler',  scraper.ScraperSchedulerHandler),

    ('/', homepage.MainPage)

], debug = settings.debug)

def main():
    run_wsgi_app(application)

if __name__ == "__main__":
    main()
