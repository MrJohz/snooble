from snooble import oauth

import pytest


class TestOAuth(object):

    def test_scope(self):
        auth = oauth.OAuth(oauth.SCRIPT_KIND, scopes=['read'],
            client_id='...', secret_id='...', username='...', password='...')
        assert auth.scopes == ['read']

    def test_only_has_correct_attributes(self):
        auth = oauth.OAuth(oauth.SCRIPT_KIND, scopes=['read'],
            client_id='...', secret_id='...', username='...', password='...')
        with pytest.raises(AttributeError):
            auth.mobile

    def test_lack_of_params(self):
        with pytest.raises(TypeError):
            oauth.OAuth(oauth.SCRIPT_KIND, scopes=['read'])

    def test_with_invalid_type(self):
        with pytest.raises(ValueError):
            oauth.OAuth('INVALID AUTH KIND', scopes=['read'])

    def test_script(self):
        auth = oauth.OAuth(oauth.SCRIPT_KIND, scopes=['read'],
            client_id='...', secret_id='...', username='...', password='...')

        assert auth.client_id == '...'
        assert auth.secret_id == '...'
        assert auth.username == '...'
        assert auth.password == '...'

    def test_explicit(self):
        auth = oauth.OAuth(oauth.EXPLICIT_KIND, scopes=['read'],
            client_id='...', secret_id='...', redirect_uri='...')

        assert auth.client_id == '...'
        assert auth.secret_id == '...'
        assert auth.redirect_uri == '...'
        assert auth.mobile is False
        assert auth.duration == 'temporary'

        auth = oauth.OAuth(oauth.EXPLICIT_KIND, scopes=['read'],
            client_id='...', secret_id='...', redirect_uri='...', mobile=True)

        assert auth.mobile is True

    def test_application_explicit(self):
        auth = oauth.OAuth(oauth.APPLICATION_EXPLICIT_KIND, scopes=['read'],
            client_id='...', secret_id='...')

        assert auth.client_id == '...'
        assert auth.secret_id == '...'

    def test_implicit(self):
        auth = oauth.OAuth(oauth.IMPLICIT_KIND, scopes=['read'],
            client_id='...', redirect_uri='...')

        assert auth.client_id == '...'
        assert auth.redirect_uri == '...'
        assert auth.mobile is False

    def test_application_implicit(self):
        auth = oauth.OAuth(oauth.APPLICATION_IMPLICIT_KIND, scopes=['read'],
            client_id='...')

        assert auth.client_id == '...'
