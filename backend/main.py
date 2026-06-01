"""发票管理系统 - FastAPI 主入口"""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pathlib import Path

from app.config import settings
from app.database import init_db, seed_default_categories
from app.resource_path import get_frontend_dir, get_base_dir
from app.routers import invoices, ocr


def _init_app():
    """初始化数据库和种子数据"""
    init_db()
    seed_default_categories()
    print(f"数据库已初始化: {settings.database_url}")
    print(f"上传目录: {settings.upload_dir_path}")
    print(f"前端目录: {get_frontend_dir()}")
    print(f"应用根目录: {get_base_dir()}")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """FastAPI lifespan 事件处理"""
    # 启动时
    _init_app()
    yield
    # 关闭时（暂无清理逻辑）


# 创建 FastAPI 应用
app = FastAPI(
    title=settings.APP_TITLE,
    version=settings.APP_VERSION,
    description="本地部署的企业发票管理系统",
    lifespan=lifespan,
)

# 配置 CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 生产环境应限制
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由
app.include_router(invoices.router)
app.include_router(ocr.router)

# 挂载上传文件目录
uploads_dir = Path(settings.upload_dir_path)
uploads_dir.mkdir(parents=True, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=str(uploads_dir)), name="uploads")

# 挂载静态文件（用于前端 SPA）
frontend_dir = get_frontend_dir()
if frontend_dir.exists():
    # 使用中间件实现 SPA fallback，不干扰 API/文档路由
    from fastapi.responses import FileResponse
    from starlette.types import Scope

    class SPAMiddleware:
        """SPA 静态文件中间件：非 API 路径返回 index.html"""
        def __init__(self, app):
            self.app = app

        async def __call__(self, scope, receive, send):
            if scope["type"] == "http":
                path = scope["path"]
                # API / 文档 / 健康检查路径直接透传
                if path.startswith(("/api", "/docs", "/redoc", "/openapi.json", "/health")):
                    await self.app(scope, receive, send)
                    return
                # 静态资源直接返回文件
                static_path = frontend_dir / path.lstrip("/")
                if static_path.exists() and static_path.is_file():
                    file_response = FileResponse(str(static_path))
                    await file_response(scope, receive, send)
                    return
                # SPA fallback: 返回 index.html
                index_path = frontend_dir / "index.html"
                if index_path.exists():
                    file_response = FileResponse(str(index_path))
                    await file_response(scope, receive, send)
                    return
            await self.app(scope, receive, send)

    app.add_middleware(SPAMiddleware)


@app.get("/")
def read_root():
    """根路径返回欢迎信息"""
    return {
        "app": settings.APP_TITLE,
        "version": settings.APP_VERSION,
        "docs": "/docs",
        "redoc": "/redoc",
    }


@app.get("/health")
def health_check():
    """健康检查端点"""
    return {"status": "healthy"}


if __name__ == "__main__":
    import sys
    import uvicorn
    is_packaged = getattr(sys, "frozen", False)
    if is_packaged:
        # PyInstaller 打包环境：直接传 app 对象（无法通过模块名导入）
        uvicorn.run(
            app,
            host="127.0.0.1",
            port=8000,
            reload=False,
            log_level="info",
        )
    else:
        # 开发环境：支持 reload
        uvicorn.run(
            "main:app",
            host="127.0.0.1",
            port=8000,
            reload=True,
            log_level="info",
        )
