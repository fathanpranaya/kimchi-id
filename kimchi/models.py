import datetime
from sqlalchemy import Boolean, Column, ForeignKey, Integer, String, Float, DateTime
from sqlalchemy.orm import relationship
from .database import Base

# class Coin(Base):
#     __tablename__ = "coin"

#     id = Column(Integer, primary_key=True, index=True)
#     name = Column(String)
#     code = Column(String, unique=True, index=True)
#     trf_fee = Column(Float, default=0)

class Ticker(Base):
    __tablename__ = "tickers"

    id = Column(Integer, primary_key=True, index=True)
    coin_name = Column(String, index=True)
    remittance = Column(String, index=True)
    
    gopax_price = Column(integer)
    indodax_price = Column(integer)

    remittance_rate = Column(float)
    kimchi_rate = Column(float)

    created_date = Column(DateTime, default=datetime.datetime.utcnow)
