from fastapi import FastAPI

from db.session import init_db
from routers.auth import router as auth_router
from routers.users import router as users_router
from routers.wallet import router as wallet_router
from routers.transaction import router as transaction_router


async def lifespan(app: FastAPI):
    await init_db()
    yield


app = FastAPI(lifespan=lifespan)
app.include_router(auth_router)
app.include_router(users_router)
app.include_router(wallet_router)
app.include_router(transaction_router)


@app.get("/")
def read_root():
    return {"Hello": "World"}

