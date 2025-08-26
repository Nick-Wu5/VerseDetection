#!/usr/bin/env python3
"""
Configuration helper for Google Cloud Vision API setup.
Ensures proper credentials are configured for OCR functionality.
"""

import os
from google.cloud import vision

def check_google_vision_setup():
    """
    Check if Google Cloud Vision API is properly configured.
    
    Returns:
        bool: True if properly configured, False otherwise
    """
    try:
        # Check if credentials are set
        credentials_path = os.getenv('GOOGLE_APPLICATION_CREDENTIALS')
        if not credentials_path:
            print("❌ GOOGLE_APPLICATION_CREDENTIALS environment variable not set")
            print("Please set it to your service account key file path")
            return False
        
        if not os.path.exists(credentials_path):
            print(f"❌ Credentials file not found: {credentials_path}")
            return False
        
        # Test the client
        client = vision.ImageAnnotatorClient()
        print("✅ Google Cloud Vision API client initialized successfully")
        print(f"✅ Credentials file: {credentials_path}")
        return True
        
    except Exception as e:
        print(f"❌ Error setting up Google Cloud Vision API: {e}")
        return False

def setup_instructions():
    """Print setup instructions for Google Cloud Vision API."""
    print("\n=== Google Cloud Vision API Setup Instructions ===")
    print("1. Go to Google Cloud Console: https://console.cloud.google.com/")
    print("2. Create a new project or select existing one")
    print("3. Enable the Cloud Vision API")
    print("4. Create a service account and download the JSON key file")
    print("5. Set environment variable:")
    print("   export GOOGLE_APPLICATION_CREDENTIALS=/path/to/your/key.json")
    print("6. Install the client library: pip install google-cloud-vision")
    print("\nFor more details: https://cloud.google.com/vision/docs/setup")

if __name__ == "__main__":
    print("Checking Google Cloud Vision API configuration...")
    
    if check_google_vision_setup():
        print("\n🎉 Setup complete! You can now run the verse detection system.")
    else:
        print("\nSetup incomplete. Please follow these instructions:")
        setup_instructions()
