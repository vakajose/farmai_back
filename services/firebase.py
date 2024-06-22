import os

import firebase_admin
from dotenv import load_dotenv
from firebase_admin import credentials, firestore

load_dotenv()

parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
firebase_keyfile = os.path.join(parent_dir, os.getenv("FIREBASE_KEYFILE"))

cred = credentials.Certificate(firebase_keyfile)
firebase_admin.initialize_app(cred)
db = firestore.client()

prefix = os.getenv('FIREBASE_COLLECTION_PREFIX', '')