# app/models/database.py
from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, ForeignKey, JSON, Float
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

Base = declarative_base()

class PromptTemplate(Base):
    __tablename__ = 'prompt_templates'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False)
    description = Column(Text)
    template_content = Column(Text, nullable=False)
    component_type = Column(String(50), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    version = Column(Integer, nullable=False)
    is_active = Column(Boolean, default=True)

class ModelConfig(Base):
    __tablename__ = 'model_configs'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False)
    model_provider = Column(String(50), nullable=False)
    model_name = Column(String(255), nullable=False)
    component_type = Column(String(50), nullable=False)
    system_prompt = Column(Text)
    parameters = Column(JSON)
    created_at = Column(DateTime, default=datetime.utcnow)
    is_active = Column(Boolean, default=True)
    experiment_group = Column(String(50))  # For grouping configs in experiments

class ExperimentResult(Base):
    __tablename__ = 'experiment_results'
    
    id = Column(Integer, primary_key=True)
    question = Column(Text, nullable=False)
    answer = Column(Text, nullable=False)
    model_config_id = Column(Integer, ForeignKey('model_configs.id'))
    score = Column(Float)
    feedback = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)