Running Locally
===

Assuming the Google App Engine SDK is installed into `~/bin/google_appengine/`

```
~/bin/google_appengine/dev_appserver.py --log_level debug .
```

Uploading to Server
---

```
~/bin/google_appengine/appcfg.py --oauth2 update .
```

Running Unit Tests
---
```
python test.py ~/bin/google_appengine/ tests/
```
