import pytest

from app import create_app
from app.config import TestingConfig
from app.extensions import db
from app.models import User


@pytest.fixture()
def client():
    app = create_app(TestingConfig)
    with app.app_context():
        db.create_all()
        admin = User(email="admin@test.local", full_name="Admin", role="admin")
        admin.set_password("secret123")
        db.session.add(admin)
        db.session.commit()
        yield app.test_client()
        db.session.remove()
        db.drop_all()
