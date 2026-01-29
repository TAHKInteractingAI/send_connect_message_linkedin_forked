from dotenv import load_dotenv
import os, json

load_dotenv()

print(type(json.loads(os.getenv("GOOGLE_APPLICATION_CREDENTIALS_TEST"))))