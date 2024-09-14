from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware

from app.Routers import Download, Spokeo

import uvicorn

app = FastAPI()

origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/audios", StaticFiles(directory="audios"), name="audios")

app.include_router(Download.router, prefix="/api/v1")
app.include_router(Spokeo.router, prefix="/api/v1")



@app.get("/check_db_connection")  
async def check_db_connection():
    from database import check_db_connection
    return await check_db_connection()

@app.get("/")
async def health_checker():
    return {"status": "success-download"}

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=7000, reload=True)
