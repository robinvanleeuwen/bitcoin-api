import simplejson as json

from functools import wraps
from flask import g
from jwt import decode, exceptions
from flask import request

from log import log


def login_required(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        log.debug("Checking token")
        authorization = request.headers.get("authorization", None)
        if not authorization:
            return (
                json.dumps({"error": "no authorization token provided"}),
                403,
                {"Content-type": "application/json"},
            )

        try:
            token = authorization.split(" ")[1]
            resp = decode(token, None, verify=False, algorithms=["HS256"])
            log.info(resp)
            g.user = resp["sub"]
        except exceptions.DecodeError as e:
            return (
                json.dumps({"error": "invalid authorization token"}),
                403,
                {"Content-type": "application/json"},
            )

        return f(*args, **kwargs)

    return wrap
