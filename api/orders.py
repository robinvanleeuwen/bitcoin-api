from flask import Blueprint
from auth import LoginManager

login_manager = LoginManager()

orders = Blueprint("orders", __name__)
