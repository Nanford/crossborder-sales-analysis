from pydantic import BaseModel
from typing import List, Optional, Dict, Any

class UploadResponse(BaseModel):
    message: str

class ProductAnalysis(BaseModel):
    sku: str
    product_name: str
    value: float

class ComparisonAnalysis(BaseModel):
    sku: str
    product_name: str
    current_value: float
    previous_value: float
    change_rate: float

class CountryAnalysis(BaseModel):
    country: str
    value: float
    percent: float
    previous_value: float
    change_rate: float

class PlatformComparison(BaseModel):
    current_amount: float
    previous_amount: float
    amount_change_rate: Optional[float] = None
    current_volume: float
    previous_volume: float
    volume_change_rate: Optional[float] = None
    current_orders: int
    previous_orders: int
    orders_change_rate: Optional[float] = None
    current_profit_rate: Optional[float] = None
    previous_profit_rate: Optional[float] = None
    profit_rate_change: Optional[float] = None

class SalespersonComparison(BaseModel):
    sales_person: str
    current_amount: float
    previous_amount: float
    amount_change_rate: Optional[float] = None
    current_volume: float
    previous_volume: float
    volume_change_rate: Optional[float] = None
    current_orders: int
    previous_orders: int
    orders_change_rate: Optional[float] = None
    current_profit_rate: Optional[float] = None
    previous_profit_rate: Optional[float] = None
    profit_rate_change: Optional[float] = None

class AIAnalysis(BaseModel):
    analysis: str 