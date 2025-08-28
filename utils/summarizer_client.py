import os
from dotenv import load_dotenv
load_dotenv()

print("Loaded key path:", os.getenv("GOOGLE_APPLICATION_CREDENTIALS"))

