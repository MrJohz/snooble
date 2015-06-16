import snooble

import pytest


class TestSnooble(object):

    def test_initialisation(self):
        snoo = snooble.Snooble('my-test-useragent')
        assert snoo.useragent == 'my-test-useragent'
        assert snoo._ratelimiter == snooble.ratelimit.RateLimiter(60, 60, False)
        assert snoo._authorized is False
        assert snoo.domain.www == snooble.WWW_DOMAIN
        assert snoo.domain.auth == snooble.AUTH_DOMAIN

        snoo.www_domain = 'http://my-fake-reddit.com'
        snoo.auth_domain = 'http://oauth.my-fake-reddit.com'

        assert snoo.domain.www == 'http://my-fake-reddit.com'
        assert snoo.domain.auth == 'http://oauth.my-fake-reddit.com'

        with pytest.raises(snooble.errors.SnoobleError):
            snoo.get('/url')
