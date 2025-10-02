import tempfile, os
from extensions import db
from models import Contact, HealthRecord, PersonalDetail, Note, Event
from app import app
import pytest

@pytest.fixture
def client():
    db_fd, db_path = tempfile.mkstemp(suffix='.db')
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + db_path
    app.config['TESTING'] = True
    with app.test_client() as client:
        with app.app_context():
            db.create_all()
        yield client
    os.close(db_fd); os.unlink(db_path)

def test_contact_crud(client):
    rv = client.post('/contacts/add', data={'name':'Alice','phone':'9999999'})
    assert rv.status_code in (302, 200)
    with app.app_context():
        c = Contact.query.filter_by(name='Alice').first()
        assert c is not None
