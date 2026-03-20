"""命令行测试：调用 Agent 并打印 messages 全部项。

用法：
  uv run python test.py OpenClaw是什么
  # 或
  python3 test.py OpenClaw是什么
"""

from __future__ import annotations

import json
import sys
import uuid
from pathlib import Path
from typing import Any


def _ensure_import_path() -> None:
    here = Path(__file__).resolve().parent
    if str(here) not in sys.path:
        sys.path.insert(0, str(here))


def _pretty(obj: Any) -> str:
    try:
        return json.dumps(obj, ensure_ascii=False, indent=2)
    except Exception:
        return repr(obj)


def main() -> int:
    _ensure_import_path()

    if len(sys.argv) < 2:
        print("用法：python3 test.py <问题>  例如：python3 test.py OpenClaw是什么")
        return 2

    query = " ".join(sys.argv[1:]).strip()
    if not query:
        print("问题不能为空")
        return 2

    from agent import create_my_agent

    agent = create_my_agent(model_id=None)
    thread_id = f"test-{uuid.uuid4().hex[:8]}"
    config = {"configurable": {"thread_id": thread_id}}

    result = agent.invoke({"messages": [("user", query)]}, config=config)
    messages = result.get("messages", [])

    try:
        for i, msg in enumerate(messages):
            cls_name = msg.__class__.__name__ if hasattr(msg, "__class__") else type(msg).__name__
            msg_type = getattr(msg, "type", None)
            content = getattr(msg, "content", None)

            print(f"\n{'='*20} message[{i}] {cls_name} {'='*20}")
            if msg_type is not None:
                print("type:", msg_type)

            if content is not None:
                print("content:\n", content)
            else:
                print("raw:\n", _pretty(msg))

            tool_calls = getattr(msg, "tool_calls", None)
            if tool_calls:
                print("tool_calls:\n", _pretty(tool_calls))
    except BrokenPipeError:
        # 当输出被管道截断（例如 `| head`）时，避免报错堆栈影响查看
        return 0

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
