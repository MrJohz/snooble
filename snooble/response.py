try:
    from collections.abc import Mapping
except ImportError:
    from collections import Mapping


class Response(Mapping):

    def __init__(self, data):
        self._json = data
        self.data = self._json['data']

    def __getitem__(self, item):
        return self.data[item]

    def __iter__(self):
        return iter(self.data)

    def __len__(self):
        return len(self.data)


class Listing(Response):

    def __init__(self, data):
        super().__init__(self, data)
