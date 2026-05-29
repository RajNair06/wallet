import os
from dotenv import load_dotenv

load_dotenv()
class Config:
    SECRET_KEY =os.getenv("SECRET_KEY")
    ALGORITHM = os.getenv("ALGORITHM")
    ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES"))
    DATABASE_URL=os.getenv("DATABASE_URL")
    REDIS_URL=os.getenv("REDIS_URL")
    BREVO_API_KEY=os.getenv("BREVO_API_KEY")
    SENDER_MAIL=os.getenv("SENDER_MAIL")
    SENDER_NAME=os.getenv("SENDER_NAME")