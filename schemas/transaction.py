from pydantic import BaseModel,Field
from datetime import datetime
from typing import Optional

class DepositWithdrawRequest(BaseModel):
    amount:int=Field(...,ge=0)
    currency:str=Field(...,min_length=3, max_length=3)

class TransferRequest(BaseModel):
    amount:int=Field(...,ge=0)
    currency:str=Field(...,min_length=3, max_length=3)
    to_account_id:int

class WithdrawResponse(BaseModel):
    wallet_id:int
    amount:int
    current_balance:int

class LedgerEntryResponse(BaseModel):
    id:int
    transaction_id:int
    wallet_id:Optional[int]=None
    entry_type:str
    amount:int
    currency:str
    balance_snapshot:Optional[int]=None
    created_at:datetime

    class Config:
        from_attributes=True

