import base64
from logging import INFO, basicConfig, getLogger
import os
import subprocess
import time
from typing import Any
from urllib.parse import urljoin

import requests

# Conditional import for runpod since it may not be available in all environments
try:
    import runpod  # type: ignore # noqa: PGH003

    RUNPOD_AVAILABLE = True
except ImportError:
    runpod = None  # type: ignore # noqa: PGH003
    RUNPOD_AVAILABLE = False

# Configure logging for better visibility in Runpod logs
basicConfig(level=INFO)
logger = getLogger(__name__)


def start_server() -> tuple[subprocess.Popen[bytes], str, int]:
    """Starts the Uvicorn server for Speaches in a background subprocess."""
    host = os.getenv("UVICORN_HOST", "127.0.0.1")
    port = int(os.getenv("UVICORN_PORT", "8000"))

    logger.info("Starting Speaches server...")
    # Command to start the FastAPI application using uvicorn
    command = ["uvicorn", "speaches.main:app", "--host", host, "--port", str(port)]
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
            logger.warning(f"Server not ready yet (attempt {i + 1}/{retries}). Retrying in {delay}s...")
            time.sleep(delay)
    logger.error("Server failed to start in the allocated time.")
    return False


# Wait for the server to be ready before starting the handler
SERVER_IS_READY = is_server_ready(SERVER_HOST, SERVER_PORT)


def handler(event: dict[str, Any]) -> dict[str, Any]:
    """Handles incoming requests from Runpod, proxies them to the local Speaches server.

    Supports all Speaches functionalities including:
    - Dynamic model loading (/api/ps endpoints)
    - Model discovery (/v1/registry, /v1/models endpoints)
    - Open WebUI integration (all OpenAI-compatible endpoints)
    - Realtime API functionality (/v1/realtime endpoint)
    - Speech-to-Text processing (/v1/audio/transcriptions endpoint)
    - Text-to-Speech generation (/v1/audio/speech endpoint)
    - Voice Activity Detection (/v1/audio/speech/timestamps endpoint)
    - Voice Chat capabilities (/v1/chat/completions endpoint)

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
    query_params = job_input.get("query_params", {})

    url = f"http://{SERVER_HOST}:{SERVER_PORT}{path}"
    logger.info(f"Proxying request: {method} {url}")

    try:
        files_data = None
        data_payload = None

        # Handle file uploads for various endpoints
        if file_url:
            logger.info(f"Downloading file from URL: {file_url}")
            with requests.get(file_url, stream=True, timeout=300) as r:
                r.raise_for_status()
                files_data = {"file": ("audio_file", r.content)}
                data_payload = dict(body)
        elif method == "POST" and body:
            # For POST requests with body data
            data_payload = dict(body)

        # Make the request to the local server with appropriate method and data
        if method == "GET":
            response = requests.get(url, headers=headers, params=query_params, timeout=120)
        elif method == "POST" and files_data:
            response = requests.post(url, files=files_data, data=data_payload, headers=headers, params=query_params, timeout=300)
        elif method == "POST":
            response = requests.post(url, json=body, headers=headers, params=query_params, timeout=120)
        elif method == "PUT":
            response = requests.put(url, json=body, headers=headers, params=query_params, timeout=120)
        elif method == "DELETE":
            response = requests.delete(url, headers=headers, params=query_params, timeout=120)
        else:
            # For other HTTP methods
            response = requests.request(method, url, json=body, headers=headers, params=query_params, timeout=120)

        response.raise_for_status()

        content_type = response.headers.get("Content-Type", "").lower()

        # Handle different response types
        if "application/json" in content_type:
            return response.json()
        elif "audio" in content_type:
            # Base64 encode audio to return it in the JSON response
            audio_bytes = response.content
            encoded_audio = base64.b64encode(audio_bytes).decode("utf-8")
            return {"status": "success", "content_type": content_type, "audio_content": encoded_audio}
        elif "text" in content_type:
            return {"text": response.text}
        else:
            # For other content types, return as base64 encoded data
            binary_data = base64.b64encode(response.content).decode("utf-8")
            return {"status": "success", "content_type": content_type, "data": binary_data}

    except requests.exceptions.HTTPError as e:
        logger.exception(f"HTTP Error: {e.response.status_code} - {e.response.text}")
        return {
            "error": {
                "message": f"Request to speaches server failed with status {e.response.status_code}",
                "details": e.response.text,
                "status_code": e.response.status_code
            }
        }
    except requests.exceptions.Timeout:
        logger.exception("Request Timeout")
        return {"error": {"message": "Request to speaches server timed out"}}
    except requests.exceptions.ConnectionError:
        logger.exception("Connection Error")
        return {"error": {"message": "Failed to connect to speaches server"}}
    except requests.exceptions.RequestException as e:
        logger.exception("Request Exception")
        return {"error": {"message": f"Request to speaches server failed: {str(e)}"}}
    except Exception as e:
        logger.exception("Unexpected Error")
        return {"error": {"message": f"Unexpected error occurred: {str(e)}"}}


# Start the Runpod serverless worker
if __name__ == "__main__":
    if RUNPOD_AVAILABLE and SERVER_IS_READY:
        logger.info("Starting Runpod serverless handler.")
        runpod.serverless.start({"handler": handler})  # type: ignore # noqa: PGH003
    elif not RUNPOD_AVAILABLE:
        logger.warning("Runpod is not available. Skipping Runpod handler initialization.")
    else:
        logger.critical("Cannot start Runpod handler because Speaches server is not ready.")