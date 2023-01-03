from typing import Optional
from http import HTTPStatus

from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field

import database.models as models
from database.database import engine
from database.database import SessionLocal

app = FastAPI()

models.Base.metadata.create_all(bind=engine)


def get_db():
    try:
        db = SessionLocal()
        yield db
    finally:
        db.close()


class Todo(BaseModel):
    title: str
    description: Optional[str]
    priority: int = Field(gt=0, ls=6, description="Priority must between 1-5.")
    complete: bool


@app.get("/")
async def read_all(db: Session = Depends(get_db)):
    return db.query(models.Todos).all()


@app.get("/todo/{todo_id}")
async def read_todo(todo_id: int, db: Session = Depends(get_db)):
    todo_model = db.query(models.Todos).filter(models.Todos.id == todo_id).first()
    if todo_model is not None:
        return todo_model
    raise http_notfound_exception()


@app.post("/")
async def create_todo(todo: Todo, db: Session = Depends(get_db)):
    todo_model = models.Todos()
    todo_model.title = todo.title
    todo_model.description = todo.description
    todo_model.priority = todo.priority
    todo_model.complete = todo.complete

    db.add(todo_model)
    db.commit()

    return {
        "status": HTTPStatus.CREATED,
        "transaction": "successful",
    }


@app.put('/{todo_id}')
async def update_todo(todo_id: int, todo: Todo, db: Session = Depends(get_db)):
    todo_model = db.query(models.Todos).filter(models.Todos.id == todo_id).first()

    if todo_model is None:
        raise http_notfound_exception()

    todo_model.title = todo.title
    todo_model.description = todo.description
    todo_model.priority = todo.priority
    todo_model.complete = todo.complete

    db.add(todo_model)
    db.commit()

    return {
        "status": HTTPStatus.OK,
        "transaction": "successful",
    }


@app.delete("/{todo_id}")
async def delete_todo(todo_id: int, db: Session = Depends(get_db)):
    todo_model = db.query(models.Todos).filter(models.Todos.id == todo_id).first()

    if todo_model is None:
        raise http_notfound_exception()

    db.query(models.Todos).filter(models.Todos.id == todo_id).delete()

    db.commit()

    return {
        "status": HTTPStatus.OK,
        "transaction": "successful",
    }


def successful_respond():
    pass


def http_notfound_exception():
    return HTTPException(status_code=HTTPStatus.NOT_FOUND, detail="Item not found.")
