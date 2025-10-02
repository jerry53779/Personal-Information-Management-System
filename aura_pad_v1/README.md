# AuraPad — Personal Info Management (Flask + SQLite)

## Setup
python -m venv .venv

# Windows
.venv\Scripts\activate

# Linux / macOS
source .venv/bin/activate

pip install -r requirements.txt

## Run
python app.py

then open http://127.0.0.1:5000

Notes:
- Default DB path is: sqlite:////C:/Users/Jerry/Desktop/DBMS PROJECT/personal_info.db
- To use a relative DB, edit app.config['SQLALCHEMY_DATABASE_URI'] in app.py or set env var AURAPAD_DB_URI to 'sqlite:///personal_info.db'
