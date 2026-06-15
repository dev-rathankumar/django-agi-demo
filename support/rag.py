import os
import chromadb
from chromadb.utils import embedding_functions
from pypdf import PdfReader


# Initialize ChromaDB client - stores data on disk
client = chromadb.PersistentClient(path="./chroma_db")

# Default embedding function - converts text to numbers
embedding_fn = embedding_functions.DefaultEmbeddingFunction()

# Get or create collection - like a table in a regular database
collection = client.get_or_create_collection(
    name="coolbreeze_docs",
    embedding_function=embedding_fn
)


def chunk_text(text, chunk_size=500):
    words = text.split()
    chunks = []
    current_chunk = []
    current_size = 0

    for word in words:
        current_chunk.append(word)
        current_size += len(word) + 1

        if current_size >= chunk_size:
            chunks.append(" ".join(current_chunk))
            current_chunk = []
            current_size = 0

    if current_chunk:
        chunks.append(" ".join(current_chunk))

    return chunks



def load_documents():
    docs_path = "support/documents/"

    documents = []
    ids = []

    for filename in os.listdir(docs_path):
        if filename.endswith(".pdf"):
            filepath = os.path.join(docs_path, filename)
            reader = PdfReader(filepath)

            full_text = ""
            for page in reader.pages:
                full_text += page.extract_text()

            chunks = chunk_text(full_text, chunk_size=500)

            for i, chunk in enumerate(chunks):
                documents.append(chunk)
                ids.append(f"{filename}_{i}")

    if documents:
        collection.add(documents=documents, ids=ids)

    print(f"Loaded {len(documents)} chunks into ChromaDB")



def search_knowledge_base(query):
    results = collection.query(query_texts=[query], n_results=3)

    if not results["documents"][0]:
        return "No relevant information found in company documents."
    
    matched_chunks = results["documents"][0]
    return "\n\n".join(matched_chunks)