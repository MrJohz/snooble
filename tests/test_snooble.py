import snooble

import pytest
import responses
import json
from base64 import b64encode
from unittest import mock
from urllib.parse import quote_plus


class TestSnooble(object):

    def test_initialisation(self):
        snoo = snooble.Snooble('my-test-useragent')
        assert snoo.useragent == 'my-test-useragent'
        assert snoo._limiter == snooble.ratelimit.RateLimiter(60, 60, False)
        assert snoo.authorized is False
        assert snoo.domain.www == snooble.WWW_DOMAIN
        assert snoo.domain.auth == snooble.AUTH_DOMAIN

        snoo.www_domain = 'http://my-fake-reddit.com'
        snoo.auth_domain = 'http://oauth.my-fake-reddit.com'

        assert snoo.domain.www == 'http://my-fake-reddit.com'
        assert snoo.domain.auth == 'http://oauth.my-fake-reddit.com'

        with pytest.raises(ValueError):
            snoo.get('/url')

    def test_oauth_returns_old_oauth(self):
        snoo = snooble.Snooble('my-test-useragent')
        original_auth = snoo.oauth(snooble.oauth.SCRIPT_KIND, scopes=['read'],
           client_id='ThisIsTheClientID', secret_id='ThisIsTheSecretID',
           username='my-username', password='my-password')
        assert original_auth is None

        new_auth = snoo.oauth()
        assert new_auth.scopes == ['read']
        assert new_auth.client_id == 'ThisIsTheClientID'
        assert new_auth.secret_id == 'ThisIsTheSecretID'
        assert new_auth.username == 'my-username'
        assert new_auth.password == 'my-password'

        final_auth = snooble.oauth.OAuth(snooble.oauth.SCRIPT_KIND, scopes=['read'],
           client_id='AnotherClientID', secret_id='AnotherSecretID',
           username='my-other-username', password='my-other-password')

        snoo.oauth(final_auth)
        assert snoo.oauth() is final_auth

    def test_authorize_cannot_be_called_without_credentials(self):
        snoo = snooble.Snooble('my-test-useragent')
        with pytest.raises(ValueError):
            snoo.authorize()

    @responses.activate
    def test_authorize_as_script_successful(self, monkeypatch):
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

        snoo.authorize()

        assert len(responses.calls) == 1
        response = responses.calls[0].request
        assert response.headers['User-Agent'] == 'my-test-useragent'
        assert response.headers['Authorization'] == \
               'Basic ' + b64encode(b'ThisIsTheClientID:ThisIsTheSecretID').decode('utf-8')
        assert 'grant_type=password' in response.body
        assert 'username=my-username' in response.body
        assert 'password=my-password' in response.body

        assert snoo._authorized is True
        assert snoo.oauth().authorization == \
            snooble.oauth.Authorization(token_type='bearer', recieved=1234567890,
                                        length=3600, token='fhTdafZI-0ClEzzYORfBSCR7x3M')

    def test_authorize_as_script_failing(self):
        with responses.RequestsMock() as rsps:
            rsps.add(responses.POST, 'https://www.reddit.com/api/v1/access_token',
                          body=json.dumps({'error': 401}), status=401)

            snoo = snooble.Snooble('my-test-useragent')

            with pytest.raises(snooble.errors.RedditError):
                snoo.oauth(snooble.oauth.SCRIPT_KIND, scopes=['read'],
                           client_id='ThisIsTheClientID', secret_id='ThisIsTheSecretID',
                           username='my-username', password='my-password')

                snoo.authorize()

            assert snoo.oauth().authorization is None
            assert snoo.authorized is False

        with responses.RequestsMock() as rsps:
            rsps.add(responses.POST, 'https://www.reddit.com/api/v1/access_token',
                          body=json.dumps({'error': 404}), status=404)

            snoo = snooble.Snooble('my-test-useragent')
            snoo.oauth(snooble.oauth.SCRIPT_KIND, scopes=['read'],
                       client_id='ThisIsTheClientID', secret_id='ThisIsTheSecretID',
                       username='my-username', password='my-password')

            with pytest.raises(snooble.errors.RedditError):
                snoo.authorize()

            assert snoo.oauth().authorization is None
            assert snoo.authorized is False

    def test_auth_url(self):
        snoo = snooble.Snooble('my-test-useragent')
        snoo.oauth(snooble.oauth.EXPLICIT_KIND, scopes=['read'],
            client_id='ThisIsTheClientID', secret_id='ThisIsTheSecretID',
            redirect_uri='https://my.redirect.site.com')

        url = snoo.auth_url('my-top-secret-secret')
        assert 'client_id=ThisIsTheClientID' in url
        assert 'redirect_uri=' + quote_plus('https://my.redirect.site.com') in url
        assert 'duration=temporary' in url
        assert 'state=my-top-secret-secret' in url
        assert 'response_type=code' in url


    @pytest.mark.xfail
    @responses.activate
    def test_authorize_explicit(self):
        assert False
