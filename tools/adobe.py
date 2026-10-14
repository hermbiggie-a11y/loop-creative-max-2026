"""Send one command to Photoshop or Premiere through the adb-mcp proxy (same wire format as the MCP servers).

    uv run --no-project --python 3.13 --with python-socketio --with websocket-client --with requests \
        tools/adobe.py photoshop createDocument '{"name":"x","width":1080,...}' [--timeout 120]

Prints the JSON response. Exit 1 on FAILURE.
"""
import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "adb-mcp", "mcp"))
import socket_client  # noqa: E402


def call(app, action, options=None, timeout=60):
    socket_client.configure(app=app, url="http://localhost:3001", timeout=timeout)
    return socket_client.send_message_blocking({"application": app, "action": action, "options": options or {}})


if __name__ == "__main__":
    args = sys.argv[1:]
    timeout = 60
    if "--timeout" in args:
        i = args.index("--timeout")
        timeout = int(args[i + 1])
        del args[i:i + 2]
    app, action = args[0], args[1]
    opts = json.loads(args[2]) if len(args) > 2 else {}
    try:
        res = call(app, action, opts, timeout)
    except Exception as e:  # AppError / RuntimeError from socket_client
        print(json.dumps({"status": "FAILURE", "message": str(e)}))
        sys.exit(1)
    print(json.dumps(res, default=str)[:20000])
