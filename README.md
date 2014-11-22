Running Locally
---

```
{Path to Google App Engine}/dev_appserver.py --log_level debug .
```

Uploading to Server
---

```
{Path to Google App Engine}/appcfg.py --oauth2 update .
```

Running Local Tests
---
```
python test.py ~/bin/google_appengine/ tests/
```
