from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routers import users, sessions, admin
from fastapi.staticfiles import StaticFiles 


import models
from database import engine

models.Base.metadata.create_all(bind=engine)

app = FastAPI()

origins = ["http://localhost:5173", "http://127.0.0.1:5173"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
   
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(users.router)
app.include_router(sessions.router)
app.include_router(admin.router)
@app.get("/")
def root():
    return {"message": "Knowledge Zakat API is running correctly! "}

app.mount("/static", StaticFiles(directory="static"), name="static")
app.mount("/pics", StaticFiles(directory="pics"), name="pics")

