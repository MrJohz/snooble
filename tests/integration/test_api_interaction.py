import snooble

import pytest
import vcr
import os

player = vcr.VCR(
    serializer='yaml',
    record_mode='none' if os.environ.get('CI') else 'once',
    cassette_library_dir='tests/integration/cassettes',
    match_on=['uri', 'method'],
    filter_headers=['Authorization'],
    filter_query_parameters=['username', 'password'],
    filter_post_data_parameters=['username', 'password'])

if os.environ.get('CI'):
    ratelimit = snooble.ratelimit.RateLimiter(1000, per=1, bursty=True)
else:
    ratelimit = snooble.ratelimit.RateLimiter(1, per=2, bursty=False)

UAGENT = 'Snooble Integration Testing (/u/MrJohz)'


def env(name, length):
    return os.environ.get('SNOOBLE_TEST_' + name, 'x' * length)


class TestAPIInteraction(object):

    @pytest.fixture
    def snoo(self):
        snoo = snooble.Snooble(UAGENT, ratelimit=ratelimit)
        snoo.oauth(snooble.oauth.SCRIPT_KIND, scopes=snooble.oauth.ALL_SCOPES,
                   client_id=env('CLIENT_ID', 14), secret_id=env('SECRET_ID', 27),
                   username=env('USERNAME', 10), password=env('PASSWORD', 10))

        with player.use_cassette('authenticate'):
            snoo.authorize()

        return snoo

    @player.use_cassette
    def test_get_fails_if_not_authorized(self):
        snoo = snooble.Snooble('my-test-useragent')
        with pytest.raises(ValueError):
            snoo.get('any/path/here')

    @player.use_cassette
    def test_get_basic_endpoint(self, snoo):
        resp = snoo.get('api/v1/me')
        assert resp['name'] == resp.json['data']['name'] == 'snooble_test_account'
        assert type(resp) is snooble.responses.Response

    @player.use_cassette
    def test_get_listing(self, snoo):
        resp = snoo.get('subreddits/new', limit=1)
        assert len(resp) == 1
        for child in resp:
            assert isinstance(child, snooble.responses.Subreddit)
