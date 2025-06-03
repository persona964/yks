from sqlalchemy import Column, Integer, Text, Date, ForeignKey
from sqlalchemy.orm import relationship
from .db import Base

class Topic(Base):
    __tablename__ = 'topic'
    id = Column(Integer, primary_key=True)
    name = Column(Text, nullable=False)
    parent_id = Column(Integer, ForeignKey('topic.id'), nullable=True, index=True)
    children = relationship('Topic')

class Session(Base):
    __tablename__ = 'session'
    id = Column(Integer, primary_key=True)
    date = Column(Date, nullable=False, index=True)
    topic_id = Column(Integer, ForeignKey('topic.id'), nullable=False, index=True)
    questions_total = Column(Integer, nullable=False)
    questions_correct = Column(Integer, nullable=False)

class StudyLog(Base):
    __tablename__ = 'studylog'
    id = Column(Integer, primary_key=True)
    date = Column(Date, nullable=False, index=True)
    topic_id = Column(Integer, ForeignKey('topic.id'), nullable=False, index=True)
    minutes = Column(Integer, nullable=False)
