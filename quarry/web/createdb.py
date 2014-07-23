from models import db
from models.user import User

if __name__ == '__main__':
    db.Model.metadata.create_all(db.engine)
