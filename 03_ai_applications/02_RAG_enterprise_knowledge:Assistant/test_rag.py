from app.services.rag import query_rag_pipeline

# Haz una pregunta relacionada con el contenido del PDF que subiste
pregunta = "busca en el documento fechas y dime a que se refieren"  # Cambia esto según el contenido de tu PDF

print(f"🔍 Preguntando: '{pregunta}'...\n")
resultado = query_rag_pipeline(query=pregunta)

print(f"🤖 Respuesta del RAG:\n{resultado['answer']}\n")
print(f"⏱️ Latencia: {resultado['latency_seconds']} segundos\n")
print("📄 Fuentes utilizadas:")
for s in resultado["sources"]:
    print(f" - Archivo: {s['source']} (Página {s['page']})")