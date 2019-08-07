#!/usr/bin/env python3
# manage.py

from flask_script import Manager
from flask_migrate import Migrate, MigrateCommand
from app import app
from db import db, models

migrate = Migrate(app, db)
manager = Manager(app)

manager.add_command("db", MigrateCommand)

if __name__ == "__main__":
    manager.run()
