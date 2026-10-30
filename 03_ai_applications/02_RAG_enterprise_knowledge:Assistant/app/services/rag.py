import os
import time
from typing import Dict, Any
from dotenv import load_dotenv

import mlflow
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_openai import ChatOpenAI  # O compatible con OpenAI/OpenRouter si usas base_url
from langchain_qdrant import QdrantVectorStore
from langchain_classic.chains import create_retrieval_chain
from langchain_classic.chains.combine_documents import create_stuff_documents_chain

from langchain_core.prompts import ChatPromptTemplate

from app.core.qdrant import client, COLLECTION_NAME
from app.services.ingestion import EMBEDDING_MODEL_NAME

load_dotenv()

# Configuración de MLflow
MLFLOW_URI = os.getenv("MLFLOW_TRACKING_URI", "http://localhost:5000")
mlflow.set_tracking_uri(MLFLOW_URI)
mlflow.set_experiment("Enterprise_Knowledge_Assistant")

def query_rag_pipeline(query: str, top_k: int = 4) -> Dict[str, Any]:
    """
    Ejecuta el pipeline RAG completo y registra los resultados en MLflow.
    """
    start_time = time.time()

    # 1. Configurar embeddings y retriever
    embeddings = HuggingFaceEmbeddings(model_name=EMBEDDING_MODEL_NAME)
    vector_store = QdrantVectorStore(
        client=client,
        collection_name=COLLECTION_NAME,
        embedding=embeddings
    )
    retriever = vector_store.as_retriever(search_kwargs={"k": top_k})

    # 2. Configurar el LLM 
    # (Si usas OpenRouter con tu modelo gratuito, puedes configurar base_url y api_key aquí)
    llm = ChatOpenAI(
        model=os.getenv("LLM_MODEL"),
        base_url=os.getenv("LLM_BASE_URL"),
        api_key=os.getenv("OPENROUTER_API_KEY"),
        temperature=0.2

    )

    system_prompt = (
        "Eres un asistente corporativo experto. Responde a la pregunta del usuario "
        "utilizando exclusivamente los siguientes fragmentos de contexto recuperados. "
        "Si la respuesta no se encuentra en el contexto, indica amablemente que no posees "
        "dicha información en la base de conocimientos.\n\n"
        "Contexto:\n{context}"
    )

    prompt = ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        ("human", "{input}"),
    ])

    question_answer_chain = create_stuff_documents_chain(llm, prompt)
    rag_chain = create_retrieval_chain(retriever, question_answer_chain)

    # 3. Ejecutar consulta
    response = rag_chain.invoke({"input": query})
    elapsed_time = round(time.time() - start_time, 3)

    # 4. Extraer fuentes
    sources = []
    for doc in response.get("context", []):
        source_info = {
            "source": doc.metadata.get("source", "Desconocido"),
            "page": doc.metadata.get("page", 0) + 1,
            "snippet": doc.page_content[:200] + "..."
        }
        sources.append(source_info)

    answer_text = response.get("answer", "")

    # 5. Registrar en MLflow
    try:
        with mlflow.start_run(run_name="RAG_Query"):
            mlflow.log_param("query", query)
            mlflow.log_param("top_k", top_k)
            mlflow.log_param("embedding_model", EMBEDDING_MODEL_NAME)
            mlflow.log_metric("latency_seconds", elapsed_time)
            mlflow.log_metric("retrieved_chunks_count", len(sources))
            mlflow.log_text(answer_text, "response_output.txt")
    except Exception as e:
        print(f"Aviso: No se pudo registrar en MLflow Server ({e}).")

    return {
        "query": query,
        "answer": answer_text,
        "sources": sources,
        "latency_seconds": elapsed_time
    }