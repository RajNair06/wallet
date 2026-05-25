from fastapi import APIRouter,Depends,HTTPException,status
from sqlmodel.ext.asyncio.session import AsyncSession
from db.session import get_session
from dependencies.auth import get_current_user
from db.models import User,Wallet
from schemas.wallet import WalletCreate,WalletResponse
from sqlmodel import select

router = APIRouter(prefix="/wallet", tags=["wallet"])

@router.post(path="",response_model=WalletResponse)
async def create_wallet(wallet:WalletCreate,session:AsyncSession=Depends(get_session),user:User=Depends(get_current_user)):
    wallet=Wallet(user_id=user.id,balance=wallet.balance,currency=wallet.currency)
    query=select(Wallet).where(Wallet.user_id==user.id)
    result=await session.exec(query)
    existing_wallet=result.first()
    if existing_wallet:
         raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A wallet already exists for this user."
        )
    new_wallet = Wallet(user_id=user.id, balance=wallet.balance, currency=wallet.currency.upper())
    session.add(new_wallet)
    await session.commit()
    await session.refresh(new_wallet)
    
    return new_wallet

@router.delete(path="")
async def delete_wallet(session:AsyncSession=Depends(get_session),user:User=Depends(get_current_user)):
     query=select(Wallet).where(Wallet.user_id==user.id)
     result=await session.exec(query)
     existing_wallet=result.first()
     if not existing_wallet:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="A wallet doesn't exist for the user."
            )
     
     user_name=f"{user.first_name} {user.last_name}"
     await session.delete(existing_wallet)
     await session.commit()
     return {
         "message":f"wallet belonging to {user_name} deleted successfully"
     }


@router.get(path="")
async def get_wallet(session:AsyncSession=Depends(get_session),user:User=Depends(get_current_user)):
     query=select(Wallet).where(Wallet.user_id==user.id)
     result=await session.exec(query)
     existing_wallet=result.first()
     if not existing_wallet:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="A wallet doesn't exist for the user."
            )
     
     user_name=f"{user.first_name} {user.last_name}"
    
     return {
         **existing_wallet.model_dump(),
         "full name":f"{user_name}"
     }
