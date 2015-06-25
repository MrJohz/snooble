from .compat import Mapping


class BaseResponse(Mapping):

    def __init__(self, resp, data):
        self.json = resp
        self._data = data

    def __getitem__(self, item):
        return self._data[item]

    def __iter__(self):
        return iter(self._data)

    def __len__(self):
        return len(self._data)


class Response(BaseResponse):

    def __init__(self, resp):
        super().__init__(resp, resp['data'])


class Listing(BaseResponse):

    def __init__(self, resp):
        super().__init__(resp, [create_response(c) for c in resp['data']['children']])


class Subreddit(Response):

    def __init__(self, resp):
        super().__init__(resp)


RESPONSE_TYPES = {
    "Listing": Listing,
    "t5": Subreddit
}


def create_response(resp):
    if 'kind' in resp:
        return RESPONSE_TYPES.get(resp['kind'], Response)(resp)
    else:
        return Response({"data": resp})
