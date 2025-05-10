import firebase_admin
from firebase_admin import credentials, firestore

cred = credentials.Certificate("creds/klyptik.json")
firebase_admin.initialize_app(cred)

db = firestore.client()

def initialize_firebase():
    """
    Initialize Firebase
    """
    return db