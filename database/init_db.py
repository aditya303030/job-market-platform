from database.connection import engine
from database.models import Base

def init_db():
    Base.metadata.create_all(bind=engine)
    print("All tables created (or already existed).")

if __name__ == "__main__":
    init_db()