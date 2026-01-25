#!/usr/bin/env python
"""
启动多领域遥感检测 Web 服务

用法:
    python run_web.py [--host HOST] [--port PORT]

示例:
    python run_web.py
    python run_web.py --port 8000
    python run_web.py --host 0.0.0.0 --port 8080
"""
import argparse
import uvicorn


def main():
    parser = argparse.ArgumentParser(description="启动多领域遥感检测 Web 服务")
    parser.add_argument("--host", default="0.0.0.0", help="服务器地址 (默认: 0.0.0.0)")
    parser.add_argument("--port", type=int, default=8080, help="服务器端口 (默认: 8080)")
    parser.add_argument("--reload", action="store_true", help="启用热重载 (开发模式)")

    args = parser.parse_args()

    print(f"""
╔══════════════════════════════════════════════════════════════╗
║           多领域遥感检测系统 - Web 服务                        ║
║      Multi-domain Remote Sensing Detection System            ║
╠══════════════════════════════════════════════════════════════╣
║  服务地址: http://{args.host}:{args.port}
║  API 文档: http://{args.host}:{args.port}/docs
╚══════════════════════════════════════════════════════════════╝
    """)

    uvicorn.run(
        "web.app:app",
        host=args.host,
        port=args.port,
        reload=args.reload
    )


if __name__ == "__main__":
    main()
