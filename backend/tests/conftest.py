"""pytest 全局配置 — 提供 path, 把 backend/ 加进 sys.path"""

import sys
from pathlib import Path

# backend/ 加入 import 路径
BACKEND_ROOT = Path(__file__).parent.parent.resolve()
sys.path.insert(0, str(BACKEND_ROOT))