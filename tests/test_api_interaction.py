import snooble

import pytest


class TestAPIInteraction(object):

    def test_get_fails_if_not_authorized(self):
        snoo = snooble.Snooble('my-test-useragent')
        with pytest.raises(ValueError):
            snoo.get('any/path/here')
