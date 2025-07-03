# run.py
from app import create_app, db
from app.models.user import User
from app.models.file import File, FileShare
import os

app = create_app()

@app.before_first_request
def create_tables():
    db.create_all()

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)