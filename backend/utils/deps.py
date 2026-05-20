from sqlmodel import Session
from app.db import engine
from typing import Generator

def get_db() -> Generator[Session, None, None]:
    db = Session(engine)
    try:
        yield db
    except Exception as e:
        db.rollback()
        raise e
    finally:
        db.close()