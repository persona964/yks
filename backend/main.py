from fastapi import FastAPI, HTTPException, Depends, Query
from sqlalchemy.orm import Session
from datetime import date
from typing import List, Optional

from .db import Base, engine, get_db
from . import models

Base.metadata.create_all(bind=engine)

app = FastAPI()

# Pydantic schemas
from pydantic import BaseModel

class TopicCreate(BaseModel):
    name: str
    parent_id: Optional[int] = None

class SessionCreate(BaseModel):
    date: date
    topic_id: int
    q_total: int
    q_correct: int

class StudyCreate(BaseModel):
    date: date
    topic_id: int
    minutes: int


class StatsResponse(BaseModel):
    accuracy: Optional[float]
    studyTime: int
    progress: Optional[float]


# Utility to build tree
from collections import defaultdict

def build_tree(topics: List[models.Topic]):
    children = defaultdict(list)
    lookup = {}
    for t in topics:
        lookup[t.id] = {"id": t.id, "name": t.name, "children": []}
        children[t.parent_id].append(t.id)
    def build(node_id):
        node = lookup[node_id]
        for child_id in children.get(node_id, []):
            node["children"].append(build(child_id))
        return node
    return [build(cid) for cid in children[None]]


@app.post('/topics')
def create_topic(topic: TopicCreate, db: Session = Depends(get_db)):
    t = models.Topic(name=topic.name, parent_id=topic.parent_id)
    db.add(t)
    db.commit()
    db.refresh(t)
    return {"id": t.id, "name": t.name, "parent_id": t.parent_id}

@app.get('/topics')
def get_topics(db: Session = Depends(get_db)):
    topics = db.query(models.Topic).all()
    return build_tree(topics)

@app.post('/sessions')
def create_session(s: SessionCreate, db: Session = Depends(get_db)):
    if s.q_correct > s.q_total:
        raise HTTPException(400, 'q_correct cannot exceed q_total')
    if s.date > date.today():
        raise HTTPException(400, 'future date not allowed')
    sess = models.Session(date=s.date, topic_id=s.topic_id,
                         questions_total=s.q_total,
                         questions_correct=s.q_correct)
    db.add(sess)
    db.commit()
    db.refresh(sess)
    return {"id": sess.id}

@app.get('/sessions')
def list_sessions(topic_id: int, from_date: date, to_date: date, db: Session = Depends(get_db)):
    rows = db.query(models.Session).filter(
        models.Session.topic_id == topic_id,
        models.Session.date.between(from_date, to_date)
    ).all()
    return [
        {"date": r.date, "q_total": r.questions_total, "q_correct": r.questions_correct}
        for r in rows
    ]

@app.post('/study')
def create_study(s: StudyCreate, db: Session = Depends(get_db)):
    if s.date > date.today():
        raise HTTPException(400, 'future date not allowed')
    log = models.StudyLog(date=s.date, topic_id=s.topic_id, minutes=s.minutes)
    db.add(log)
    db.commit()
    db.refresh(log)
    return {"id": log.id}

@app.get('/stats')
def get_stats(topic_id: int, from_date: date, to_date: date, db: Session = Depends(get_db)):
    # gather subtree ids (simplified: only topic itself)
    # TODO include descendants
    base = db.query(models.Session).filter(
        models.Session.topic_id == topic_id,
        models.Session.date.between(from_date, to_date)
    )
    correct = sum(r.questions_correct for r in base)
    total = sum(r.questions_total for r in base)

    study = db.query(models.StudyLog).filter(
        models.StudyLog.topic_id == topic_id,
        models.StudyLog.date.between(from_date, to_date)
    )
    mins = sum(r.minutes for r in study)

    accuracy = (correct / total) if total else None
    # Progress is simple average for now
    progress = None
    if accuracy is not None:
        progress = (accuracy + min(mins / 60.0, 1.0)) / 2  # TODO weighting

    return StatsResponse(accuracy=accuracy, studyTime=mins, progress=progress)
