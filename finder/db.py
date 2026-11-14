"""
Database connection module for MongoDB Atlas using PyMongo.
This module maintains a singleton MongoDB client and provides helper functions
to access the database and collections without re-initializing connections on each request.
"""

import os
from pathlib import Path
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure, ConfigurationError, ServerSelectionTimeoutError

# --- Load .env early so MONGO_URI is always available, even in scripts ---
try:
    from dotenv import load_dotenv
    _BASE_DIR = Path(__file__).resolve().parent.parent
    load_dotenv(_BASE_DIR / '.env', override=False)
except ImportError:
    pass  # dotenv not installed — rely on environment variables being set externally

# --- certifi CA bundle for Windows TLS compatibility with MongoDB Atlas ---
try:
    import certifi
    CA_FILE = certifi.where()
except ImportError:
    CA_FILE = None

# Global client cache — reset whenever URI changes
_client = None
_cached_uri = None


def get_mongo_client():
    """
    Returns a cached PyMongo MongoClient instance.
    Initializes the client on first call and whenever MONGO_URI changes.

    TLS Fix for Windows (TLSV1_ALERT_INTERNAL_ERROR):
    - Uses certifi CA bundle to validate Atlas's certificate chain.
    - Explicitly sets tls=True and tlsCAFile to bypass Windows Schannel issues.
    """
    global _client, _cached_uri

    mongo_uri = os.getenv('MONGO_URI', 'mongodb://localhost:27017/')

    if _client is None or _cached_uri != mongo_uri:
        is_atlas = 'mongodb+srv://' in mongo_uri or 'tls=true' in mongo_uri.lower()

        client_kwargs = {
            'serverSelectionTimeoutMS': 10000,
            'connectTimeoutMS': 10000,
            'socketTimeoutMS': 20000,
        }

        if is_atlas and CA_FILE:
            client_kwargs['tls'] = True
            client_kwargs['tlsCAFile'] = CA_FILE

        _client = MongoClient(mongo_uri, **client_kwargs)
        _cached_uri = mongo_uri

    return _client

def get_db():
    """
    Returns the MongoDB database instance defined in .env (default: 'campus_lost_found').
    """
    client = get_mongo_client()
    db_name = os.getenv('MONGO_DB_NAME', 'campus_lost_found')
    return client[db_name]

def get_reports_collection():
    """
    Returns the 'item_reports' collection from the MongoDB database.
    """
    db = get_db()
    return db['item_reports']

def test_connection():
    """
    Pings the MongoDB server to verify whether the connection credentials and network access work.
    Returns:
        (is_successful: bool, message: str)
    """
    try:
        client = get_mongo_client()
        client.admin.command('ping')
        db_name = os.getenv('MONGO_DB_NAME', 'campus_lost_found')
        return True, f"Successfully connected to MongoDB! Database: '{db_name}'"
    except ConfigurationError as ce:
        return False, f"Configuration Error: {ce}"
    except ConnectionFailure as cf:
        return False, f"Connection Failed: Could not reach MongoDB cluster. Please check network access (IP whitelist) and credentials. Details: {cf}"
    except Exception as e:
        return False, f"Unexpected error while connecting to MongoDB: {e}"

if __name__ == '__main__':
    import dotenv
    from pathlib import Path
    BASE_DIR = Path(__file__).resolve().parent.parent
    dotenv.load_dotenv(BASE_DIR / '.env')
    success, msg = test_connection()
    print("Test Result:", "SUCCESS" if success else "FAILED")
    print(msg)
