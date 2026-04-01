import json
import os
import sys
from http.server import BaseHTTPRequestHandler, HTTPServer

from models import ChatRequest, ChatResponse
from llm import chat, clear_session
from pydantic import ValidationError

def load_env():
    env_path = os.path.join(os.path.dirname(__file__), ".env")
    if os.path.exists(env_path):
        with open(env_path) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, _, value = line.partition("=")
                    os.environ.setdefault(key.strip(), value.strip())


BASE_DIR = os.path.dirname(os.path.abspath(__file__))


class ChatHandler(BaseHTTPRequestHandler):

    def log_message(self, fmt, *args):
        """Override to suppress noisy default logging."""
        print(f"[{self.address_string()}] {fmt % args}")

    def _send_json(self, data: dict, status: int = 200):
        body = json.dumps(data, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self._cors_headers()
        self.end_headers()
        self.wfile.write(body)

    def _cors_headers(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")

    def do_OPTIONS(self):
        """Handle pre-flight CORS requests."""
        self.send_response(204)
        self._cors_headers()
        self.end_headers()

    def do_GET(self):
        if self.path in ("/", "/index.html"):
            self._serve_file("index.html", "text/html; charset=utf-8")
        else:
            self._send_json({"error": "Not found"}, 404)

    def _serve_file(self, filename: str, content_type: str):
        filepath = os.path.join(BASE_DIR, filename)
        if not os.path.exists(filepath):
            self._send_json({"error": f"{filename} not found"}, 404)
            return
        with open(filepath, "rb") as f:
            body = f.read()
        self.send_response(200)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self._cors_headers()
        self.end_headers()
        self.wfile.write(body)

    def do_POST(self):
        if self.path == "/api/chat":
            self._handle_chat()
        elif self.path == "/api/session/clear":
            self._handle_clear_session()
        else:
            self._send_json({"error": "Not found"}, 404)

    def _handle_chat(self):
        try:
            length = int(self.headers.get("Content-Length", 0))
            raw = self.rfile.read(length)
            data = json.loads(raw.decode("utf-8"))
        except (json.JSONDecodeError, ValueError) as e:
            self._send_json({"error": f"Invalid JSON: {e}"}, 400)
            return

        try:
            req = ChatRequest(**data)
        except ValidationError as e:
            self._send_json({"error": e.errors()}, 422)
            return

        response: ChatResponse = chat(req.session_id, req.message)
        out = response.model_dump(include={"answer", "query", "suggested_questions"})
        self._send_json(out)

    def _handle_clear_session(self):
        try:
            length = int(self.headers.get("Content-Length", 0))
            raw = self.rfile.read(length)
            data = json.loads(raw.decode("utf-8"))
            session_id = data.get("session_id", "")
        except Exception:
            self._send_json({"error": "Invalid request"}, 400)
            return

        clear_session(session_id)
        self._send_json({"status": "ok", "message": f"Session '{session_id}' cleared."})


def run(host: str = "0.0.0.0", port: int = 8000):
    load_env()

    # Validate required environment
    provider = os.environ.get("PROVIDER", "openai").lower()
    if provider == "openai" and not os.environ.get("OPENAI_API_KEY"):
        print("ERROR: OPENAI_API_KEY is not set. Please set it in your .env file or environment.")
        sys.exit(1)
    if provider == "azure" and not os.environ.get("AZURE_OPENAI_API_KEY"):
        print("ERROR: AZURE_OPENAI_API_KEY is not set.")
        sys.exit(1)

    from database import get_db
    get_db()
    from llm import _get_system_prompt
    _get_system_prompt()

    server = HTTPServer((host, port), ChatHandler)
    print(f"Inventory Chatbot running at http://localhost:{port}")

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nServer stopped.")
        server.server_close()


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    run(port=port)
