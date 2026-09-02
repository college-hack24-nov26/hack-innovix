from flask import Flask

from app import create_app
from app.extensions import db
from app.models import User

app = Flask(__name__)
app = create_app()
