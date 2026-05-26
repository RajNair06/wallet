from fastapi import Depends,APIRouter,status,HTTPException,Query
from sqlalchemy.ext.asyncio import AsyncSession
from db.session import get_session
from dependencies.auth import get_current_user
from db.models import User,Wallet,Transaction,TransactionType
from sqlmodel import select
from schemas.transaction import DepositWithdrawRequest,TransferRequest
from sqlalchemy.orm import aliased
from sqlalchemy import or_


router = APIRouter(prefix="/transaction", tags=["transaction"])

@router.patch(path="/withdraw")
async def transaction(
    payload:DepositWithdrawRequest,
    session: AsyncSession = Depends(get_session),
    user: User = Depends(get_current_user)
):
    if payload.amount<=0:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,detail="withdrawal amount must be greater than zero")
    query=select(Wallet).where(Wallet.user_id==user.id)
    result=await session.execute(query)
    existing_wallet=result.scalar_one_or_none()
    if not existing_wallet:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="A wallet doesn't exist for the user."
            )
    if payload.amount>existing_wallet.balance:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Insufficient Balance"
            )
    if existing_wallet.currency != payload.currency:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Currency mismatch with your wallet."
        )
    existing_wallet.balance=existing_wallet.balance-payload.amount
    transaction=Transaction(from_wallet_id=existing_wallet.id,amount=payload.amount,currency=existing_wallet.currency,transaction_type=TransactionType.WITHDRAWAL)
    session.add(transaction)
    await session.commit()
    await session.refresh(existing_wallet)
    
    return {
        "wallet_id":existing_wallet.id,"amount":payload.amount,"current_balance":existing_wallet.balance
        }


@router.patch(path="/deposit")
async def deposit_transaction(
    payload: DepositWithdrawRequest,
    session: AsyncSession = Depends(get_session),
    user: User = Depends(get_current_user)
):
    if payload.amount <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Deposit amount must be greater than zero"
        )
        
    query = select(Wallet).where(Wallet.user_id == user.id)
    result = await session.execute(query)
    existing_wallet = result.scalar_one_or_none()
    
    if not existing_wallet:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="A wallet doesn't exist for the user."
        )
    if existing_wallet.currency != payload.currency:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Currency mismatch with your wallet."
        )
        
    # Add money to the balance
    existing_wallet.balance = existing_wallet.balance + payload.amount
    
    # Create log: assigned to to_wallet_id
    transaction = Transaction(
        to_wallet_id=existing_wallet.id,
        from_wallet_id=None,  # External source
        amount=payload.amount,
        currency=existing_wallet.currency,
        transaction_type=TransactionType.DEPOSIT
    )
    
    session.add(transaction)
    await session.commit()
    await session.refresh(existing_wallet)
    
    return {
        "wallet_id": existing_wallet.id,
        "amount": payload.amount,
        "current_balance": existing_wallet.balance
    }


@router.patch(path="/transfer")
async def transfer_transaction(
    payload: TransferRequest,
    session: AsyncSession = Depends(get_session),
    user: User = Depends(get_current_user)
):
    if payload.amount <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Transfer amount must be greater than zero"
        )
        
    # 1. Fetch sender's wallet
    sender_query = select(Wallet).where(Wallet.user_id == user.id)
    sender_result = await session.execute(sender_query)
    existing_wallet = sender_result.scalar_one_or_none()
    
    if not existing_wallet:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Your wallet doesn't exist."
        )
        
    # Prevent transferring to oneself
    if existing_wallet.id == payload.to_account_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot transfer money to your own wallet."
        )
        
    if payload.amount > existing_wallet.balance:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Insufficient Balance"
        )
        
    # 2. Fetch receiver's wallet using the target ID from payload
    receiver_query = select(Wallet).where(Wallet.id == payload.to_account_id)
    receiver_result = await session.execute(receiver_query)
    receiver_wallet = receiver_result.scalar_one_or_none()
    
    if not receiver_wallet:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Recipient wallet not found."
        )
        
    # Optional: Currency match verification
    if existing_wallet.currency != payload.currency:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Currency mismatch with your wallet."
        )
        
    # 3. Perform the balance swap
    existing_wallet.balance = existing_wallet.balance - payload.amount
    receiver_wallet.balance = receiver_wallet.balance + payload.amount
    
    # 4. Create log: from_wallet_id is sender, to_wallet_id is payload target
    transaction = Transaction(
        from_wallet_id=existing_wallet.id,
        to_wallet_id=payload.to_account_id,
        amount=payload.amount,
        currency=existing_wallet.currency,
        transaction_type=TransactionType.TRANSFER
    )
    
    session.add(transaction)
    await session.commit()
    await session.refresh(existing_wallet)
    
    return {
        "wallet_id": existing_wallet.id,
        "recipient_wallet_id": payload.to_account_id,
        "amount": payload.amount,
        "current_balance": existing_wallet.balance
    }


@router.get(path="/history")
async def deposit_transaction(limit:int=Query(default=10,ge=1,le=100),offset:int=Query(default=0,ge=0),
    session: AsyncSession = Depends(get_session),
    user: User = Depends(get_current_user)
):
    wallet_query=select(Wallet.id).where(Wallet.user_id==user.id)
    wallet_result=await session.execute(wallet_query)
    user_wallet_id=wallet_result.scalar_one_or_none()
    if not user_wallet_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="wallet not found")
    SenderWallet=aliased(Wallet)
    SenderUser=aliased(User)
    ReceiverWallet=aliased(Wallet)
    ReceiverUser=aliased(User)
    history_query=(select(Transaction.id,Transaction.amount,Transaction.currency,Transaction.transaction_type,Transaction.created_at,(SenderUser.first_name+ " "+ SenderUser.last_name).label("sender_name"),(ReceiverUser.first_name+ " "+ ReceiverUser.last_name).label("receiver_name")).outerjoin(SenderWallet, Transaction.from_wallet_id == SenderWallet.id).outerjoin(SenderUser, SenderWallet.user_id == SenderUser.id).outerjoin(ReceiverWallet, Transaction.to_wallet_id == ReceiverWallet.id).outerjoin(ReceiverUser, ReceiverWallet.user_id == ReceiverUser.id).where(or_(Transaction.from_wallet_id == user_wallet_id,Transaction.to_wallet_id == user_wallet_id)).order_by(Transaction.created_at.desc()).limit(limit).offset(offset) )

    result=await session.execute(history_query)
    transactions_list = []
    for row in result.all():
        transactions_list.append({
            "id": row.id,
            "amount": row.amount,
            "currency": row.currency,
            "type": row.transaction_type,
            "date": row.created_at,
            "sender": row.sender_name if row.sender_name and row.sender_name.strip() else "External Source",
            "receiver": row.receiver_name if row.receiver_name and row.receiver_name.strip() else "External Destination"
        })
        
    return {
        "transactions": transactions_list,
        "limit": limit,
        "offset": offset
    }

    
    




    



    

    



