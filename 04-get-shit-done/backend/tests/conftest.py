"""pytest 测试基础设施 — 提供所有测试文件共用的 fixture。

设计要点：
- in-memory SQLite + StaticPool：保证每个连接都看到同一张内存数据库（否则各连接各自独立）
- function scope：每个测试函数前重建 schema，测试完全隔离
- dependency_overrides[get_db]：TestClient 复用同一 session，避免事务可见性问题
"""

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from fastapi.testclient import TestClient

from app.core.database import Base, get_db
from app.main import app

TEST_DB_URL = "sqlite:///:memory:"


@pytest.fixture
def db_engine():
    """创建 in-memory SQLite 引擎并建表，测试结束后销毁所有表。

    StaticPool 是关键：它让所有连接（包括 TestClient 内部创建的连接）
    共享同一个物理内存数据库，否则每次 connect() 都会得到一个空库。
    """
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
    """提供与 db_engine 绑定的 Session，测试结束后关闭。"""
    Session = sessionmaker(autocommit=False, autoflush=False, bind=db_engine)
    session = Session()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def client(db_session):
    """提供 TestClient，通过 dependency_overrides 将 get_db 替换为共享的 db_session。

    使用 try/finally 而非 yield，确保 session 在整个请求生命周期内保持打开，
    不会在请求中途被关闭导致 DetachedInstanceError。
    """
    def override_get_db():
        try:
            yield db_session
        finally:
            pass  # session 由 db_session fixture 统一管理，此处不关闭

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


@pytest.fixture
def seed_model(client):
    """通过 API 创建一个 Model，返回响应中的 data 对象。"""
    res = client.post(
        "/api/v1/models/",
        json={
            "name": "GPT-4o",
            "provider": "OpenAI",
            "model_type": "chat",
            "version": "2024-08-06",
        },
    )
    return res.json()["data"]


@pytest.fixture
def seed_prompt(client):
    """通过 API 创建一个 Prompt，返回响应中的 data 对象。"""
    res = client.post(
        "/api/v1/prompts/",
        json={
            "title": "翻译助手",
            "content": "将以下内容翻译为{language}: {text}",
        },
    )
    return res.json()["data"]


@pytest.fixture
def seed_agent(client, seed_model, seed_prompt):
    """通过 API 创建一个处于 DRAFT 状态的 Agent（已关联 Model + Prompt）。

    这个 fixture 是激活类测试的标准起点，保证前置条件（有效的 model_id 和 prompt_id）已满足。
    """
    res = client.post(
        "/api/v1/agents/",
        json={
            "name": "翻译智能体",
            "description": "多语言翻译",
            "model_id": seed_model["id"],
            "prompt_id": seed_prompt["id"],
        },
    )
    return res.json()["data"]
