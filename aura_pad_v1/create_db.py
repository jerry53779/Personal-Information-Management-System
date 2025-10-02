from app import app
from extensions import db
with app.app_context():
    db.create_all()
    print('DB created (if not exists)')
