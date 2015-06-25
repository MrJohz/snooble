from snooble import utils

import pytest


class TestFetchParameter(object):

    def test_where_argument_exists(self):
        assert utils.fetch_parameter({'a': 1}, 'a') == 1

    def test_where_argument_not_exists(self):
        with pytest.raises(TypeError):
            utils.fetch_parameter({'a': 1}, 'b')


class TestAssignParameters(object):

    @pytest.fixture
    def obj(self):
        class FooClass:
            pass
        return FooClass()

    def test_assign_single_param(self, obj):
        kwargs = {'three': 3, 'four': 4}
        utils.assign_parameters(obj, kwargs, ['three'])
        assert len(kwargs) == 1
        assert hasattr(obj, 'three') and obj.three == 3

    def test_assign_many_params(self, obj):
        kwargs = {'many': True, 'ones': 1111}
        utils.assign_parameters(obj, kwargs, ('many', 'ones'))
        assert len(kwargs) == 0
        assert hasattr(obj, 'many') and obj.many is True
        assert hasattr(obj, 'ones') and obj.ones == 1111

    def test_missing_param(self, obj):
        kwargs = {'present': True}
        with pytest.raises(TypeError):
            utils.assign_parameters(obj, kwargs, ['missing'])


class TestStrList(object):

    def test_with_string(self):
        assert utils.strlist('hello') == ['hello']

    def test_with_list(self):
        assert utils.strlist(['hello', 'goodbye']) == ['hello', 'goodbye']

    def test_with_iter(self):
        iter_list = iter(['hello', 'goodbye'])
        assert utils.strlist(iter_list) == iter_list
