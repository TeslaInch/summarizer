import os
from google.cloud import vision
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

key_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS", "").strip().strip('"').strip("'")
print(f"Using credentials: {key_path}")
if not key_path or not Path(key_path).exists():
    raise FileNotFoundError(f"Key not found at: {key_path}")

# Initialize client
client = vision.ImageAnnotatorClient()

# Simple test image (Google sample)
image_uri = "https://cloud.google.com/vision/docs/images/logo_cloud.png"
image = vision.Image()
image.source.image_uri = image_uri

response = client.label_detection(image=image)
if response.error.message:
    raise RuntimeError(f"Vision API error: {response.error.message}")

print("Labels returned:")
for label in response.label_annotations:
    print(f"- {label.description} ({label.score:.2f})")
