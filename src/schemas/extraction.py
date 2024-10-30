from pydantic import BaseModel, Field
from schemas.market import TradeSymbol


class ExtractionYield(BaseModel):
    symbol: TradeSymbol
    units: int


class Extraction(BaseModel):
    shipSymbol: str
    yield_field: ExtractionYield = Field(alias='yield')