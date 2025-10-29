# **Speaches on Runpod Serverless**
[![Runpod](https://api.runpod.io/badge/Daniel-OS01/speaches)](https://console.runpod.io/hub/Daniel-OS01/speaches)

This document provides instructions on how to deploy and use the [Speaches](https://github.com/Daniel-OS01/speaches) server on [Runpod Serverless](https://www.runpod.io/serverless-gpu).

# Speaches

## **Overview**

Speaches is an OpenAI API-compatible server for speech-to-text and text-to-speech. By deploying it on Runpod Serverless, you get a scalable, pay-as-you-go API endpoint for your audio processing needs, backed by powerful GPUs.

This adaptation works by running the Speaches Uvicorn server inside the serverless worker. A Runpod handler script acts as a proxy, forwarding incoming API requests to the Speaches server and returning its responses. This setup ensures all features, including the Realtime API, VAD, and dynamic model loading, are available.

Key features include:
- OpenAI API compatibility for seamless integration with existing tools
- Realtime API with VAD (Voice Activity Detection)
- Dynamic model loading/unloading for efficient resource usage
- Streaming transcription via SSE
- Audio I/O support (text in/audio out, audio in/text out, audio in/audio out)
- Support for multiple models including faster-whisper (STT), piper, and Kokoro (TTS)
- GPU and CPU deployment options

## **How to Deploy**

1. **Fork the Repository:** If you haven't already, fork the [speaches repository](https://github.com/Daniel-OS01/speaches) to your own GitHub account.  
2. **Connect to Runpod:** Log in to your Runpod account and connect your GitHub account.  
3. **Create a New Template:**  
   * Go to **Templates** in the Runpod console and click **New Template**.  
   * Give it a name (e.g., "speaches-serverless").  
   * Set **Container Image** to the name of the image you will build (e.g., your-dockerhub-username/speaches-runpod:latest). You will need to push the Docker image there later.  
   * Set **Container Disk** to at least 15 GB to accommodate models.  
4. **Create a Serverless Endpoint:**  
   * Go to **Serverless** \-\> **My Endpoints** and click **New Endpoint**.  
   * Select the template you just created.  
   * Configure the endpoint settings (GPU, idle timeout, etc.). We recommend using a GPU like an RTX 3090 or better.  
   * Click **Create Endpoint**.  
5. **Build and Push the Docker Image:**  
   * Clone your forked repository to your local machine.  
   * Build the Docker image using the provided Dockerfile:  
     ```bash
     docker build \-t your-dockerhub-username/speaches-runpod:latest .
     ```

   * Push the image to Docker Hub (or your preferred registry):  
     ```bash
     docker push your-dockerhub-username/speaches-runpod:latest
     ```

     Ensure the image name matches what you configured in the Runpod template.  
6. **Deployment:** Runpod will automatically pull the image and deploy your endpoint.

## **How to Use the Endpoint**

Once your endpoint is active, you can send requests to it using its unique URL. The request body should follow the schema defined in .runpod/hub.json.

The handler.py script expects an input object with the following fields:

* method: The HTTP method (e.g., "POST").  
* path: The API path you want to reach (e.g., "/v1/audio/speech").  
* body: A JSON object containing the request payload for the Speaches server.  
* file\_url (optional): For transcription, provide a public URL to the audio file.
* headers (optional): Additional headers to pass to the Speaches server.

### **Example: Text-to-Speech (TTS)**

You can send a request to your Runpod endpoint URL (https://api.runpod.ai/v2/{YOUR\_ENDPOINT\_ID}/runsync).

**Request Body (input object):**
```json
{  
  "input": {  
    "method": "POST",  
    "path": "/v1/audio/speech",  
    "body": {  
      "model": "speaches-ai/Kokoro-82M-v1.0-ONNX",
      "input": "Hello from Runpod! This is text-to-speech in action.",
      "voice": "af_heart"
    }  
  }  
}
```

**Response:**  
The response will be a JSON object. If the request is successful, it will contain the base64-encoded audio content.  
```json
{  
  "status": "success",  
  "content\_type": "audio/wav",  
  "audio\_content": "UklGRiS....(base64 data)..."  
}
```
You can then decode this string to get the audio file.

### **Example: Speech-to-Text (STT)**

**Request Body (input object):**
```json
{  
  "input": {  
    "method": "POST",  
    "path": "/v1/audio/transcriptions",  
    "file\_url": "https\_url\_to\_your\_public\_audio\_file.wav",  
    "body": {  
        "model": "Systran/faster-whisper-tiny.en"
    }  
  }  
}
```
**Response:**
```json
{  
  "text": "This is the transcribed text from your audio file."  
}  
```

### **Example: List Available Models**

**Request Body (input object):**
```json
{  
  "input": {  
    "method": "GET",  
    "path": "/v1/models"
  }  
}
```

**Response:**
```json
{
  "data": [
    {
      "id": "Systran/faster-whisper-tiny.en",
      "task": "automatic-speech-recognition"
    },
    {
      "id": "speaches-ai/Kokoro-82M-v1.0-ONNX",
      "task": "text-to-speech"
    }
  ]
}
```

### **Example: Discover Models in Registry**

**Request Body (input object):**
```json
{  
  "input": {  
    "method": "GET",  
    "path": "/v1/registry"
  }  
}
```

**Response:**
```json
{
  "data": [
    {
      "id": "Systran/faster-whisper-tiny.en",
      "task": "automatic-speech-recognition"
    },
    {
      "id": "Systran/faster-whisper-small.en",
      "task": "automatic-speech-recognition"
    },
    {
      "id": "speaches-ai/Kokoro-82M-v1.0-ONNX",
      "task": "text-to-speech"
    }
  ]
}
```

### **Example: Voice Activity Detection (VAD)**

**Request Body (input object):**
```json
{  
  "input": {  
    "method": "POST",  
    "path": "/v1/audio/speech/timestamps",  
    "file\_url": "https\_url\_to\_your\_public\_audio\_file.wav"
  }  
}
```

**Response:**
```json
[
  {
    "start": 100,
    "end": 500
  },
  {
    "start": 750,
    "end": 1200
  }
]
```

### **Example: Dynamic Model Management**

**List loaded models:**
```json
{  
  "input": {  
    "method": "GET",  
    "path": "/api/ps"
  }  
}
```

**Load a model:**
```json
{  
  "input": {  
    "method": "POST",  
    "path": "/api/ps/Systran/faster-whisper-tiny.en"
  }  
}
```

**Unload a model:**
```json
{  
  "input": {  
    "method": "DELETE",  
    "path": "/api/ps/Systran/faster-whisper-tiny.en"
  }  
}
```

### **Example: Realtime API**

To use the Realtime API, you'll need to connect via WebSocket:

**WebSocket URL:**
```
wss://api.runpod.ai/v2/{YOUR_ENDPOINT_ID}/runsync/v1/realtime?model=Systran/faster-whisper-tiny.en&intent=transcription&api_key=your-api-key
```

Refer to the [Realtime API documentation](https://github.com/Daniel-OS01/speaches/blob/master/docs/speaches-docs/usage/realtime-api.md) for detailed usage instructions.

### **Example: Voice Chat**

For voice chat functionality, you can use the chat completions endpoint with audio:

**Request Body (input object):**
```json
{  
  "input": {  
    "method": "POST",  
    "path": "/v1/chat/completions",
    "body": {
      "model": "gpt-4o-mini",
      "messages": [
        {
          "role": "user",
          "content": [
            {
              "type": "text",
              "text": "What is in this recording?"
            },
            {
              "type": "input_audio",
              "input_audio": {
                "data": "<base64_encoded_audio_data>",
                "format": "wav"
              }
            }
          ]
        }
      ],
      "modalities": ["text", "audio"],
      "audio": {
        "voice": "alloy",
        "format": "wav"
      }
    }
  }  
}
```

## **Advanced Usage**

### **Model Aliasing**

Speaches supports model aliasing for easier model management. You can use friendly names instead of full model paths:

```json
{
  "whisper-1": "Systran/faster-whisper-large-v3",
  "tts-1": "speaches-ai/Kokoro-82M-v1.0-ONNX"
}
```

### **Open WebUI Integration**

Speaches can be integrated with Open WebUI for a graphical interface. Configure the following settings in Open WebUI:

- Speech-to-Text Engine: OpenAI
- API Base URL: `http://your-runpod-endpoint-url/v1`
- API Key: any non-empty value (e.g., "does-not-matter")
- Model: `Systran/faster-whisper-tiny.en`

### **Environment Variables**

The following environment variables can be set to customize the behavior of Speaches:

- `MODEL_LOAD_TIMEOUT`: Timeout for model loading (default: 300 seconds)
- `HF_HUB_ENABLE_HF_TRANSFER`: Enable faster Hugging Face downloads (default: 1)
- `HF_TOKEN`: Hugging Face token for private models (optional)

## **Troubleshooting**

If you encounter issues:

1. **Check the model is downloaded:** Ensure the model you're trying to use has been downloaded to the server.
2. **Verify the endpoint URL:** Make sure you're using the correct Runpod endpoint URL.
3. **Check disk space:** Ensure you have allocated enough disk space (at least 15GB) for models.
4. **Review logs:** Check Runpod logs for detailed error messages.

For more detailed documentation, refer to the [Speaches documentation](https://github.com/Daniel-OS01/speaches/tree/master/docs/speaches-docs/usage).