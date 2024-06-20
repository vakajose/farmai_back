import os

import firebase_admin
from dotenv import load_dotenv
from firebase_admin import credentials, firestore

load_dotenv()
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
firebase_keyfile = os.path.join(parent_dir, os.getenv("FIREBASE_KEYFILE"))
print(firebase_keyfile)
cred = credentials.Certificate(firebase_keyfile)
firebase_admin.initialize_app(cred)
db = firestore.client()


def create_user(data):
    user_ref = db.collection('users').document(data['username'])
    user_ref.set(data)


def get_user_by_username(username):
    user_ref = db.collection('users').document(username)
    user = user_ref.get()
    if user.exists:
        return user.to_dict()
    return None
