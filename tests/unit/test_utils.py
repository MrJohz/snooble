import pytest

from snooble import utils


class TestFetchParameter(object):

    def test_where_argument_exists(self):
        assert utils.fetch_parameter({'a': 1}, 'a') == 1

    def test_where_argument_not_exists(self):
        with pytest.raises(TypeError):
            utils.fetch_parameter({'a': 1}, 'b')


class TestStrList(object):

    def test_with_string(self):
        assert utils.strlist('hello') == ['hello']

    def test_with_list(self):
        assert utils.strlist(['hello', 'goodbye']) == ['hello', 'goodbye']

    def test_with_iter(self):
        iter_list = iter(['hello', 'goodbye'])
        assert utils.strlist(iter_list) == iter_list
