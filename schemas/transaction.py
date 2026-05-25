from pydantic import BaseModel,Field

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

