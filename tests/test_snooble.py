import snooble

import pytest
import responses
import json
from base64 import b64encode
from unittest import mock


class TestSnooble(object):

    def test_initialisation(self):
        snoo = snooble.Snooble('my-test-useragent')
        assert snoo.useragent == 'my-test-useragent'
        assert snoo._limiter == snooble.ratelimit.RateLimiter(60, 60, False)
        assert snoo._authorized is False
        assert snoo.domain.www == snooble.WWW_DOMAIN
        assert snoo.domain.auth == snooble.AUTH_DOMAIN

        snoo.www_domain = 'http://my-fake-reddit.com'
        snoo.auth_domain = 'http://oauth.my-fake-reddit.com'

        assert snoo.domain.www == 'http://my-fake-reddit.com'
        assert snoo.domain.auth == 'http://oauth.my-fake-reddit.com'

        with pytest.raises(snooble.errors.SnoobleError):
            snoo.get('/url')

    @responses.activate
    def test_oauth_as_script_successful(self, monkeypatch):
        time_mock = mock.Mock(return_value=1234567890)
        monkeypatch.setattr('time.time', time_mock)

        responses.add(responses.POST, 'https://www.reddit.com/api/v1/access_token',
                      body=json.dumps({'access_token': 'fhTdafZI-0ClEzzYORfBSCR7x3M',
                                       'expires_in': 3600,
                                       'scope': '*',
                                       'token_type': 'bearer'}),
                      content_type='application/json')

        snoo = snooble.Snooble('my-test-useragent')
        snoo.oauth(snooble.oauth.SCRIPT_KIND, scopes=['read'],
                   client_id='ThisIsTheClientID', secret_id='ThisIsTheSecretID',
                   username='my-username', password='my-password')

        assert len(responses.calls) == 1
        response = responses.calls[0].request
        assert response.headers['User-Agent'] == 'my-test-useragent'
        assert response.headers['Authorization'] == \
               'Basic ' + b64encode(b'ThisIsTheClientID:ThisIsTheSecretID').decode('utf-8')
        assert 'grant_type=password' in response.body
        assert 'username=my-username' in response.body
        assert 'password=my-password' in response.body

        assert snoo._authorized is True
        assert snoo.authorization == \
            snooble.oauth.Authorization(token_type='bearer', recieved=1234567890,
                                        length=3600, token='fhTdafZI-0ClEzzYORfBSCR7x3M')

    def test_oauth_as_script_failing(self):
        with responses.RequestsMock() as rsps:
            rsps.add(responses.POST, 'https://www.reddit.com/api/v1/access_token',
                          body=json.dumps({'error': 401}), status=401)

            snoo = snooble.Snooble('my-test-useragent')

            with pytest.raises(snooble.errors.RedditError):
                snoo.oauth(snooble.oauth.SCRIPT_KIND, scopes=['read'],
                           client_id='ThisIsTheClientID', secret_id='ThisIsTheSecretID',
                           username='my-username', password='my-password')

            assert snoo.authorization is None
            assert snoo._authorized is False

        with responses.RequestsMock() as rsps:
            rsps.add(responses.POST, 'https://www.reddit.com/api/v1/access_token',
                          body=json.dumps({'error': 404}), status=404)

            snoo = snooble.Snooble('my-test-useragent')

            with pytest.raises(snooble.errors.RedditError):
                snoo.oauth(snooble.oauth.SCRIPT_KIND, scopes=['read'],
                           client_id='ThisIsTheClientID', secret_id='ThisIsTheSecretID',
                           username='my-username', password='my-password')

            assert snoo.authorization is None
            assert snoo._authorized is False
