import os
import pytest
from app import db as _db
from app import create_app


@pytest.fixture(scope='session')
def app():
    """Create and configure a new app instance for each test session."""
    app = create_app(os.environ.get('FLASK_CONFIG', 'testing'))
    with app.app_context():
        yield app
        _db.drop_all()


@pytest.fixture
def client(app, db):
    """Create a test client for the app."""
    with app.test_client() as client:
        with app.app_context():
            yield client


@pytest.fixture(scope='session')
def db(app):
    """Initialize and clean up the database."""
    _db.app = app
    with app.app_context():
        _db.create_all()
        yield _db
        _db.session.remove()
        _db.drop_all()
