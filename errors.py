from log import log


class APIError(object):

    def json_error(self):
        return {
            "error": self.msg
        }


class CredentialsError(APIError):

    def __init__(self, msg="Generic Credentials Error"):
        log.error(msg)
        self.msg = msg


class GenericApiError(APIError):

    def __init__(self, msg="Generic API Error"):
        log.error(msg)
        self.msg = msg
