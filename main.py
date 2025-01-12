from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel, Field
from typing import Optional, Dict
from datetime import datetime, timedelta

app = FastAPI()

class Task(BaseModel):
    id: int = None
    title: str = Field(..., min_length=3, max_length=100)
    description: str = Field(None, max_length=300)
    status: str = Field("do wykonania", pattern="^(do wykonania|w trakcie|zako\u0144czone)$")

class PomodoroSession(BaseModel):
    task_id: int
    start_time: datetime
    end_time: datetime
    completed: bool

tasks = [
    {
        "id": 1,
        "title": "Nauka FastAPI",
        "description": "Przygotować przykładowe API z dokumentacją",
        "status": "TODO",
    }
]

pomodoro_sessions = [
    {
        "task_id": 1,
        "start_time": "2025-01-09T12:00:00",
        "end_time": "2025-01-09T12:25:00",
        "completed": True,
    }
]

active_timers: Dict[int, datetime] = {}

@app.get("/")
def read_root():
    return {"Zadanie": "Specjalistyczne oprogramowanie narzędziowe"}

@app.post("/tasks")
def add_task(task: Task):
    if any(existing_task["title"] == task.title for existing_task in tasks):
        raise HTTPException(status_code=400, detail="Tytuł musi być unikalny.")
    task.id = max(task["id"] for task in tasks) + 1 if tasks else 1
    tasks.append(task.dict())
    return task

@app.get("/tasks")
def show_tasks(status: Optional[str] = Query(None, regex="^(do wykonania|w trakcie|zako\u0144czone)$")):
    if status:
        return [task for task in tasks if task["status"] == status]
    return tasks

@app.get("/tasks/{task_id}")
def get_task_by_id(task_id: int):
    task = next((task for task in tasks if task["id"] == task_id), None)
    if not task:
        raise HTTPException(status_code=404, detail="Nie znaleziono zadania")
    return task

@app.put("/tasks/{task_id}")
def update_task(task_id: int, updated_task: Task):
    for task in tasks:
        if task["id"] == task_id:
            if updated_task.title and any(existing_task["title"] == updated_task.title and existing_task["id"] != task_id for existing_task in tasks):
                raise HTTPException(status_code=400, detail="Tytuł musi być unikalny.")
            task["title"] = updated_task.title or task["title"]
            task["description"] = updated_task.description or task["description"]
            task["status"] = updated_task.status or task["status"]
            return task
    raise HTTPException(status_code=404, detail="Nie znaleziono zadania")

@app.delete("/tasks/{task_id}")
def delete_task(task_id: int):
    for task in tasks:
        if task["id"] == task_id:
            tasks.remove(task)
            return {"detail": "Zadanie usunięte"}
    raise HTTPException(status_code=404, detail="Nie znaleziono zadania")

@app.post("/pomodoro")
def create_pomodoro(task_id: int):
    task = next((task for task in tasks if task["id"] == task_id), None)
    if not task:
        raise HTTPException(status_code=404, detail="Nie znaleziono zadania")
    if task_id in active_timers:
        raise HTTPException(status_code=400, detail="Aktywny timer już istnieje dla tego zadania.")

    start_time = datetime.now()
    end_time = start_time + timedelta(minutes=25)
    active_timers[task_id] = end_time
    return {"task_id": task_id, "start_time": start_time, "end_time": end_time}

@app.post("/pomodoro/{task_id}/stop")
def stop_pomodoro(task_id: int):
    if task_id not in active_timers:
        raise HTTPException(status_code=400, detail="Brak aktywnego timera dla tego zadania.")

    start_time = datetime.now() - timedelta(minutes=25)
    end_time = datetime.now()
    pomodoro_sessions.append({
        "task_id": task_id,
        "start_time": start_time.isoformat(),
        "end_time": end_time.isoformat(),
        "completed": True
    })
    del active_timers[task_id]
    return {"detail": "Timer zatrzymany"}

@app.get("/pomodoro/stats")
def get_pomodoro_stats():
    stats = {}
    total_time = timedelta()

    for session in pomodoro_sessions:
        task_id = session["task_id"]
        start_time = datetime.fromisoformat(session["start_time"])
        end_time = datetime.fromisoformat(session["end_time"])
        duration = end_time - start_time
        total_time += duration
        if task_id not in stats:
            stats[task_id] = {"count": 0, "total_time": timedelta()}
        stats[task_id]["count"] += 1
        stats[task_id]["total_time"] += duration

    return {
        "task_stats": stats,
        "total_time_spent": total_time
    }