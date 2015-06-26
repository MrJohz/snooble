class CallbackMetaClass(type):

    def __new__(meta, name, supercls, dct):
        if name == 'CallbackClass':
            return super().__new__(meta, name, supercls, dct)

        callbacks = {}

        for key, cb in dct.items():
            if hasattr(cb, 'replacement_key'):
                key = cb.replacement_key
            elif hasattr(cb, 'ignore_cb'):
                continue
            elif key.startswith('_'):
                continue
            elif not callable(cb):
                continue

            callbacks[key] = cb

        dct['_callbacks'] = callbacks
        return super().__new__(meta, name, supercls, dct)

    def __getitem__(cls, key):
        if 'default' in cls._callbacks:
            return cls._callbacks.get(key, cls._callbacks['default'])
        else:
            return cls._callbacks[key]

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
