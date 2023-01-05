from http import HTTPStatus
from typing import Optional

import uvicorn
from fastapi import FastAPI, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

import database.models as models
from auth import get_current_user, get_user_exception
from database.database import engine, SessionLocal

app = FastAPI()

models.Base.metadata.create_all(bind=engine)


class Todo(BaseModel):
    title: str
    description: Optional[str]
    priority: int = Field(gt=0, ls=6, description="Priority must between 1-5.")
    complete: bool


def get_db():
    try:
        db = SessionLocal()
        yield db
    finally:
        db.close()


def http_respond(http_status: HTTPStatus, transaction: str = "successful"):
    return {
        "status": http_status,
        "transaction": transaction,
    }


def http_notfound_exception():
    return HTTPException(status_code=HTTPStatus.NOT_FOUND, detail="Item not found.")


@app.get("/")
async def read_all(db: Session = Depends(get_db)):
    return db.query(models.Todos).all()


@app.get("/todos/user")
async def read_user_todos(user: dict = Depends(get_current_user),
                          db: Session = Depends(get_db)):
    if user is None:
        raise get_user_exception()
    return db.query(models.Todos).filter(models.Todos.owner_id == user.get("id")).all()


@app.get("/todo/{todo_id}")
async def read_todo(todo_id: int,
                    user: dict = Depends(get_current_user),
                    db: Session = Depends(get_db)):
    if user is None:
        raise get_user_exception()

    todo_model = db.query(models.Todos) \
        .filter(models.Todos.id == todo_id) \
        .filter(models.Todos.owner_id == user.get("id")) \
        .first()
    if todo_model is not None:
        return todo_model
    raise http_notfound_exception()


@app.post("/")
async def create_todo(todo: Todo,
                      user: dict = Depends(get_current_user),
                      db: Session = Depends(get_db)):
    if user is None:
        raise get_user_exception()
    todo_model = models.Todos()
    todo_model.title = todo.title
    todo_model.description = todo.description
    todo_model.priority = todo.priority
    todo_model.complete = todo.complete
    todo_model.owner_id = user.get("id")

    db.add(todo_model)
    db.commit()

    return http_respond(HTTPStatus.CREATED)


@app.put('/{todo_id}')
async def update_todo(todo_id: int,
                      todo: Todo,
                      user: dict = Depends(get_current_user),
                      db: Session = Depends(get_db)):
    if user is None:
        raise get_user_exception()

    todo_model = db.query(models.Todos).filter(models.Todos.id == todo_id).first()
    if todo_model is None:
        raise http_notfound_exception()

    todo_model.title = todo.title
    todo_model.description = todo.description
    todo_model.priority = todo.priority
    todo_model.complete = todo.complete
    todo_model.owner_id = user.get("id")

    db.add(todo_model)
    db.commit()

    return http_respond(HTTPStatus.OK)


@app.delete("/{todo_id}")
async def delete_todo(todo_id: int,
                      user: dict = Depends(get_current_user),
                      db: Session = Depends(get_db)):
    if user is None:
        raise get_user_exception()

    todo_model = db.query(models.Todos) \
        .filter(models.Todos.id == todo_id) \
        .filter(models.Todos.owner_id == user.get("id")) \
        .first()
    if todo_model is None:
        raise http_notfound_exception()

    db.query(models.Todos).filter(models.Todos.id == todo_id).delete()
    db.commit()

    return http_respond(HTTPStatus.OK)


if __name__ == "__main__":
    uvicorn.run("main:app", port=8080, reload=True)
