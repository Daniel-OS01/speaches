# Runpod Deployment for Speaches

This directory contains all the necessary files for deploying Speaches on Runpod Serverless.

## Files

- `handler.py`: The main handler function that proxies requests to the Speaches server
- `Dockerfile`: Container configuration for Runpod deployment
- `hub.json`: Metadata and configuration for Runpod Hub listing
- `tests.json`: Test cases for Runpod's automated testing
- `runpod_requirements.txt`: Python dependencies required for Runpod deployment

## Deployment

To deploy Speaches on Runpod:

1. Create a new GitHub release
2. The Runpod Hub will automatically index and build your repository
3. After successful testing, the Runpod team will review and publish your listing

## Testing

The tests defined in `tests.json` will be automatically executed during the build process. These tests verify that all Speaches functionalities work correctly:

- Health check endpoint
- Text-to-Speech generation
- Speech-to-Text transcription
- Model listing and discovery
- Voice Activity Detection
- Dynamic model loading

## Configuration

The deployment can be configured through environment variables defined in `hub.json`. Users can adjust settings like model load timeout when deploying the endpoint.