"""使用 SQLModel 的数据库连接和会话管理"""
from sqlmodel import SQLModel, create_engine, Session
from app.config import settings

engine = create_engine(
    settings.DATABASE_URL,
    echo=False,
    pool_pre_ping=True,
    pool_size=10,
    max_overflow=20,
)


def init_db():
    """初始化数据库：创建所有表"""
    SQLModel.metadata.create_all(engine)


def get_session():
    """获取数据库会话的依赖项"""
    with Session(engine) as session:
        yield session



