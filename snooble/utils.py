def fetch_parameter(kwargs, param):
    """Fetch a parameter from a keyword-argument dict

    Specifically for use in enforcing "stricter" typing for functions or methods that
    use **kwargs to allow for different sets of arguments.
    """
    try:
        return kwargs.pop(param)
    except KeyError:
        raise TypeError('Missing keyword argument {param}'.format(param=param))


def strlist(list_or_string):
    """Converts a string into a list of strings, returns any other input

    Specifically typechecks the str type, so it will only work on strings that subclass
    that.  But what other types of strings are you using?
    """
    if isinstance(list_or_string, str):
        return [list_or_string]
    else:
        return list_or_string
