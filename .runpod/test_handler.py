#!/usr/bin/env python3
"""
Test script to verify the handler functionality locally.
"""

import json
import sys
import os

# Add the current directory to the path so we can import the handler
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import the handler function
from handler import handler

def test_health_check():
    """Test the health check endpoint."""
    print("Testing health check...")
    event = {
        "input": {
            "method": "GET",
            "path": "/health"
        }
    }
    
    try:
        result = handler(event)
        print("Health check result:", json.dumps(result, indent=2))
        return result
    except Exception as e:
        print(f"Error during health check: {e}")
        return None

def test_list_models():
    """Test the list models endpoint."""
    print("\nTesting list models...")
    event = {
        "input": {
            "method": "GET",
            "path": "/v1/models"
        }
    }
    
    try:
        result = handler(event)
        print("List models result:", json.dumps(result, indent=2))
        return result
    except Exception as e:
        print(f"Error during list models: {e}")
        return None

if __name__ == "__main__":
    print("Running handler tests...")
    
    # Test health check
    health_result = test_health_check()
    
    # Test list models
    models_result = test_list_models()
    
    print("\nTests completed.")