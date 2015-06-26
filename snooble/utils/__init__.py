def fetch_parameter(kwargs, param):
    """Fetch a parameter from a keyword-argument dict

    Specifically for use in enforcing "stricter" typing for functions or methods that
    use **kwargs to allow for different sets of arguments.
    """
    try:
        return kwargs.pop(param)
    except KeyError:
        raise TypeError('Missing keyword argument {param}'.format(param=param))


def assign_parameters(obj, kwargs, params):
    """Assign keyword parameters to an object

    Given an object, a dict of keyword-arguments, and an iterable of required parameters,
    this method will fetch each parameter using fetch_parameter, and set it on the object.
    """
    for param in params:
        setattr(obj, param, fetch_parameter(kwargs, param))


def strlist(list_or_string):
    """Converts a string into a list of strings, returns any other input

    Specifically typechecks the str type, so it will only work on strings that subclass
    that.  But what other types of strings are you using?
    """
    if isinstance(list_or_string, str):
        return [list_or_string]
    else:
        return list_or_string
