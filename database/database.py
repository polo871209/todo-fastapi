import os

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base

from dotenv import load_dotenv, find_dotenv

load_dotenv(find_dotenv())

POSTGRES_PASSWORD = os.environ['POSTGRES_PASSWORD']

SQLALCHEMY_DATABASE_URL = f"postgresql://postgres:{POSTGRES_PASSWORD}@localhost/todo-app-db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()
