from snooble.utils import cbc

import pytest


class TestCBC(object):

    def test_contains_correct_properties(self):
        class MY_CALLBACKS(cbc.CallbackClass):

            def hyphen(arg):
                return "-{arg}-".format(arg=arg)

            def plus(arg):
                return "+{arg}+".format(arg=arg)

            def star(arg):
                return "*{arg}*".format(arg=arg)

        assert "hyphen" in MY_CALLBACKS
        assert MY_CALLBACKS['hyphen'] is MY_CALLBACKS.hyphen
        assert "plus" in MY_CALLBACKS
        assert "star" in MY_CALLBACKS
        assert MY_CALLBACKS['star']('a') == MY_CALLBACKS.star('a') == '*a*'

        assert MY_CALLBACKS.get('star') is MY_CALLBACKS.star
        assert MY_CALLBACKS.get('non-existant') is None
        assert MY_CALLBACKS.get('more-non-existant', 'default') == 'default'

        with pytest.raises(KeyError):
            MY_CALLBACKS['non-existant']

        assert len(MY_CALLBACKS) == 3
        assert set(MY_CALLBACKS) == {'hyphen', 'plus', 'star'}

    def test_renaming_properties(self):
        class MY_CALLBACKS(cbc.CallbackClass):

            @cbc.CallbackClass.key('hyphen')
            def format_hyphen(arg):
                return "-{arg}-".format(arg=arg)

            @cbc.CallbackClass.key('plus')
            def plus_format(arg):
                return "+{arg}+".format(arg=arg)

            @cbc.CallbackClass.key('star')
            def star(arg):
                return "*{arg}*".format(arg=arg)

        assert "hyphen" in MY_CALLBACKS
        assert MY_CALLBACKS['hyphen'] is MY_CALLBACKS.format_hyphen
        assert "plus" in MY_CALLBACKS
        assert "star" in MY_CALLBACKS
        assert MY_CALLBACKS['star']('a') == MY_CALLBACKS.star('a') == '*a*'

        assert len(MY_CALLBACKS) == 3
        assert set(MY_CALLBACKS) == {'hyphen', 'plus', 'star'}

    def test_ignoring_properties(self):
        class MY_CALLBACKS(cbc.CallbackClass):

            def hyphen(arg):
                return "-{arg}-".format(arg=arg)

            def plus(arg):
                return "+{arg}+".format(arg=arg)

            def star(arg):
                return "*{arg}*".format(arg=arg)

            @cbc.CallbackClass.ignore
            def ignore_this():
                return "ignored"

        assert "hyphen" in MY_CALLBACKS
        assert MY_CALLBACKS['hyphen'] is MY_CALLBACKS.hyphen
        assert "plus" in MY_CALLBACKS
        assert "star" in MY_CALLBACKS
        assert MY_CALLBACKS['star']('a') == MY_CALLBACKS.star('a') == '*a*'

        assert len(MY_CALLBACKS) == 3
        assert set(MY_CALLBACKS) == {'hyphen', 'plus', 'star'}

        assert MY_CALLBACKS.ignore_this() == "ignored"

    def test_add_callback(self):
        class MY_CALLBACKS(cbc.CallbackClass):
            pass

        @MY_CALLBACKS.add_callback()
        def hyphen(arg):
            return "-{arg}-".format(arg=arg)

        @MY_CALLBACKS.add_callback('plus')
        def plus_format(arg):
            return "+{arg}+".format(arg=arg)

        def star(arg):
            return "*{arg}*".format(arg=arg)

        def brackets_formatter(arg):
            return "({arg})".format(arg=arg)

        MY_CALLBACKS.add_callback(star)
        MY_CALLBACKS.add_callback('brackets', brackets_formatter)

        assert len(MY_CALLBACKS) == 4
        assert set(MY_CALLBACKS) == {"hyphen", "plus", "star", "brackets"}
        assert MY_CALLBACKS['hyphen']('a') == "-a-"
        assert MY_CALLBACKS['plus']('a') == "+a+"
        assert MY_CALLBACKS['star']('a') == "*a*"
        assert MY_CALLBACKS['brackets']('a') == '(a)'

        with pytest.raises(TypeError):
            MY_CALLBACKS.add_callback(1, 2, 3, 4, 5)

    def test_non_callables(self):
        class MY_CALLBACKS(cbc.CallbackClass):

            def hyphen(arg):
                return "-{arg}-".format(arg=arg)

            def plus(arg):
                return "+{arg}+".format(arg=arg)

            def star(arg):
                return "*{arg}*".format(arg=arg)

            invisible_attr = 'hello'

        assert "hyphen" in MY_CALLBACKS
        assert MY_CALLBACKS['hyphen'] is MY_CALLBACKS.hyphen
        assert "plus" in MY_CALLBACKS
        assert "star" in MY_CALLBACKS
        assert MY_CALLBACKS['star']('a') == MY_CALLBACKS.star('a') == '*a*'

        assert len(MY_CALLBACKS) == 3
        assert set(MY_CALLBACKS) == {'hyphen', 'plus', 'star'}

        assert "invisible_attr" not in MY_CALLBACKS
        assert MY_CALLBACKS.invisible_attr == 'hello'

    def test_default_get(self):
        class MY_CALLBACKS(cbc.CallbackClass):

            def hyphen(arg):
                return "-{arg}-".format(arg=arg)

            def plus(arg):
                return "+{arg}+".format(arg=arg)

            def star(arg):
                return "*{arg}*".format(arg=arg)

            @cbc.CallbackClass.default
            def default(arg):
                return "{arg}".format(arg=arg)

        assert "hyphen" in MY_CALLBACKS
        assert MY_CALLBACKS['hyphen'] is MY_CALLBACKS.hyphen
        assert "plus" in MY_CALLBACKS
        assert "star" in MY_CALLBACKS
        assert MY_CALLBACKS['star']('a') == MY_CALLBACKS.star('a') == '*a*'
        assert "default" in MY_CALLBACKS

        assert MY_CALLBACKS.get('star') is MY_CALLBACKS.star
        assert MY_CALLBACKS.get('non-existant') is None
        assert MY_CALLBACKS.get('more-non-existant', 'default') == 'default'

        assert MY_CALLBACKS['anything-here'] is MY_CALLBACKS.default

        assert len(MY_CALLBACKS) == 4
        assert set(MY_CALLBACKS) == {'hyphen', 'plus', 'star', 'default'}

        class HIDDEN_DEFAULT(cbc.CallbackClass):

            @cbc.CallbackClass.default
            @cbc.CallbackClass.ignore
            def default(arg):
                pass

            def hyphen(arg):
                return "-{arg}-".format(arg=arg)

        assert 'default' not in HIDDEN_DEFAULT
        assert HIDDEN_DEFAULT['hyphen'] is HIDDEN_DEFAULT.hyphen
        assert HIDDEN_DEFAULT['non-existant'] is HIDDEN_DEFAULT.default

        with pytest.raises(TypeError):
            class BAD_CALLBACKS(cbc.CallbackClass):

                @cbc.CallbackClass.default
                def default_one():
                    pass

                @cbc.CallbackClass.default
                def default_two():
                    pass

    def test_iteration_methods(self):
        class MY_CALLBACKS(cbc.CallbackClass):

            def hyphen(arg):
                return "-{arg}-".format(arg=arg)

            def plus(arg):
                return "+{arg}+".format(arg=arg)

            def star(arg):
                return "*{arg}*".format(arg=arg)

        assert set(MY_CALLBACKS) == set(MY_CALLBACKS.keys())
        assert set(zip(MY_CALLBACKS, MY_CALLBACKS.values())) == \
            set(MY_CALLBACKS.items())
