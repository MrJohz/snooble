from snooble import ratelimit

import time  # used to monkeypatch this module

from unittest import mock
import pytest


class TestRatelimit(object):

    def test_bursty(self):
        limiter = ratelimit.RateLimiter(5, 1, bursty=False)
        assert limiter.current_bucket == 1
        assert limiter.refresh_period == 1 / 5
        limiter.take()
        assert limiter.current_bucket == 0

    def test_bursty_property(self):
        limiter = ratelimit.RateLimiter(5, 1, bursty=True)
        assert limiter.current_bucket == 5
        assert limiter.refresh_period == 1

        limiter.bursty = False
        assert limiter.bucket_size == 1
        assert limiter.current_bucket == 1
        assert limiter.refresh_period == 1 / 5

        limiter.bursty = False
        assert limiter.bucket_size == 1
        assert limiter.current_bucket == 1
        assert limiter.refresh_period == 1 / 5
        limiter.take()
        assert limiter.current_bucket == 0

        limiter.bursty = True
        assert limiter.bucket_size == 5
        assert limiter.current_bucket == 0
        assert limiter.refresh_period == 1

        limiter.bursty = True
        assert limiter.bucket_size == 5
        assert limiter.current_bucket == 0
        assert limiter.refresh_period == 1

    def test_able_to_take_when_bucket_filled(self, monkeypatch):
        mocker = mock.Mock()
        monkeypatch.setattr(time, 'sleep', mocker)

        limiter = ratelimit.RateLimiter(5, 1)
        assert limiter.current_bucket == 5
        limiter.take()
        assert limiter.current_bucket == 4
        limiter.take(4)
        assert limiter.current_bucket == 0

        assert not mocker.called

    def test_sleeps_until_finished(self, monkeypatch):
        sleep_mocker = mock.Mock()
        timer_mocker = mock.Mock(side_effect=[0, 0.1, 0.2, 1])
        monkeypatch.setattr(time, 'sleep', sleep_mocker)
        monkeypatch.setattr(time, 'perf_counter', timer_mocker)

        limiter = ratelimit.RateLimiter(1, 1)
        assert limiter.current_bucket == 1

        limiter.take()
        assert limiter.current_bucket == 0
        assert not sleep_mocker.called

        limiter.take()
        assert limiter.current_bucket == 0
        assert sleep_mocker.called
        assert sleep_mocker.call_args_list == [mock.call(0.9), mock.call(0.8)]
        assert len(timer_mocker.call_args_list) == 4

    def test_taking_many_at_once_small_bucket(self, monkeypatch):
        sleep_mocker = mock.Mock()
        timer_mocker = mock.Mock(side_effect=range(100))
        monkeypatch.setattr(time, 'sleep', sleep_mocker)
        monkeypatch.setattr(time, 'perf_counter', timer_mocker)

        small_bucket = ratelimit.RateLimiter(1, 1)
        assert small_bucket.current_bucket == 1

        small_bucket.take()
        assert small_bucket.current_bucket == 0

        small_bucket.take(8)
        assert small_bucket.current_bucket == 0
        assert len(timer_mocker.call_args_list) == 9

    def test_taking_many_at_once_big_bucket(self, monkeypatch):
        sleep_mocker = mock.Mock()
        timer_mocker = mock.Mock(side_effect=range(100))
        monkeypatch.setattr(time, 'sleep', sleep_mocker)
        monkeypatch.setattr(time, 'perf_counter', timer_mocker)

        big_bucket = ratelimit.RateLimiter(3, 1)
        assert big_bucket.current_bucket == 3

        big_bucket.take()
        assert big_bucket.current_bucket == 2
        assert not sleep_mocker.called

        big_bucket.take(8)
        assert big_bucket.current_bucket == 0
        assert len(timer_mocker.call_args_list) == 3

    def test_equality(self):

        limit1 = ratelimit.RateLimiter(rate=60, per=60, bursty=False)
        limit2 = ratelimit.RateLimiter(rate=60, per=60, bursty=True)
        limit3 = ratelimit.RateLimiter(rate=25, per=50, bursty=True)
        limit4 = ratelimit.RateLimiter(rate=60, per=60, bursty=False)

        assert limit1 == limit4 and limit4 == limit1
        assert limit1 != limit2
        assert limit1 != limit3
        assert limit1 != (60, 60)


class TestLimitation(object):

    def test_wrapping(self):
        take_mocker = mock.Mock(return_value=True)
        ratelimiter = ratelimit.RateLimiter(1, 1)
        ratelimiter.take = take_mocker

        test_object = mock.Mock()
        limited_object = ratelimiter.limitate(test_object, ['limited_method', 'limited_uncalled_method'])

        limited_object.arbitrary_method()
        assert not take_mocker.called
        assert test_object.arbitrary_method.called
        test_object.reset_mock()
        take_mocker.reset_mock()

        limited_object.arbitrary_uncalled_method
        assert not take_mocker.called
        assert not test_object.arbitrary_uncalled_method.called
        test_object.reset_mock()
        take_mocker.reset_mock()

        limited_object.limited_method()
        assert take_mocker.called
        assert test_object.limited_method.called
        test_object.reset_mock()
        take_mocker.reset_mock()

        limited_object.limited_uncalled_method
        assert not take_mocker.called
        assert not test_object.limited_uncalled_method.called
        test_object.reset_mock()
        take_mocker.reset_mock()

        test_object = mock.Mock()
        test_object.arbitrary_attribute = "arbitrary"
        test_object.limited_attribute = "limited"
        limited_object = ratelimiter.limitate(test_object, ['limited_attribute'])

        limited_object.arbitrary_attribute
        assert not take_mocker.called
        test_object.reset_mock()
        take_mocker.reset_mock()

        limited_object.limited_attribute
        assert take_mocker.called

    def test_wrapper_passes_information_through(self):
        take_mocker = mock.Mock(return_value=True)
        ratelimiter = ratelimit.RateLimiter(1, 1)
        ratelimiter.take = take_mocker

        test_object = mock.Mock()
        limited_object = ratelimiter.limitate(test_object, ['limited_method'])

        limited_object.arbitrary_method("arg1", "arg2", ["args4", "and 5"], name="hello")
        assert not take_mocker.called
        assert (test_object.arbitrary_method.call_args ==
                mock.call("arg1", "arg2", ["args4", "and 5"], name="hello"))

        test_object.reset_mock()

        limited_object.limited_method("arg1", "arg2", ["args4", "and 5"], name="hello")
        assert take_mocker.called
        assert (test_object.limited_method.call_args ==
                mock.call("arg1", "arg2", ["args4", "and 5"], name="hello"))

    @pytest.mark.xfail
    def test_wrapper_looks_like_object(self):
        take_mocker = mock.Mock(return_value=True)
        ratelimiter = ratelimit.RateLimiter(1, 1)
        ratelimiter.take = take_mocker

        class MyCustomObject(object):

            def limited_method(self):
                return "limited"

            def unlimited_method(self, arg1, arg2="hello"):
                return "unlimited"

        test_object = MyCustomObject()

        limited_object = ratelimiter.limitate(test_object, ['limited_method'])

        assert isinstance(limited_object, MyCustomObject)
        assert hasattr(limited_object, 'limited_method')
        assert hasattr(limited_object, 'unlimited_method')
        # TODO: method signatures are alike
