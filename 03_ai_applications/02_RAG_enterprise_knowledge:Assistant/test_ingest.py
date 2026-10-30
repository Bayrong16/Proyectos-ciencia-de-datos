from app.core.qdrant import init_qdrant_collection
from app.services.ingestion import process_pdf_and_store

# 1. Asegurar que la colección existe
init_qdrant_collection()

# 2. Procesar PDF de prueba (reemplaza 'reporte.pdf' por el nombre de tu archivo)
pdf_path = "data/pdfs/tdrs.pdf"
num_chunks = process_pdf_and_store(pdf_path)

print(f"✅ ¡Proceso completado! Se guardaron {num_chunks} chunks en Qdrant.")