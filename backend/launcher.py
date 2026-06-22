"""发票管理系统 — 启动器
独立进程：启动服务后端 → 健康检测 → 自动打开浏览器 → 进程守护
"""

import os
import sys
import time
import signal
import subprocess
import urllib.request
import urllib.error
import webbrowser
from pathlib import Path

# ── 配置 ──
SERVER_EXE = "InvoiceSystem.exe"
HEALTH_URL = "http://127.0.0.1:8000/health"
APP_URL = "http://127.0.0.1:8000"
LAUNCHER_PORT = 8000
MAX_WAIT_SECONDS = 30
POLL_INTERVAL = 0.5


def _launcher_dir() -> Path:
    """Launcher.exe 所在目录"""
    if getattr(sys, "frozen", False):
        return Path(sys.executable).parent.resolve()
    return Path(__file__).parent.resolve()


def find_server_exe() -> str:
    """查找服务端可执行文件，找不到则抛出 FileNotFoundError"""
    launcher_dir = _launcher_dir()
    server_path = launcher_dir / SERVER_EXE
    if server_path.exists():
        return str(server_path)

    raise FileNotFoundError(
        f"找不到 {SERVER_EXE}\n"
        f"预期位置: {server_path}\n"
        f"请确保 {SERVER_EXE} 与 Launcher.exe 在同一目录下"
    )


def check_health(timeout: float = 2.0) -> bool:
    """向 /health 端点发 GET 请求，返回是否就绪"""
    try:
        req = urllib.request.Request(HEALTH_URL)
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.status == 200
    except (urllib.error.URLError, ConnectionRefusedError, TimeoutError, OSError):
        return False


def print_banner():
    print()
    print("=" * 52)
    print("   发票管理系统 — Launcher")
    print("=" * 52)
    print()


def main():
    print_banner()

    # 1. 定位服务端
    try:
        server_exe = find_server_exe()
    except FileNotFoundError as e:
        print(f"[错误] {e}")
        print()
        input("按回车键退出...")
        sys.exit(1)

    # 2. 启动服务进程
    print(f"[启动] 正在启动服务端...")
    server_dir = os.path.dirname(server_exe)

    try:
        proc = subprocess.Popen(
            [server_exe],
            cwd=server_dir,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            encoding="utf-8",
            errors="replace",
            creationflags=subprocess.CREATE_NO_WINDOW,
        )
    except Exception as e:
        print(f"[错误] 无法启动 {SERVER_EXE}: {e}")
        print()
        input("按回车键退出...")
        sys.exit(1)

    # 3. 轮询健康检查
    print(f"[等待] 等待服务就绪（最多 {MAX_WAIT_SECONDS}s）...", end="", flush=True)

    start = time.time()
    while time.time() - start < MAX_WAIT_SECONDS:
        # 进程提前退出 → 错误
        if proc.poll() is not None:
            print()
            print(f"[错误] 服务进程意外退出，退出码: {proc.returncode}")

            # 打印服务端输出帮助定位问题
            try:
                remaining = proc.stdout.read()
                if remaining:
                    print()
                    print("── 服务端输出 ──")
                    print(remaining.strip())
                    print("── 输出结束 ──")
            except Exception:
                pass

            print()
            input("按回车键退出...")
            sys.exit(1)

        if check_health():
            elapsed = time.time() - start
            print(f" 就绪！(耗时 {elapsed:.1f}s)")
            print()
            print(f"[打开] 正在打开浏览器: {APP_URL}")
            webbrowser.open_new_tab(APP_URL)
            break

        time.sleep(POLL_INTERVAL)
        sys.stdout.write(".")
        sys.stdout.flush()
    else:
        # 超时
        print()
        print(f"[超时] 服务在 {MAX_WAIT_SECONDS}s 内未能就绪")

        # 打印服务端输出帮助定位问题
        try:
            proc.terminate()
            proc.wait(timeout=5)
            remaining = proc.stdout.read()
            if remaining:
                print()
                print("── 服务端输出 ──")
                print(remaining.strip())
                print("── 输出结束 ──")
        except Exception:
            try:
                proc.kill()
            except Exception:
                pass

        print()
        input("按回车键退出...")
        sys.exit(1)

    # 4. 守护模式 — 等待服务进程退出
    print()
    print("  服务运行中...")
    print(f"  访问地址: {APP_URL}")
    print("  按 Ctrl+C 停止服务")
    print()

    try:
        while True:
            ret = proc.poll()
            if ret is not None:
                print(f"[退出] 服务进程已结束，退出码: {ret}")
                break
            time.sleep(1)
    except KeyboardInterrupt:
        print()
        print("[停止] 正在关闭服务...")
        try:
            proc.terminate()
            proc.wait(timeout=10)
        except subprocess.TimeoutExpired:
            print("[停止] 服务未响应，强制结束...")
            proc.kill()
            proc.wait()
        print("[停止] 服务已关闭")

    print()
    print("再见！")


if __name__ == "__main__":
    main()
