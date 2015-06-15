import time
import functools


class _LimitationObject(object):

    def __init__(self, ratelimiter, obj, override_list):
        self.__ratelimiter = ratelimiter
        self.__obj = obj
        self.__override_list = override_list

    def __getattr__(self, name):
        attribute = getattr(self.__obj, name)

        if name not in self.__override_list:
            return attribute
        elif callable(attribute):

            @functools.wraps(attribute)
            def wrapper(*args, **kwargs):
                self.__ratelimiter.take()
                return attribute()
            return wrapper

        else:
            self.__ratelimiter.take()
            return attribute


class RateLimiter(object):

    def __init__(self, rate, per, bursty=True):
        self._bursty = bursty
        if not self.bursty:
            self._burst_bucket_size = rate
            self._burst_refresh_period = per
            per = per / rate
            rate = 1

        self.bucket_size = self.current_bucket = rate
        self.refresh_period = per
        self.last_refresh = time.perf_counter()

    @property
    def bursty(self):
        return self._bursty

    @bursty.setter
    def bursty(self, bursty):
        if bool(bursty) == self._bursty:
            return
        elif bursty:
            self.bucket_size = self._burst_bucket_size
            self.refresh_period = self._burst_refresh_period
            self._bursty = True
        elif not bursty:
            self._burst_bucket_size = self.bucket_size
            self._burst_refresh_period = self.refresh_period
            self.bucket_size = 1
            self.refresh_period = self._burst_refresh_period / self._burst_bucket_size
            self._bursty = False
        else:
            assert False

        if self.current_bucket > self.bucket_size:
            self.current_bucket = self.bucket_size

    def take(self, items=1, block=True):
        for i in range(items):
            while self.current_bucket < 1:
                now = time.perf_counter()
                if (self.last_refresh + self.refresh_period) <= now:
                    self.last_refresh = now
                    self.current_bucket = self.bucket_size
                else:
                    time.sleep((self.last_refresh + self.refresh_period) - now)

            self.current_bucket -= 1

    def limitate(self, obj, overrides):
        return _LimitationObject(self, obj, overrides)
