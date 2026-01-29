from dotenv import load_dotenv
import os, json

load_dotenv()

print(type(os.getenv('GOOGLE_APPLICATION_CRED')))