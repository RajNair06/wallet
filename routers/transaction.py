from fastapi import Depends, APIRouter, status, HTTPException, Query, Header
from sqlalchemy.ext.asyncio import AsyncSession
from db.session import get_session
from dependencies.auth import get_current_user
from db.models import User, Wallet, Transaction, TransactionType, LedgerEntry, EntryType
from sqlmodel import select
from schemas.transaction import DepositWithdrawRequest, TransferRequest, LedgerEntryResponse
from sqlalchemy.orm import aliased
from sqlalchemy import or_
from workers import mail_reciept
from core.limiter import sensitive_txn_limiter,deposit_limiter

router = APIRouter(prefix="/transaction", tags=["transaction"])


@router.patch(path="/withdraw",dependencies=[Depends(sensitive_txn_limiter)])
async def withdraw(
    payload: DepositWithdrawRequest,
    x_idempotency_key: str = Header(..., alias="X-Idempotency-Key"),
    session: AsyncSession = Depends(get_session),
    user: User = Depends(get_current_user),
):
    if payload.amount <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Withdrawal amount must be greater than zero",
        )
    query = select(Wallet).where(Wallet.user_id == user.id)
    result = await session.execute(query)
    existing_wallet = result.scalar_one_or_none()
    if not existing_wallet:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="A wallet doesn't exist for the user.",
        )
    if payload.amount > existing_wallet.balance:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Insufficient Balance",
        )
    if existing_wallet.currency != payload.currency:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Currency mismatch with your wallet.",
        )

    existing_wallet.balance = existing_wallet.balance - payload.amount
    transaction = Transaction(
        from_wallet_id=existing_wallet.id,
        amount=payload.amount,
        currency=existing_wallet.currency,
        transaction_type=TransactionType.WITHDRAWAL,
    )
    session.add(transaction)
    await session.flush()

    debit_entry = LedgerEntry(
        transaction_id=transaction.id,
        wallet_id=existing_wallet.id,
        entry_type=EntryType.DEBIT,
        amount=payload.amount,
        currency=existing_wallet.currency,
        balance_snapshot=existing_wallet.balance,
    )
    credit_entry = LedgerEntry(
        transaction_id=transaction.id,
        wallet_id=None,
        entry_type=EntryType.CREDIT,
        amount=payload.amount,
        currency=existing_wallet.currency,
        balance_snapshot=None,
    )
    session.add_all([debit_entry, credit_entry])

    user_email = user.email
    await session.commit()
    await session.refresh(transaction)
    await session.refresh(existing_wallet)
    mail_reciept.send(
        transaction_id=transaction.id,
        usr_mail=user_email,
        amount=payload.amount,
        txn_type=TransactionType.WITHDRAWAL.value,
        from_wallet_id=existing_wallet.id,
        to_wallet_id=None,
        currency=transaction.currency,
        current_balance=existing_wallet.balance,
    )
    return {
        "wallet_id": existing_wallet.id,
        "amount": payload.amount,
        "current_balance": existing_wallet.balance,
    }


@router.patch(path="/deposit",dependencies=[Depends(deposit_limiter)])
async def deposit_transaction(
    payload: DepositWithdrawRequest,
    x_idempotency_key: str = Header(..., alias="X-Idempotency-Key"),
    session: AsyncSession = Depends(get_session),
    user: User = Depends(get_current_user),
):
    if payload.amount <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Deposit amount must be greater than zero",
        )

    query = select(Wallet).where(Wallet.user_id == user.id)
    result = await session.execute(query)
    existing_wallet = result.scalar_one_or_none()

    if not existing_wallet:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="A wallet doesn't exist for the user.",
        )
    if existing_wallet.currency != payload.currency:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Currency mismatch with your wallet.",
        )

    existing_wallet.balance = existing_wallet.balance + payload.amount

    transaction = Transaction(
        to_wallet_id=existing_wallet.id,
        from_wallet_id=None,
        amount=payload.amount,
        currency=existing_wallet.currency,
        transaction_type=TransactionType.DEPOSIT,
    )
    session.add(transaction)
    await session.flush()

    debit_entry = LedgerEntry(
        transaction_id=transaction.id,
        wallet_id=None,
        entry_type=EntryType.DEBIT,
        amount=payload.amount,
        currency=existing_wallet.currency,
        balance_snapshot=None,
    )
    credit_entry = LedgerEntry(
        transaction_id=transaction.id,
        wallet_id=existing_wallet.id,
        entry_type=EntryType.CREDIT,
        amount=payload.amount,
        currency=existing_wallet.currency,
        balance_snapshot=existing_wallet.balance,
    )
    session.add_all([debit_entry, credit_entry])

    user_email = user.email
    await session.commit()
    await session.refresh(transaction)
    await session.refresh(existing_wallet)
    mail_reciept.send(
        transaction_id=transaction.id,
        usr_mail=user_email,
        amount=payload.amount,
        txn_type=TransactionType.DEPOSIT.value,
        from_wallet_id=None,
        to_wallet_id=existing_wallet.id,
        currency=transaction.currency,
        current_balance=existing_wallet.balance,
    )

    return {
        "wallet_id": existing_wallet.id,
        "amount": payload.amount,
        "current_balance": existing_wallet.balance,
    }


@router.patch(path="/transfer",dependencies=[Depends(sensitive_txn_limiter)])
async def transfer_transaction(
    payload: TransferRequest,
    x_idempotency_key: str = Header(..., alias="X-Idempotency-Key"),
    session: AsyncSession = Depends(get_session),
    user: User = Depends(get_current_user),
):
    if payload.amount <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Transfer amount must be greater than zero",
        )

    sender_query = select(Wallet).where(Wallet.user_id == user.id)
    sender_result = await session.execute(sender_query)
    existing_wallet = sender_result.scalar_one_or_none()

    if not existing_wallet:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Your wallet doesn't exist.",
        )

    if existing_wallet.id == payload.to_account_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot transfer money to your own wallet.",
        )

    if payload.amount > existing_wallet.balance:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Insufficient Balance",
        )

    receiver_query = select(Wallet).where(Wallet.id == payload.to_account_id)
    receiver_result = await session.execute(receiver_query)
    receiver_wallet = receiver_result.scalar_one_or_none()

    if not receiver_wallet:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Recipient wallet not found.",
        )

    if existing_wallet.currency != payload.currency:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Currency mismatch with your wallet.",
        )

    existing_wallet.balance = existing_wallet.balance - payload.amount
    receiver_wallet.balance = receiver_wallet.balance + payload.amount

    transaction = Transaction(
        from_wallet_id=existing_wallet.id,
        to_wallet_id=payload.to_account_id,
        amount=payload.amount,
        currency=existing_wallet.currency,
        transaction_type=TransactionType.TRANSFER,
    )
    session.add(transaction)
    await session.flush()

    debit_entry = LedgerEntry(
        transaction_id=transaction.id,
        wallet_id=existing_wallet.id,
        entry_type=EntryType.DEBIT,
        amount=payload.amount,
        currency=existing_wallet.currency,
        balance_snapshot=existing_wallet.balance,
    )
    credit_entry = LedgerEntry(
        transaction_id=transaction.id,
        wallet_id=receiver_wallet.id,
        entry_type=EntryType.CREDIT,
        amount=payload.amount,
        currency=existing_wallet.currency,
        balance_snapshot=receiver_wallet.balance,
    )
    session.add_all([debit_entry, credit_entry])

    user_email = user.email
    reciever_user_query = select(User).where(User.id == receiver_wallet.user_id)
    reciever_user_result = await session.execute(reciever_user_query)
    reciever_user_result = reciever_user_result.scalar_one_or_none()
    reciever_full_name = f"{reciever_user_result.first_name} {reciever_user_result.last_name}"

    await session.commit()
    await session.refresh(existing_wallet)
    await session.refresh(transaction)
    mail_reciept.send(
        transaction_id=transaction.id,
        usr_mail=user_email,
        amount=payload.amount,
        txn_type=TransactionType.TRANSFER.value,
        from_wallet_id=existing_wallet.id,
        to_wallet_id=payload.to_account_id,
        currency=transaction.currency,
        current_balance=existing_wallet.balance,
        reciever_name=reciever_full_name,
    )
    return {
        "wallet_id": existing_wallet.id,
        "recipient_wallet_id": payload.to_account_id,
        "amount": payload.amount,
        "current_balance": existing_wallet.balance,
    }


@router.get(path="/history")
async def history(
    limit: int = Query(default=10, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    session: AsyncSession = Depends(get_session),
    user: User = Depends(get_current_user),
):
    wallet_query = select(Wallet.id).where(Wallet.user_id == user.id)
    wallet_result = await session.execute(wallet_query)
    user_wallet_id = wallet_result.scalar_one_or_none()
    if not user_wallet_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="wallet not found"
        )
    SenderWallet = aliased(Wallet)
    SenderUser = aliased(User)
    ReceiverWallet = aliased(Wallet)
    ReceiverUser = aliased(User)
    history_query = (
        select(
            Transaction.id,
            Transaction.amount,
            Transaction.currency,
            Transaction.transaction_type,
            Transaction.created_at,
            (SenderUser.first_name + " " + SenderUser.last_name).label("sender_name"),
            (ReceiverUser.first_name + " " + ReceiverUser.last_name).label(
                "receiver_name"
            ),
        )
        .outerjoin(SenderWallet, Transaction.from_wallet_id == SenderWallet.id)
        .outerjoin(SenderUser, SenderWallet.user_id == SenderUser.id)
        .outerjoin(ReceiverWallet, Transaction.to_wallet_id == ReceiverWallet.id)
        .outerjoin(ReceiverUser, ReceiverWallet.user_id == ReceiverUser.id)
        .where(
            or_(
                Transaction.from_wallet_id == user_wallet_id,
                Transaction.to_wallet_id == user_wallet_id,
            )
        )
        .order_by(Transaction.created_at.desc())
        .limit(limit)
        .offset(offset)
    )

    result = await session.execute(history_query)
    transactions_list = []
    for row in result.all():
        transactions_list.append(
            {
                "id": row.id,
                "amount": row.amount,
                "currency": row.currency,
                "type": row.transaction_type,
                "date": row.created_at,
                "sender": row.sender_name
                if row.sender_name and row.sender_name.strip()
                else "External Source",
                "receiver": row.receiver_name
                if row.receiver_name and row.receiver_name.strip()
                else "External Destination",
            }
        )

    return {"transactions": transactions_list, "limit": limit, "offset": offset}


@router.get(path="/{transaction_id}/ledger", response_model=list[LedgerEntryResponse])
async def get_transaction_ledger(
    transaction_id: int,
    session: AsyncSession = Depends(get_session),
    user: User = Depends(get_current_user),
):
    wallet_query = select(Wallet.id).where(Wallet.user_id == user.id)
    wallet_result = await session.execute(wallet_query)
    user_wallet_id = wallet_result.scalar_one_or_none()
    if not user_wallet_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Wallet not found"
        )

    txn_query = select(Transaction).where(Transaction.id == transaction_id)
    txn_result = await session.execute(txn_query)
    transaction = txn_result.scalar_one_or_none()
    if not transaction:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Transaction not found"
        )
    if (
        transaction.from_wallet_id != user_wallet_id
        and transaction.to_wallet_id != user_wallet_id
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only view ledger entries for your own transactions",
        )

    ledger_query = select(LedgerEntry).where(
        LedgerEntry.transaction_id == transaction_id
    )
    ledger_result = await session.execute(ledger_query)
    return ledger_result.scalars().all()

    
    




    



    

    



