"""
database.py
-----------
Owns all interaction with ChromaDB. Nothing outside this file should ever
import chromadb directly -- keep the vector store logic isolated so it's
easy to swap or debug independently of the rest of the app.
"""

import os
import json
import chromadb
from chromadb.utils import embedding_functions

from src.config import CHROMA_DB_PATH, CHROMA_COLLECTION_NAME, SPORTS_FACTS_PATH


def get_chroma_client():
    """Initializes and returns a persistent ChromaDB client saving to disk."""
    return chromadb.PersistentClient(path=CHROMA_DB_PATH)


def _get_collection(client):
    """Gets (or lazily creates) the sports_history collection using
    ChromaDB's default local sentence-transformers embedding function."""
    embedding_fn = embedding_functions.DefaultEmbeddingFunction()
    return client.get_or_create_collection(
        name=CHROMA_COLLECTION_NAME,
        embedding_function=embedding_fn,
    )


def setup_and_populate_db(json_file_path: str = None):
    """
    Reads the offline JSON facts, creates a collection, and populates it.
    Safe to call on every app startup -- it's a no-op if the DB already
    has data, so re-running your Streamlit app won't duplicate entries.
    """
    json_file_path = json_file_path or SPORTS_FACTS_PATH
    client = get_chroma_client()
    collection = _get_collection(client)

    if collection.count() > 0:
        print(f"[database] Already populated with {collection.count()} facts.")
        return collection

    if not os.path.exists(json_file_path):
        print(f"[database] ERROR: fact file not found at {json_file_path}")
        return collection

    with open(json_file_path, "r", encoding="utf-8") as f:
        facts_list = json.load(f)

    documents, metadata_list, ids = [], [], []
    for idx, item in enumerate(facts_list):
        documents.append(item["fact"])
        # Storing sport as metadata lets us filter queries by sport later.
        metadata_list.append({"sport": item["sport"]})
        ids.append(f"fact_{idx}")

    collection.add(documents=documents, metadatas=metadata_list, ids=ids)
    print(f"[database] Vectorized and stored {len(documents)} facts.")
    return collection


def query_historic_facts(sport: str, query_text: str, n_results: int = 3):
    """
    Queries ChromaDB for historic documents relating to a sport.
    Filters results to only the selected sport category via metadata.
    Returns a list of matched fact strings (possibly empty).
    """
    client = get_chroma_client()
    collection = _get_collection(client)

    if collection.count() == 0:
        return []

    results = collection.query(
        query_texts=[query_text],
        n_results=min(n_results, collection.count()),
        where={"sport": sport},
    )
    return results.get("documents", [[]])[0]


def reset_database():
    """Utility for development: wipes the collection so it can be
    re-seeded from scratch. Not wired to the UI by default."""
    client = get_chroma_client()
    try:
        client.delete_collection(CHROMA_COLLECTION_NAME)
        print("[database] Collection deleted.")
    except Exception as e:
        print(f"[database] Nothing to delete or error occurred: {e}")
