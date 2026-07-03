import os
from contextlib import contextmanager

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
  raise RuntimeError(
        "DATABASE_URL is not set. Copy .env.example to .env and fill in your values."
  )

engine = create_engine(
    DATABASE_URL,
    echo=False,
    future=True,
    pool_pre_ping=True,   # checks the connection is alive before using it
    pool_recycle=300,     # recycles connections every 5 mins (300 secs) so the pooler never closes one under us
)

SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)


@contextmanager
def get_session():
    session: Session = SessionLocal()
    try:
        yield session
    finally:
        session.close()