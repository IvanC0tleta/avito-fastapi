from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os


# ПОДКЛЮЧЕНИЕ К БАЗЕ ДАННЫХ
# os.environ["POSTGRES_USERNAME"] = "postgres"
# os.environ["POSTGRES_PASSWORD"] = "1234"
# os.environ["POSTGRES_HOST"] = "localhost"
# os.environ["POSTGRES_PORT"] = "5432"
# os.environ["POSTGRES_DATABASE"] = "postgres"

server_address = os.getenv("SERVER_ADDRESS", "127.0.0.1:8000")
postgres_conn = os.getenv("POSTGRES_CONN")
postgres_jdbc_url = os.getenv("POSTGRES_JDBC_URL")
postgres_username = os.getenv("POSTGRES_USERNAME")
postgres_password = os.getenv("POSTGRES_PASSWORD")
postgres_host = os.getenv("POSTGRES_HOST", "localhost")
postgres_port = os.getenv("POSTGRES_PORT", "5432")
postgres_database = os.getenv("POSTGRES_DATABASE")

SQLALCHEMY_DATABASE_URL = f"postgresql://{postgres_username}:{postgres_password}@{postgres_host}:{postgres_port}/{postgres_database}"
engine = create_engine(SQLALCHEMY_DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
