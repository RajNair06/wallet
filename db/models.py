from sqlmodel import SQLModel, Field
from typing import Optional
from datetime  import datetime
from sqlalchemy import Column, Integer, String, DateTime, CheckConstraint, func
from enum import Enum
class TransactionType(str, Enum):
    WITHDRAWAL = "withdrawal"
    DEPOSIT = "deposit"
    TRANSFER = "transfer"





class User(SQLModel, table=True):
    __tablename__ = "user"
    id: Optional[int] = Field(default=None, primary_key=True)
    first_name: str
    last_name: str
    email: str = Field(index=True, unique=True)
    hashed_password: str

class Wallet(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id", unique=True,ondelete="CASCADE")
    balance: int = Field(
        default=0,
        sa_column=Column(Integer, CheckConstraint("balance >= 0"), nullable=False)
    )
    created_at: Optional[datetime] = Field(
        default=None,
        sa_column=Column(DateTime, server_default=func.now(), nullable=False)
    )
    updated_at: Optional[datetime] = Field(
        default=None,
        sa_column=Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)
    )
    
    currency: str = Field(max_length=3)


class Transaction(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    from_wallet_id: int | None = Field(foreign_key="wallet.id",default=None)
    to_wallet_id: int| None = Field(foreign_key="wallet.id",default=None)
    amount: int = Field(
        default=0,
        sa_column=Column(Integer, CheckConstraint("amount >= 0"), nullable=False)
    )
    transaction_type: TransactionType
    
    currency: str = Field(max_length=3)
    created_at: Optional[datetime] = Field(
        default=None,
        sa_column=Column(DateTime, server_default=func.now(), nullable=False)
    )