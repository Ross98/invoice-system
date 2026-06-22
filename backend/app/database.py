from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from .config import settings

engine = create_engine(
    settings.database_url,
    connect_args={"check_same_thread": False},  # SQLite 专用
    echo=False,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    pass


def get_db():
    """获取数据库会话的依赖注入"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """创建所有表"""
    Base.metadata.create_all(bind=engine)


def seed_default_categories():
    """插入默认消费分类（如果不存在）

    本函数在启动时调用,内部显式管理 session,与请求级 get_db yield 模式隔离以避免 lifespan 阶段的 session 嵌套。
    """
    from .models.invoice import Category
    defaults = ["打车费", "招待费", "高铁票", "飞机票", "办公用品", "快递"]
    db = SessionLocal()
    try:
        existing = db.query(Category).count()
        if existing == 0:
            for name in defaults:
                db.add(Category(name=name))
            db.commit()
            print(f"已插入 {len(defaults)} 个默认分类: {defaults}")
    finally:
        db.close()
