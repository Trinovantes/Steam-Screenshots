import webapp2
import unittest
import webtest

import urls
from controllers import ifttt
from controllers import private

class TriggerTestCase(unittest.TestCase):
    def setUp(self):
        self.testapp = webtest.TestApp(urls.application)

    def testStatusHandlerFail(self):
        response = self.testapp.get('/ifttt/v1/status', expect_errors=True)
        self.assertEqual(response.status_int, 401)
        self.assertEqual(response.content_type, 'application/json')

    def testStatusHandler(self):
        response = self.testapp.get('/ifttt/v1/status', headers={
            ifttt.HEADER_CHANNEL_KEY : private.IFTTT_CHANNEL_KEY
        })
        self.assertEqual(response.status_int, 200)
        self.assertEqual(response.content_type, 'application/json')

if __name__ == '__main__':
    unittest.main()
