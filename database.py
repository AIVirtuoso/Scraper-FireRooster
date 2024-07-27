import os
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from fastapi import FastAPI, Depends
from schema import Base
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

host = os.getenv("MYSQL_HOST")
user = os.getenv("MYSQL_USER")
password = os.getenv("MYSQL_PASSWORD")
database = os.getenv("MYSQL_DATABASE")

# MySQL connection needs an escaped password string if there are special characters.
escaped_password = password.replace('+', '%2B').replace(':', '%3A')

DATABASE_URI = f"mysql+aiomysql://{user}:{escaped_password}@{host}/{database}"

# Create asynchronous engine and session
engine = create_async_engine(DATABASE_URI, echo=True, pool_size=30)
AsyncSessionLocal = sessionmaker(
    engine, expire_on_commit=False, class_=AsyncSession
)

async def create_tables():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)