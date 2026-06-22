"""测试 app.routers.settings.require_admin 的鉴权逻辑
- BUG #7/8 修复: /api/settings/reset 与 /backup 强制鉴权

策略: 直接测试 require_admin 函数,不通过 TestClient (避免 lifespan 副作用)
"""

from unittest.mock import MagicMock, patch

import pytest
from fastapi import HTTPException


class TestRequireAdminNoTokenConfigured:
    """未设置 ADMIN_TOKEN 时: 本地兼容,不强制"""

    def test_no_token_no_request_token_passes(self):
        """本地环境: ADMIN_TOKEN=None 时即使不传任何 token 也通过"""
        from app.routers.settings import require_admin

        with patch("app.routers.settings.app_settings") as mock_settings:
            mock_settings.ADMIN_TOKEN = None
            # 无 header 无 query, 应直接通过不抛异常
            result = require_admin(x_admin_token=None, token=None)
            assert result is None

    def test_no_token_with_random_request_passes(self):
        """本地环境: 即使传了无效 token 也通过 (因为没强制)"""
        from app.routers.settings import require_admin

        with patch("app.routers.settings.app_settings") as mock_settings:
            mock_settings.ADMIN_TOKEN = None
            result = require_admin(x_admin_token="anything", token="anything")
            assert result is None


class TestRequireAdminWithTokenConfigured:
    """设置 ADMIN_TOKEN 后: 强制鉴权"""

    def test_no_token_returns_401(self):
        """核心安全测试: 设了 token 后无 token 必须 401"""
        from app.routers.settings import require_admin

        with patch("app.routers.settings.app_settings") as mock_settings:
            mock_settings.ADMIN_TOKEN = "secret-token-xyz"
            with pytest.raises(HTTPException) as exc:
                require_admin(x_admin_token=None, token=None)
            assert exc.value.status_code == 401

    def test_wrong_header_token_returns_401(self):
        from app.routers.settings import require_admin

        with patch("app.routers.settings.app_settings") as mock_settings:
            mock_settings.ADMIN_TOKEN = "secret-token-xyz"
            with pytest.raises(HTTPException) as exc:
                require_admin(x_admin_token="wrong", token=None)
            assert exc.value.status_code == 401

    def test_wrong_query_token_returns_401(self):
        from app.routers.settings import require_admin

        with patch("app.routers.settings.app_settings") as mock_settings:
            mock_settings.ADMIN_TOKEN = "secret-token-xyz"
            with pytest.raises(HTTPException) as exc:
                require_admin(x_admin_token=None, token="wrong")
            assert exc.value.status_code == 401

    def test_correct_header_token_passes(self):
        """正确 token 通过 Header 传入: 应通过"""
        from app.routers.settings import require_admin

        with patch("app.routers.settings.app_settings") as mock_settings:
            mock_settings.ADMIN_TOKEN = "secret-token-xyz"
            result = require_admin(x_admin_token="secret-token-xyz", token=None)
            assert result is None

    def test_correct_query_token_passes(self):
        """正确 token 通过 Query 传入: 应通过"""
        from app.routers.settings import require_admin

        with patch("app.routers.settings.app_settings") as mock_settings:
            mock_settings.ADMIN_TOKEN = "secret-token-xyz"
            result = require_admin(x_admin_token=None, token="secret-token-xyz")
            assert result is None

    def test_header_takes_priority_over_query(self):
        """Header 优先于 query (Header 优先)"""
        from app.routers.settings import require_admin

        with patch("app.routers.settings.app_settings") as mock_settings:
            mock_settings.ADMIN_TOKEN = "secret-token-xyz"
            # Header 错 + Query 对: 应失败 (因为 header 优先)
            with pytest.raises(HTTPException) as exc:
                require_admin(x_admin_token="wrong", token="secret-token-xyz")
            assert exc.value.status_code == 401


class TestRequireAdminUsesConstantTimeCompare:
    """防御时序攻击: 必须用 compare_digest"""

    def test_uses_secrets_compare_digest(self):
        """回归测试: 不应直接用 == 比较 token (会泄露长度信息)"""
        import inspect
        from app.routers.settings import require_admin

        source = inspect.getsource(require_admin)
        assert "compare_digest" in source, "必须用 secrets.compare_digest 防时序攻击"
        assert "==" not in source.split("compare_digest")[1], "compare_digest 后不应再用 =="