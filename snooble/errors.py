class SnoobleError(ValueError):
    pass

class RedditError(SnoobleError):

    def __init__(self, arg, response=None):
        super().__init__(self, arg)
        self.response = response
