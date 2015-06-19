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
        assert not snoo.authorized
        assert snoo.domain.www == snooble.WWW_DOMAIN
        assert snoo.domain.auth == snooble.AUTH_DOMAIN

        ratelimit = snooble.ratelimit.RateLimiter(60, 60, True)
        snoo2 = snooble.Snooble('my-test-useragent', ratelimit=ratelimit)
        assert snoo2._limiter is ratelimit

        auth = snooble.oauth.OAuth(snooble.oauth.APPLICATION_INSTALLED_KIND,
                                   scopes=['read'], client_id='ThisIsTheClientID')
        snoo3 = snooble.Snooble('my-test-useragent', auth=auth)
        assert snoo3._auth is auth

    def test_domain_property(self):
        snoo = snooble.Snooble('my-test-useragent',
                               www_domain='www.domain', auth_domain='auth.domain')
        assert snoo.domain.www == 'www.domain'
        assert snoo.domain.auth == 'auth.domain'

        snoo.www_domain = 'http://my-fake-reddit.com'
        snoo.auth_domain = 'http://oauth.my-fake-reddit.com'

        assert snoo.domain.www == 'http://my-fake-reddit.com'
        assert snoo.domain.auth == 'http://oauth.my-fake-reddit.com'

        snoo.domain = ('www.domain.again', 'auth.domain.again')
        assert snoo.domain.www == 'www.domain.again'
        assert snoo.domain.auth == 'auth.domain.again'

    def test_oauth_returns_old_oauth(self):
        snoo = snooble.Snooble('my-test-useragent')
        original_auth = snoo.oauth(snooble.oauth.SCRIPT_KIND, scopes=['read'],
                                   client_id='ClientID', secret_id='SecretID',
                                   username='my-username', password='my-password')
        assert original_auth is None

        new_auth = snoo.oauth()
        assert new_auth.scopes == ['read']
        assert new_auth.client_id == 'ClientID'
        assert new_auth.secret_id == 'SecretID'
        assert new_auth.username == 'my-username'
        assert new_auth.password == 'my-password'

        final = snooble.oauth.OAuth(snooble.oauth.SCRIPT_KIND, scopes=['read'],
                                    client_id='OtherClientID', secret_id='OtherSecretID',
                                    username='other-username', password='other-password')

        snoo.oauth(final)
        assert snoo.oauth() is final

    def test_authorize_cannot_be_called_without_credentials(self):
        snoo = snooble.Snooble('my-test-useragent')
        with pytest.raises(ValueError):
            snoo.authorize()

    def test_auth_url(self):
        snoo = snooble.Snooble('my-test-useragent')
        snoo.oauth(snooble.oauth.EXPLICIT_KIND, scopes=['read'],
                   client_id='ThisIsTheClientID', secret_id='ThisIsTheSecretID',
                   redirect_uri='https://my.site.com')

        url = snoo.auth_url('my-top-secret-secret')
        assert 'client_id=ThisIsTheClientID' in url
        assert 'redirect_uri=' + quote_plus('https://my.site.com') in url
        assert 'duration=temporary' in url
        assert 'state=my-top-secret-secret' in url
        assert 'response_type=code' in url
        assert ".compact" not in url

        snoo.oauth().mobile = True
        url = snoo.auth_url('secret-with-mobile-url')
        assert ".compact" in url

        with pytest.raises(ValueError):
            snooble.Snooble('my-test-useragent').auth_url('without-credentials')

        snoo = snooble.Snooble('my-test-useragent')
        snoo.oauth(snooble.oauth.SCRIPT_KIND, scopes=['read'],
                   client_id='ThisIsTheClientID', secret_id='ThisIsTheSecretID',
                   username='my-username', password='my-password')
        with pytest.raises(ValueError):
            snoo.auth_url('with-wrong-auth-kind')

        snoo.oauth(snooble.oauth.IMPLICIT_KIND, scopes=['read'],
                   client_id='ThisIsTheClientID', redirect_uri='https://my.site.com')
        url = snoo.auth_url('my-top-secret-secret')
        assert 'client_id=ThisIsTheClientID' in url
        assert 'redirect_uri=' + quote_plus('https://my.site.com') in url
        assert 'state=my-top-secret-secret' in url
        assert 'response_type=token' in url
        assert ".compact" not in url

    @responses.activate
    def test_authorize_as_script_successful(self, monkeypatch):
        time_mock = mock.Mock(return_value=1234567890)
        monkeypatch.setattr('time.time', time_mock)

        responses.add(responses.POST, 'https://www.reddit.com/api/v1/access_token',
                      body=json.dumps({'access_token': 'fhTdafZI-0ClEzzYORfBSCR7x3M',
                                       'expires_in': 3600,
                                       'scope': 'read',
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

    @responses.activate
    def test_authorize_as_script_failing(self):
        responses.add(responses.POST, 'https://www.reddit.com/api/v1/access_token',
                      body=json.dumps({'error': 401}), status=401)

        snoo = snooble.Snooble('my-test-useragent')
        snoo.oauth(snooble.oauth.SCRIPT_KIND, scopes=['read'],
                   client_id='ThisIsTheClientID', secret_id='ThisIsTheSecretID',
                   username='my-username', password='my-password')

        with pytest.raises(snooble.errors.RedditError):
            snoo.authorize()

        assert snoo.oauth().authorization is None
        assert snoo.authorized is False

    @responses.activate
    def test_authorize_explicit(self):
        responses.add(responses.POST, 'https://www.reddit.com/api/v1/access_token',
                      body=json.dumps({'access_token': 'fhTdafZI-0ClEzzYORfBSCR7x3M',
                                       'expires_in': 3600,
                                       'scope': '*',
                                       'token_type': 'bearer',
                                       'scope': 'read'}),
                      content_type='application/json')

        snoo = snooble.Snooble('my-test-useragent')
        snoo.oauth(snooble.oauth.EXPLICIT_KIND, scopes=['read'],
                   client_id='ThisIsTheClientID', secret_id='ThisIsTheSecretID',
                   redirect_uri='https://my.site.com')

        snoo.authorize('reddit-magic-token')
        assert len(responses.calls) == 1
        request = responses.calls[0].request
        assert request.headers['User-Agent'] == 'my-test-useragent'
        assert request.headers['Authorization'] == \
            'Basic ' + b64encode(b'ThisIsTheClientID:ThisIsTheSecretID').decode('utf-8')
        assert 'grant_type=authorization_code' in request.body
        assert 'code=reddit-magic-token' in request.body
        assert 'redirect_uri=' + quote_plus('https://my.site.com') in request.body

        assert snoo.authorized

    @responses.activate
    def test_authorize_as_explicit_failing(self):
        responses.add(responses.POST, 'https://www.reddit.com/api/v1/access_token',
                      body=json.dumps({'error': 401}), status=401)

        snoo = snooble.Snooble('my-test-useragent')

        snoo.oauth(snooble.oauth.EXPLICIT_KIND, scopes=['read'],
                   client_id='ThisIsTheClientID', secret_id='ThisIsTheSecretID',
                   redirect_uri='https://my.site.com')

        with pytest.raises(snooble.errors.RedditError):
            snoo.authorize('reddit-magic-token')

        assert not snoo.authorized

    def test_authorize_as_implicit(self):
        snoo = snooble.Snooble('my-test-useragent')
        snoo.oauth(snooble.oauth.IMPLICIT_KIND, scopes=['read'],
                   client_id='ThisIsTheClientID', redirect_uri='https://my.site.com')
        snoo.authorize('reddit-magic-token')

        assert snoo.authorized

    @responses.activate
    def test_authorize_as_explicit_app(self):
        responses.add(responses.POST, 'https://www.reddit.com/api/v1/access_token',
                      body=json.dumps({'access_token': 'fhTdafZI-0ClEzzYORfBSCR7x3M',
                                       'expires_in': 3600,
                                       'scope': '*',
                                       'token_type': 'bearer',
                                       'scope': 'read'}),
                      content_type='application/json')

        snoo = snooble.Snooble('my-test-useragent')
        snoo.oauth(snooble.oauth.APPLICATION_EXPLICIT_KIND, scopes=['read'],
                   client_id='ThisIsTheClientID', secret_id='ThisIsTheSecretID')

        snoo.authorize()

        assert len(responses.calls) == 1

        request = responses.calls[0].request
        assert request.headers['User-Agent'] == 'my-test-useragent'
        assert request.headers['Authorization'] == \
            'Basic ' + b64encode(b'ThisIsTheClientID:ThisIsTheSecretID').decode('utf-8')
        assert 'grant_type=client_credentials' in request.body

        assert snoo.authorized

    @responses.activate
    def test_authorize_as_explicit_app_failing(self):
        responses.add(responses.POST, 'https://www.reddit.com/api/v1/access_token',
                      body=json.dumps({'error': 401}), status=401)

        snoo = snooble.Snooble('my-test-useragent')

        snoo.oauth(snooble.oauth.APPLICATION_EXPLICIT_KIND, scopes=['read'],
                   client_id='ThisIsTheClientID', secret_id='ThisIsTheSecretID')

        with pytest.raises(snooble.errors.RedditError):
            snoo.authorize()

        assert not snoo.authorized

    @responses.activate
    def test_authorize_as_installed_app(self):
        responses.add(responses.POST, 'https://www.reddit.com/api/v1/access_token',
                      body=json.dumps({'access_token': 'fhTdafZI-0ClEzzYORfBSCR7x3M',
                                       'expires_in': 3600,
                                       'scope': '*',
                                       'token_type': 'bearer',
                                       'scope': 'read'}),
                      content_type='application/json')

        snoo = snooble.Snooble('my-test-useragent')
        snoo.oauth(snooble.oauth.APPLICATION_INSTALLED_KIND, scopes=['read'],
                   client_id='ThisIsTheClientID')

        snoo.authorize()

        assert len(responses.calls) == 1

        request = responses.calls[0].request
        assert request.headers['User-Agent'] == 'my-test-useragent'
        assert request.headers['Authorization'] == \
            'Basic ' + b64encode(b'ThisIsTheClientID:').decode('utf-8')
        assert 'grant_type=' + quote_plus('https://oauth.reddit.com/grants/installed_client') \
            in request.body

        assert snoo.authorized

    @responses.activate
    def test_authorize_as_installed_app_failing(self):
        responses.add(responses.POST, 'https://www.reddit.com/api/v1/access_token',
                      body=json.dumps({'error': 401}), status=401)

        snoo = snooble.Snooble('my-test-useragent')

        snoo.oauth(snooble.oauth.APPLICATION_INSTALLED_KIND, scopes=['read'],
                   client_id='ThisIsTheClientID')

        with pytest.raises(snooble.errors.RedditError):
            snoo.authorize()

        assert not snoo.authorized

    def test_unrecognised_auth_kind(self):
        auth = snooble.oauth.OAuth(snooble.oauth.APPLICATION_INSTALLED_KIND,
                                   scopes=['read'], client_id='ThisIsTheClientID')
        auth.kind = "This kind doesn't exist!"

        snoo = snooble.Snooble('my-test-useragent', auth=auth)
        with pytest.raises(ValueError):
            snoo.authorize()
