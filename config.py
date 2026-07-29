import os
from dotenv import load_dotenv

#Loads variables from .env
load_dotenv()

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'vceui748426c287498bsbvghucygle')

    #Centralize the database paths
    DATABASE_PATH = os.path.join(BASE_DIR, 'database', 'database.db')
    SCHEMA_PATH = os.path.join(BASE_DIR, 'database', 'schema.sql')

    #Groq AI API KEY
    GROQ_API_KEY = os.environ.get('GROQ_API_KEY')
    PERMANENT_SESSION_LIFETIME = int(os.environ.get('PERMANENT_SESSION_LIFETIME', 86400))
