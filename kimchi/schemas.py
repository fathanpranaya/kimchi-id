from pydantic import BaseModel

class TickerBase(BaseModel):
    coin_name: str
    remittance: str
    gopax_price: int
    indodax_price: int
    remittance_rate: float
    kimchi_rate: float

class TickerCreate(TickerBase):
    pass

class Ticker(TickerBase):
    id: int
    
    class Config:
        orm_mode = True