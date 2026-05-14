import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from fastapi.testclient import TestClient

from app.core.database import Base, get_db
from app.main import app
from app.models.entity import AgentStatus


TEST_DB_URL = "sqlite:///:memory:"


@pytest.fixture
def db_engine():
    engine = create_engine(
        TEST_DB_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    yield engine
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def db_session(db_engine):
    Session = sessionmaker(autocommit=False, autoflush=False, bind=db_engine)
    session = Session()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def client(db_session):
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


@pytest.fixture
def seed_model(client):
    """创建一个 Model 并返回其数据"""
    res = client.post("/api/v1/models/", json={
        "name": "GPT-4o",
        "provider": "OpenAI",
        "model_type": "chat",
        "version": "2024-08-06",
    })
    return res.json()["data"]


@pytest.fixture
def seed_prompt(client):
    """创建一个 Prompt 并返回其数据"""
    res = client.post("/api/v1/prompts/", json={
        "title": "翻译助手",
        "content": "将以下内容翻译为{language}: {text}",
    })
    return res.json()["data"]


@pytest.fixture
def seed_agent(client, seed_model, seed_prompt):
    """创建一个关联了 Model 和 Prompt 的 DRAFT Agent"""
    res = client.post("/api/v1/agents/", json={
        "name": "翻译智能体",
        "description": "多语言翻译",
        "model_id": seed_model["id"],
        "prompt_id": seed_prompt["id"],
    })
    return res.json()["data"]
