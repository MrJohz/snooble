"""Classes to make writing callback mappings easier.

I tend to write a certain amount of code by writing a number of callback functions that
all recieve the same arguments but do slightly different things, and then making a dict
that maps a key to each function.  That's fine, but I have to write each function down
twice, once when defining it, and once when putting it into the dict.  I also end up with
functions floating all over the place polluting the namespace.  Again, fine, but there
should probably be some better way of doing this.

Example:
    Imagine a situation where a user can select an animal and view a picture of it.  To
    make things (sligtly) more confusing, all of the animal pictures are stored in
    different places, and need different bits of code to access them.  Callbacks (may be)
    the answer (but probably aren't a very good one...)::

        class ANIMAL_TYPE(CallbackClass):

            def platipus():
                return open('platipus_image.jpeg').read()

            def aardvark():
                return requests.get('https://my.site.com/aardvark.png').data

            def elephant():
                return b64encode(elephant_pic_data)

        # (somewhere else)

        animal = input('Pick an animal:')
        animal_image = ANIMAL_TYPE[animal]()

ANIMAL_TYPE will now act as an immutable mapping, where the key for each function is that
function's name.  If no animal is found, a KeyError will be raised.  It may be that your
case is served better by including a default case - to do this simply decorate the default
function definition with ``@CallbackClass.default``.  If you want to add a function that
should not be treated as a callback, use ``@CallbackClass.ignore``.  (This can be applied
to the default case if necessary.)  If you want to use a different key, use
``@CallbackClass.key(new_key)``.  This key doesn't need to be a string, it can be any
hashable type.
"""


class CallbackMetaClass(type):

    def __new__(meta, name, supercls, dct):
        if name == 'CallbackClass':
            return super().__new__(meta, name, supercls, dct)

        callbacks = {}
        default_callback = None

        for key, cb in dct.items():
            if hasattr(cb, 'is_default'):
                if default_callback is not None:
                    raise TypeError("Only one default callback may be registered")
                default_callback = cb

            if hasattr(cb, 'ignore_cb'):
                continue
            elif hasattr(cb, 'replacement_key'):
                key = cb.replacement_key
            elif key.startswith('_'):
                continue
            elif not callable(cb):
                continue

            callbacks[key] = cb

        dct['_callbacks'] = callbacks
        dct['_default_cb'] = default_callback
        return super().__new__(meta, name, supercls, dct)

    def __getitem__(cls, key):
        default = cls._default_cb
        if default is None:
            return cls._callbacks[key]
        else:
            return cls.get(key, default)

    def get(cls, key, default=None):
        return cls._callbacks.get(key, default)

    def __contains__(cls, key):
        return key in cls._callbacks

    def __iter__(cls):
        return iter(cls._callbacks)

    def keys(cls):
        return cls._callbacks.keys()

    def items(cls):
        return cls._callbacks.items()

    def values(cls):
        return cls._callbacks.values()

    def __len__(cls):
        return len(cls._callbacks)


class CallbackClass(object, metaclass=CallbackMetaClass):

    @staticmethod
    def key(name):
        def wrapper(func):
            func.replacement_key = name
            return func
        return wrapper

    @staticmethod
    def ignore(func):
        func.ignore_cb = True
        return func

    @staticmethod
    def default(func):
        func.is_default = True
        return func

    @classmethod
    def add_callback(cls, *args):
        if len(args) == 2:
            # add_callback(string, callback)
            cls._callbacks[args[0]] = args[1]
        elif len(args) == 1 and callable(args[0]):
            # add_callback(callback)
            cls._callbacks[args[0].__name__] = args[0]
        elif len(args) == 1:
            # @add_callback(name)
            def wrapper(func):
                cls._callbacks[args[0]] = func
                return func
            return wrapper
        elif len(args) == 0:
            # @add_callback()
            def wrapper(func):
                cls._callbacks[func.__name__] = func
                return func
            return wrapper
        else:
            raise TypeError("add_callback requires 0, 1, or 2 args, passed " + len(args))
