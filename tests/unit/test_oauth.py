from snooble import oauth

import pytest


class TestOAuth(object):

    def test_scope(self):
        auth = oauth.OAuth(oauth.SCRIPT_KIND, scopes=['read'], client_id='...',
                           secret_id='...', username='...', password='...')
        assert auth.scopes == ['read']

    def test_lack_of_params(self):
        with pytest.raises(TypeError):
            oauth.OAuth(oauth.SCRIPT_KIND, scopes=['read'])

    def test_with_invalid_type(self):
        with pytest.raises(ValueError):
            oauth.OAuth('INVALID AUTH KIND', scopes=['read'])

    def test_script(self):
        auth = oauth.OAuth(oauth.SCRIPT_KIND, scopes=['read'], client_id='...',
                           secret_id='...', username='...', password='...')

        assert auth.client_id == '...'
        assert auth.secret_id == '...'
        assert auth.username == '...'
        assert auth.password == '...'

    def test_explicit(self):
        auth = oauth.OAuth(oauth.EXPLICIT_KIND, scopes=['read'], client_id='...',
                           secret_id='...', redirect_uri='...')

        assert auth.client_id == '...'
        assert auth.secret_id == '...'
        assert auth.redirect_uri == '...'
        assert auth.mobile is False
        assert auth.duration == 'temporary'

        auth = oauth.OAuth(oauth.EXPLICIT_KIND, scopes=['read'], client_id='...',
                           secret_id='...', redirect_uri='...', mobile=True)

        assert auth.mobile is True

    def test_application_explicit(self):
        auth = oauth.OAuth(oauth.APPLICATION_EXPLICIT_KIND, scopes=['read'],
                           client_id='...', secret_id='...')

        assert auth.client_id == '...'
        assert auth.secret_id == '...'

    def test_implicit(self):
        auth = oauth.OAuth(oauth.IMPLICIT_KIND, scopes=['read'], client_id='...',
                           redirect_uri='...')

        assert auth.client_id == '...'
        assert auth.redirect_uri == '...'
        assert auth.mobile is False

    def test_application_installed(self):
        auth = oauth.OAuth(oauth.APPLICATION_INSTALLED_KIND, scopes=['read'],
                           client_id='...', device_id='...')

        assert auth.client_id == '...'


class TestAuthorization(object):

    def test_initialization(self):
        auth = oauth.Authorization(token_type='a', token='b', recieved=0, length=1)

        assert auth.token_type == 'a'
        assert auth.token == 'b'
        assert auth.recieved == 0
        assert auth.length == 1

    def test_equality(self):
        auth1 = oauth.Authorization(token_type='a', token='b', recieved=0, length=1)
        auth2 = oauth.Authorization(token_type='a', token='b', recieved=0, length=1)
        auth3 = oauth.Authorization(token_type='a', token='b', recieved=0, length=4)

        from collections import namedtuple
        shitty_auth = namedtuple('Authorization', ['token_type', 'token', 'recieved', 'length'])
        auth4 = shitty_auth(token_type='a', token='b', recieved=0, length=1)

        assert auth1 == auth2 and auth2 == auth1
        assert auth1 != auth3
        assert auth1 != auth4
