from sqlalchemy.orm import SessionLocal
from . import models, schemas

def get_ticker(db: Session, coin_name: str, limit: int = 1000):
    return db.query(models.Ticker).filter(models.Ticker.coin_name == coin_name).order_by(models.Ticker.id.desc()).limit(limit).all()

def create_ticker(db: Session, ticker: schemas.TickerCreate):
    db_ticker = models.Ticker(**ticker.dict())
    db.add(db_ticker)
    db.commit()
    db.refresh(db_ticker)
    return db_ticker