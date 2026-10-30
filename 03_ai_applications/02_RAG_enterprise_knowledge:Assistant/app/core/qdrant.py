import os
from dotenv import load_dotenv
from qdrant_client import QdrantClient
from qdrant_client.http.models import Distance, VectorParams

load_dotenv()

QDRANT_HOST = os.getenv("QDRANT_HOST", "localhost")
QDRANT_PORT = int(os.getenv("QDRANT_PORT", 6333))
COLLECTION_NAME = os.getenv("QDRANT_COLLECTION_NAME", "corporate_docs")

# Instancia del cliente de Qdrant
client = QdrantClient(host=QDRANT_HOST, port=QDRANT_PORT)

def init_qdrant_collection():
    """Inicializa la colección en Qdrant si aún no existe."""
    collections = client.get_collections().collections
    collection_names = [col.name for col in collections]

    if COLLECTION_NAME not in collection_names:
        # text-embedding-3-small de OpenAI genera vectores de dimensión 1536
        client.create_collection(
            collection_name=COLLECTION_NAME,
            vectors_config=VectorParams(
                size=384,
                distance=Distance.COSINE
            )
        )
        print(f"Colección '{COLLECTION_NAME}' creada con éxito en Qdrant.")
    else:
        print(f"La colección '{COLLECTION_NAME}' ya existe.")

if __name__ == "__main__":
    init_qdrant_collection()