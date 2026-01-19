#!/usr/bin/env python3
"""Simple webhook receiver for Alertmanager that sends macOS notifications."""
from http.server import HTTPServer, BaseHTTPRequestHandler
import json
import subprocess

class AlertHandler(BaseHTTPRequestHandler):
    def do_POST(self):
        content_length = int(self.headers['Content-Length'])
        post_data = self.rfile.read(content_length)
        alerts = json.loads(post_data)

        for alert in alerts.get('alerts', []):
            title = alert.get('labels', {}).get('alertname', 'Alert')
            summary = alert.get('annotations', {}).get('summary', 'No details')
            subprocess.run([
                "osascript", "-e",
                f'display notification "{summary}" with title "Claude Code: {title}"'
            ], capture_output=True)

        self.send_response(200)
        self.end_headers()

    def log_message(self, format, *args):
        pass

if __name__ == '__main__':
    server = HTTPServer(('127.0.0.1', 9099), AlertHandler)
    print("Alert notifier listening on :9099")
    server.serve_forever()
