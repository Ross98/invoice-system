from pathlib import Path
import sys

from pydantic_settings import BaseSettings


def _default_env_file() -> str:
    """查找 .env 文件：优先 exe 同级 data/ 目录，其次开发环境当前目录"""
    # PyInstaller 打包后: <exe>/data/.env
    if getattr(sys, "frozen", False):
        exe_dir = Path(sys.executable).parent
        candidate = exe_dir / "data" / ".env"
        if candidate.exists():
            return str(candidate)
    # 开发环境
    candidate = Path(__file__).parent.parent / ".env"
    if candidate.exists():
        return str(candidate)
    return ".env"


class Settings(BaseSettings):
    # 数据库 — 打包后在 data/ 目录下
    DATABASE_URL: str = "sqlite:///./invoice.db"

    # 文件上传
    UPLOAD_DIR: str = "../uploads"
    MAX_FILE_SIZE_MB: int = 10
    STORAGE_THRESHOLD_MB: int = 1  # 小于此值存数据库 BLOB

    # OCR — 留空则自动从 runtime/ 目录查找，或使用系统安装的
    OCR_ENGINE: str = "local"
    TESSERACT_PATH: str = ""
    POPPLER_PATH: str = ""

    # 应用
    APP_TITLE: str = "发票管理系统"
    APP_VERSION: str = "2.0.0"

    # 部署
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    CORS_ORIGINS: str = "*"  # 生产环境改为具体域名，如 "https://invoice.your-domain.com"

    class Config:
        env_file = _default_env_file()

    def _get_base_dir(self) -> Path:
        """获取应用根目录"""
        if getattr(sys, "frozen", False):
            return Path(sys.executable).parent.resolve()
        return Path(__file__).parent.parent.resolve()

    def _get_data_dir(self) -> Path:
        """获取数据目录（打包后为 data/，开发环境为 backend/）"""
        base = self._get_base_dir()
        if getattr(sys, "frozen", False):
            data_dir = base / "data"
            data_dir.mkdir(parents=True, exist_ok=True)
            return data_dir
        return base

    @property
    def upload_dir_path(self) -> Path:
        """获取上传目录的绝对路径"""
        data_dir = self._get_data_dir()
        upload_dir = data_dir / "uploads"
        upload_dir.mkdir(parents=True, exist_ok=True)
        return upload_dir

    @property
    def database_url(self) -> str:
        """获取数据库连接 URL（自动修正为绝对路径）"""
        db_url = self.DATABASE_URL
        if db_url.startswith("sqlite:///./"):
            db_file = db_url[12:]  # 取出 ./invoice.db 部分
            data_dir = self._get_data_dir()
            resolved = (data_dir / db_file).as_posix()
            return f"sqlite:///{resolved}"
        return db_url

    @property
    def max_file_size_bytes(self) -> int:
        return self.MAX_FILE_SIZE_MB * 1024 * 1024

    @property
    def storage_threshold_bytes(self) -> int:
        return self.STORAGE_THRESHOLD_MB * 1024 * 1024


# 全局配置实例
settings = Settings()
