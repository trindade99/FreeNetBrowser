import http.server
import os
from urllib.parse import unquote

class RobustFileHandler(http.server.BaseHTTPRequestHandler):
    def __init__(self, *args, directory=None, **kwargs):
        self.directory = directory or os.getcwd()
        # Set protocol version to HTTP/1.0 for simpler handling
        self.protocol_version = 'HTTP/1.0'
        super().__init__(*args, **kwargs)

    def log_message(self, format, *args):
        """Redirect server logs to our debug system"""

    def do_GET(self):
        try:
            # Immediate connection check
            if not self.wfile:
                return

            # Parse path
            path = unquote(self.path.lstrip('/'))
            if not path or path == '/':
                path = 'index.html'

            file_path = os.path.join(self.directory, path)
            # Check file exists
            if not os.path.exists(file_path):
                self.send_simple_error(404, "File not found")
                return

            # Read file
            try:
                with open(file_path, 'rb') as f:
                    content = f.read()
            except Exception as e:
                self.send_simple_error(500, f"Cannot read file: {e}")
                return

            # Send response
            self.send_simple_response(content, path)

        except Exception as e:
            import traceback
            print(e)

    def send_simple_response(self, content, filename):
        """Send response with proper error handling"""
        try:
            # Check connection before each step
            if not self.wfile:
                return

            # Send status
            self.send_response(200)

            # Determine content type
            content_type = 'text/html; charset=utf-8'
            if filename.endswith('.css'):
                content_type = 'text/css'
            elif filename.endswith('.js'):
                content_type = 'application/javascript'
            elif filename.endswith(('.png', '.jpg', '.jpeg')):
                content_type = 'image/jpeg'

            # Send headers
            self.send_header('Content-Type', content_type)
            self.send_header('Content-Length', str(len(content)))
            self.send_header('Connection', 'close')
            self.end_headers()

            # Check connection again before writing
            if self.wfile:
                self.wfile.write(content)
                self.wfile.flush()

        except (BrokenPipeError, ConnectionResetError, ConnectionAbortedError) as e:
            print(e)
        except Exception as e:
            print(e)

    def send_simple_error(self, code, message):
        """Send error response safely"""
        try:
            if self.wfile:
                self.send_response(code)
                self.send_header('Content-Type', 'text/html')
                self.end_headers()
                self.wfile.write(f"<html><body><h1>Error {code}</h1><p>{message}</p></body></html>".encode())
                self.wfile.flush()
        except:
            print(f"Failed to send error response")
