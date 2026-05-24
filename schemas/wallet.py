from pydantic import BaseModel,field_validator
from datetime import datetime

class WalletCreate(BaseModel):
    balance:int
    currency:str

    @field_validator("balance")
    @classmethod
    def validate_balance(cls,v:int):
        if v<0:
            raise ValueError("Balance must be greater than or equal to zero")
        return v
    
    @field_validator("currency")
    @classmethod
    def validate_currency(cls,v:str):
        if len(v)!=3:
            raise ValueError("currency must be exactly 3 characters")
        return v

class WalletResponse(BaseModel):
    id:int
    user_id:int
    balance:int
    created_at:datetime
    currency:str
    
