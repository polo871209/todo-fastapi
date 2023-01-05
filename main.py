import uvicorn
from fastapi import FastAPI

import database.models as models
from database.database import engine
from routers import auth, todos

app = FastAPI()
app.include_router(auth.router)
app.include_router(todos.router)

models.Base.metadata.create_all(bind=engine)

if __name__ == "__main__":
    uvicorn.run("main:app", port=8080, reload=True)
