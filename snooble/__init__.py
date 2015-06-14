import requests

from .oauth import OAuth


class Snooble(object):

    def __init__(self, useragent):
        self.useragent = useragent
        self._session = requests.Session()
        self._session.headers.update({"User-Agent": useragent})

    def oauth(self, oauth=None, **kwargs):
        if oauth is None:
            self.oauth(OAuth(**kwargs))

        self._oauth_details = oauth
