import os
from dotenv import load_dotenv

from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings  # Gratis y local
from langchain_qdrant import QdrantVectorStore

from app.core.qdrant import client, COLLECTION_NAME

load_dotenv()

# Modelo de embeddings local y totalmente gratuito
EMBEDDING_MODEL_NAME = "BAAI/bge-small-en-v1.5"

def process_pdf_and_store(file_path: str) -> int:
    """
    Carga un archivo PDF, lo divide en chunks, genera embeddings
    gratuitos con HuggingFace y los almacena en Qdrant.
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"El archivo {file_path} no existe.")

    # 1. Cargar el PDF
    loader = PyPDFLoader(file_path)
    documents = loader.load()

    # 2. Dividir el texto en chunks
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=150,
        length_function=len
    )
    chunks = text_splitter.split_documents(documents)

    # 3. Inicializar el modelo de embeddings GRATUITO
    embeddings = HuggingFaceEmbeddings(model_name=EMBEDDING_MODEL_NAME)

    # 4. Instanciar la base vectorial en Qdrant
    vector_store = QdrantVectorStore(
        client=client,
        collection_name=COLLECTION_NAME,
        embedding=embeddings
    )

    # 5. Guardar chunks en Qdrant
    vector_store.add_documents(chunks)

    return len(chunks)