from datetime import datetime
from uuid import uuid4

import simplejson as json
from functools import wraps
from flask import request, g
from sqlalchemy import and_

from log import log
from db import db
from db.models import Users, Tokens


class LoginManager(object):

    def token_required(self, f):

        @wraps(f)
        def wrapper(*args, **kwargs):
            print(request.data)
            token = request.data.get('token', False)
            username = request.data.get("username", False)
            log.debug(token)
            log.debug(username)
            if not token or not username:
                return {"error": "not authenticated!"}

            validation = self.validate_token(token, username)

            if validation == "expired":
                return {"error": "token expired"}

            if validation == "invalid":
                return {"error": "not authenticated"}

            if validation == "valid":
                return f(*args, **kwargs)

        return wrapper

    def validate_token(self, token, username):

        record = db.session().query(Tokens).join(Users, Users.name == username).filter(
                Tokens.token == token
        ).one_or_none()

        if record is None:
            log.debug("Invalid token")
            return "invalid"

        if record.ttl_max is None:
            log.debug("Invalid token, ttl_max is None")
            return "expired"

        if datetime.now() > record.ttl_max:
            log.debug(f"Token expired (was valid until: {record.ttl_max}), removing token.")
            self.logout()
            return "expired"

        try:
            record.timestamp = datetime.now()
            db.session().commit()
        except Exception as e:
            log.error(f"Could not update token: {e}")
            return "invalid"

        log.debug("Token Valid")
        return "valid"

    @staticmethod
    def logout():

        token = request.data.get('token', False)
        username = request.data.get("username", False)

        record = db.session().query(Tokens).join(Users, Users.name == username).filter(
                Tokens.token == token
        ).one_or_none()

        if record is None:
            return False

        try:
            log.debug(f"Removing token '{token}' for user '{username}'")
            db.session().delete(record)
            db.session().commit()
            return True
        except Exception as e:
            log.error(f"{e}")
            return False

    def login(self):
        username = request.data.get("username", False)
        password = request.data.get("password", False)

        log.debug(f"username: {username}")
        log.debug(f"password: {password}")

        if not username or not password:
            return {"error": "invalid credentials"}

        user = db.session().query(Users).filter(
            and_(
                Users.name == username,
                Users.password == password
            )
        ).one_or_none()

        if not user:
            return {"error": "invalid credentials"}

        else:
            token = Tokens()
            token.ttl_max = "2021-12-12 12:00:00"
            token.token = self.generate_token()
            token.user = user
            token.timestamp = datetime.now()
            token.ttl_increment = 60
            try:
                db.session().add(token)
                db.session().commit()
                return {"token": token.token}
            except Exception as e:
                log.error(f"Could not create token: {e}")
                return {"error": "could not create token"}

    @staticmethod
    def generate_token():
        return uuid4()






