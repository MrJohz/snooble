import snooble

import pytest
import responses
import json
import vcr
import os
from base64 import b64encode
from urllib.parse import quote_plus

player = vcr.VCR(
    serializer='yaml',
    record_mode='none' if os.environ.get('CI') else 'once',
    cassette_library_dir='tests/integration/cassettes',
    match_on=['uri', 'method'],
    filter_headers=['Authorization'],
    filter_query_parameters=['username', 'password'],
    filter_post_data_parameters=['username', 'password'])

UAGENT = 'Snooble Integration Testing (/u/MrJohz)'


def env(name, length):
    return os.environ.get('SNOOBLE_TEST_' + name, 'x' * length)


class TestAuthorization(object):

    def test_authorize_as_script_successful(self):
        snoo = snooble.Snooble(UAGENT)
        snoo.oauth(snooble.oauth.SCRIPT_KIND, scopes=snooble.oauth.ALL_SCOPES,
                   client_id=env('CLIENT_ID', 14), secret_id=env('SECRET_ID', 27),
                   username=env('USERNAME', 10), password=env('PASSWORD', 10))

        with player.use_cassette('test_authorize_as_script_successful') as cass:
            snoo.authorize()
            assert snoo.authorized

            assert len(cass) == 1
            request = cass.requests[0]
            assert request.headers['User-Agent'] == UAGENT
            assert b'grant_type=password' in request.body

    def test_authorize_as_script_failing(self):
        snoo = snooble.Snooble(UAGENT)
        snoo.oauth(snooble.oauth.SCRIPT_KIND, scopes=snooble.oauth.ALL_SCOPES,
                   client_id='NONEXISTENT_ID', secret_id=env('SECRET_ID', 27),
                   username=env('USERNAME', 10), password=env('PASSWORD', 10))

        with player.use_cassette('test_authorize_as_script_failing (no-id)'):
            with pytest.raises(snooble.errors.RedditError):
                snoo.authorize()
        assert not snoo.authorized

        snoo.oauth(snooble.oauth.SCRIPT_KIND, scopes=snooble.oauth.ALL_SCOPES,
                   client_id=env('CLIENT_ID', 14), secret_id=env('SECRET_ID', 27),
                   username='NONEXISTENT_UNAME', password=env('PASSWORD', 10))
        with player.use_cassette('test_authorize_as_script_failing (no-uname)'):
            with pytest.raises(snooble.errors.RedditError):
                snoo.authorize()
        assert not snoo.authorized

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
