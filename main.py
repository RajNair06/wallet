from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from db.session import init_db
from routers.auth import router as auth_router
from routers.users import router as users_router
from routers.wallet import router as wallet_router
from routers.transaction import router as transaction_router
from middleware.idempotency import CustomMiddleWare

templates = Jinja2Templates(directory="templates")






async def lifespan(app: FastAPI):
    await init_db()
    yield


app = FastAPI(lifespan=lifespan)
app.add_middleware(CustomMiddleWare)
app.include_router(auth_router)
app.include_router(users_router)
app.include_router(wallet_router)
app.include_router(transaction_router)


@app.get("/", response_class=HTMLResponse)
def read_root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

