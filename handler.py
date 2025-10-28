import base64
import os
import subprocess
import time
from logging import INFO, basicConfig, getLogger
from typing import Any

import requests
import runpod

# Configure logging for better visibility in Runpod logs
basicConfig(level=INFO)
logger = getLogger(__name__)


def start_server() -> tuple[subprocess.Popen[bytes], str, int]:
    """Starts the Uvicorn server for Speaches in a background subprocess."""
    host = os.getenv("UVICORN_HOST", "127.0.0.1")
    port = int(os.getenv("UVICORN_PORT", "8000"))

    logger.info("Starting Speaches server...")
    # Command to start the FastAPI application using uvicorn
    command = [
        "uvicorn", "speaches.main:app",
        "--host", host,
        "--port", str(port)
    ]
    # Start the server as a subprocess
    server_process = subprocess.Popen(command)
    logger.info(f"Speaches server process started with PID: {server_process.pid}")
    return server_process, host, port


# Start the server once when the worker initializes
server_process, SERVER_HOST, SERVER_PORT = start_server()


def is_server_ready(host: str, port: int, retries: int = 12, delay: int = 5) -> bool:
    """Checks if the background server is ready to accept connections."""
    url = f"http://{host}:{port}/health"
    for i in range(retries):
        try:
            response = requests.get(url, timeout=5)
            if response.status_code == 200:
                logger.info("Speaches server is ready.")
                return True
        except requests.exceptions.RequestException:
            logger.warning(f"Server not ready yet (attempt {i+1}/{retries}). Retrying in {delay}s...")
            time.sleep(delay)
    logger.error("Server failed to start in the allocated time.")
    return False


# Wait for the server to be ready before starting the handler
SERVER_IS_READY = is_server_ready(SERVER_HOST, SERVER_PORT)


def handler(event: dict[str, Any]) -> dict[str, Any]:
    """Handles incoming requests from Runpod, proxies them to the local Speaches server.

    Returns the response from the server.
    """
    if not SERVER_IS_READY:
        return {"error": {"message": "Server is not running or failed to start."}}

    job_input = event.get("input", {})

    method = job_input.get("method", "GET").upper()
    path = job_input.get("path", "/")
    headers = job_input.get("headers", {})
    body = job_input.get("body", {})
    file_url = job_input.get("file_url")

    url = f"http://{SERVER_HOST}:{SERVER_PORT}{path}"
    logger.info(f"Proxying request: {method} {url}")

    try:
        files_data = None
        data_payload = None

        # Handle file uploads (for STT) by downloading from the provided URL
        if file_url:
            with requests.get(file_url, stream=True, timeout=300) as r:
                r.raise_for_status()
                files_data = {"file": ("audio_file", r.content)}
                data_payload = dict(body)

        # Make the request to the local server
        if method == "POST" and files_data:
             response = requests.post(url, files=files_data, data=data_payload, headers=headers, timeout=300)
        else:
             response = requests.request(method, url, json=body, headers=headers, timeout=120)

        response.raise_for_status()

        content_type = response.headers.get("Content-Type", "")

        if "application/json" in content_type:
            return response.json()
        elif "audio" in content_type:
            # Base64 encode audio to return it in the JSON response
            audio_bytes = response.content
            encoded_audio = base64.b64encode(audio_bytes).decode("utf-8")
            return {
                "status": "success",
                "content_type": content_type,
                "audio_content": encoded_audio
            }
        else:
            return response.text()

    except requests.exceptions.HTTPError as e:
        logger.exception(f"HTTP Error: {e.response.status_code} - {e.response.text}")
        return {
            "error": {
                "message": f"Request to speaches server failed with status {e.response.status_code}",
                "details": e.response.text
            }
        }
    except requests.exceptions.RequestException:
        logger.exception("Request Exception")
        return {"error": {"message": "Failed to connect to speaches server"}}


# Start the Runpod serverless worker
if __name__ == "__main__":
    if SERVER_IS_READY:
        logger.info("Starting Runpod serverless handler.")
        runpod.serverless.start({"handler": handler})
    else:
        logger.critical("Cannot start Runpod handler because Speaches server is not ready.")