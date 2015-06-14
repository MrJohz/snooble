import functools

class RateLimiter(object):

    def __init__(self, rate, per):
        self._bucket_size = rate
        self._refresh_rate = per

def ratelimited(func):
    @functools.wraps(func)
    def limited(self, *args, **kwargs):
        pass

    return limited
