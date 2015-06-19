What's In This Folder?
======================

I often look through other people's code, usually for guidance on how to implement things
that I know they must have implemented, but also out of general interest.  Eventually I
get to a folder like this where all of the files have fairly cryptic names, that make
perfect sense if you know what they're used for, but the usage can't necessarily be
deduced from the name alone.  Hence this document, which discusses what each file contains
as well as some of the patterns files might use.

This should not be considered documentation, and may well be out-of-date and useless at
any point in time, but if you're interested in the code itself, it might be occasionally
helpful.


\_\_init\_\_.py
---------------
This contains the main ``Snooble`` class that drives much of the operation.  As a rule,
most of usable operations such as getting and posting data, and authenticating the user
are defined and implemented here.


errors.py
---------
This file contains definitions for any custom error classes that might be used in the
codebase, to ensure that all exceptions have a strict and clear hierarchy.  The choice
between using a standard exception and a custom exception is difficult, in general I've
used Python's own exceptions for errors that look like bad programming, and custom
exceptions in places where the error is more likely to come from malformed user input.


oauth.py
--------
This file contains two classes (``OAuth`` and ``Authorization``) that represent the
current state of authentication at any point during snooble's usage.  ``OAuth`` is the
general class that carries all the details needed to make an authorization request to
Reddit's servers.  If that authorization request has been successful, it'll also have an
``Authorization`` instance attached to it that contains the response from that
authorization request, used to make authorized calls to the rest of Reddit's API.


ratelimit.py
------------
Reddit's API access is ratelimited, this implements some amount of compliance with that.
It principally contains a ``RateLimiter`` class that uses the basic idea of refilling
buckets to limit access to the ``take`` method, implementing pauses by sleeping for as
long as it takes.  There are no guarantees that this will work well enough in a
multi-threaded environment at the moment.

This file also contains a ``_LimitationObject`` class, which is a horrifically hacky way
of forcing an object's methods and attributes to comply with ratelimits.  It is created
using the ``limitate`` object of the ``RateLimiter`` class.  It's used in the ``Snooble``
class to limit access to a requests session without needing to constantly be checking the
ratelimit.  It should work generally okay with methods, not so well with attributes.


response.py
-----------
This file contains the classes that are returned when a Reddit API call is made.  They
should be as lightweight and simple as possible for most operations (basically just thin
wrappers around the stored data dictionary) but there is some differentiation made
between different types, and a handful of helper methods in various places.


utils.py
--------
This file contains functions that are needed in two or three different places, and
therefore fall under a fairly general "rule of three" idea, and so have been factored out
as much as possible.  Currently these include:

* ``fetch_parameter`` - Because ``OAuth`` has a lot of parameters that are only needed
  some of the time, it makes sense to just use **kwargs, and force all of the arguments
  to be explicitly stated.  This function, given a dictionary, will pop out the value
  that corresponds to a particular argument, or raise a TypeError complaining about the
  need for that value if it can't get at it.  Note that the dictionary will be mutated -
  this can be useful if you want to check at the end that all of the arguments were used.
  (I don't necessarily, but I have used that feature elsewhere.)

* ``strlist`` - Python strings are iterable, which is useful, but means that if you want
  to accept either a list of strings, or a single string, you need to be a bit clever
  about it.  This method checks isinstance to determine if it is a string, so is hidden
  here so I can pretend that I'm still ducktyping all the way, and also so that it can
  be made Py2/Py3 compatible fairly easily
