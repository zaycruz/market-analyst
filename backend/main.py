import json
import http.server
import socketserver
from urllib.parse import urlparse, parse_qs
from datetime import datetime

from backend.config.settings import settings
from backend.agents.orchestrator import Oracle


class OracleHandler(http.server.BaseHTTPRequestHandler):
    oracle = Oracle()

    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path

        if path == "/" or path == "/health":
            self._send_json(
                {
                    "name": settings.app_name,
                    "version": settings.app_version,
                    "status": "running",
                    "timestamp": datetime.now().isoformat(),
                }
            )

        elif path.startswith("/api/reports/daily/"):
            date = path.replace("/api/reports/daily/", "")
            self._get_report("daily", date)

        elif path.startswith("/api/reports/weekly/"):
            date = path.replace("/api/reports/weekly/", "")
            self._get_report("weekly", date)

        elif path == "/api/reports/recent":
            self._get_recent_reports()

        else:
            self._send_json({"error": "Not found"}, 404)

    def do_POST(self):
        parsed = urlparse(self.path)
        path = parsed.path

        if path == "/api/reports/generate/daily":
            self._generate_daily()

        elif path == "/api/research":
            content_length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(content_length).decode("utf-8")
            try:
                data = json.loads(body)
                query = data.get("query", "")
                self._run_research(query)
            except json.JSONDecodeError:
                self._send_json({"error": "Invalid JSON"}, 400)

        else:
            self._send_json({"error": "Not found"}, 404)

    def _send_json(self, data, status=200):
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(json.dumps(data, indent=2).encode("utf-8"))

    def _get_report(self, report_type: str, date: str):
        import os

        filepath = os.path.join(settings.reports_dir, report_type, f"{date}.md")

        if os.path.exists(filepath):
            with open(filepath) as f:
                content = f.read()
            self._send_json({"date": date, "type": report_type, "content": content})
        else:
            self._send_json({"error": f"Report not found: {filepath}"}, 404)

    def _get_recent_reports(self):
        import os

        reports = []

        for report_type in ["daily", "weekly"]:
            report_dir = os.path.join(settings.reports_dir, report_type)
            if os.path.exists(report_dir):
                for filename in sorted(os.listdir(report_dir), reverse=True)[:10]:
                    if filename.endswith(".md"):
                        date = filename.replace(".md", "")
                        reports.append(
                            {
                                "date": date,
                                "type": report_type,
                                "file": os.path.join(report_dir, filename),
                            }
                        )

        self._send_json({"reports": reports, "count": len(reports)})

    def _generate_daily(self):
        try:
            state = self.oracle.run_daily_brief()
            self._send_json(
                {
                    "status": "success",
                    "date": state.date,
                    "thesis": state.thesis,
                    "confidence": state.confidence,
                    "recommendations": len(state.recommendations),
                    "report_file": f"{settings.reports_dir}/daily/{state.date}.md",
                }
            )
        except Exception as e:
            self._send_json({"error": str(e)}, 500)

    def _run_research(self, query: str):
        try:
            state = self.oracle.run_research(query)
            self._send_json(
                {
                    "query": query,
                    "thesis": state.thesis,
                    "confidence": state.confidence,
                    "recommendations": state.recommendations,
                    "sources": state.sources,
                }
            )
        except Exception as e:
            self._send_json({"error": str(e)}, 500)

    def log_message(self, format, *args):
        print(f"[{datetime.now().strftime('%H:%M:%S')}] {args[0]}")


def start_server():
    print(f"""
╔══════════════════════════════════════════════════════════╗
║     ORACLE - Macro Research Agent                        ║
║     Version: {settings.app_version}                                        ║
╠══════════════════════════════════════════════════════════╣
║  API Server running on http://{settings.host}:{settings.port}               ║
║                                                          ║
║  Endpoints:                                              ║
║    GET  /                     - Health check             ║
║    GET  /api/reports/daily/   - Get daily report         ║
║    GET  /api/reports/weekly/  - Get weekly report        ║
║    GET  /api/reports/recent   - List recent reports      ║
║    POST /api/reports/generate/daily - Generate report    ║
║    POST /api/research         - Run research query       ║
║                                                          ║
║  Press Ctrl+C to stop                                    ║
╚══════════════════════════════════════════════════════════╝
""")

    with socketserver.TCPServer((settings.host, settings.port), OracleHandler) as httpd:
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nShutting down server...")
            httpd.shutdown()


if __name__ == "__main__":
    start_server()
