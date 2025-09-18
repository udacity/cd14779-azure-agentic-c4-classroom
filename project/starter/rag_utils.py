
import os
from azure.storage.blob import BlobServiceClient
from docx import Document


def read_docx(file_path):
    """
    Reads text content from a .docx file.

    Args:
        file_path (str): Path to the .docx file

    Returns:
        str: Extracted text from the document
    """
    try:
        doc = Document(file_path)
        full_text = []

        for paragraph in doc.paragraphs:
            full_text.append(paragraph.text)

        return '\n'.join(full_text)

    except Exception as e:
        print(f"Error reading DOCX file: {str(e)}")
        return None
    
def read_pdf(file_path: str) -> str:
    """
    Extract text From a PDF file.
    """
    text = "this is just a fake placeholder for pdf text"
    
    return text

def download_blobs_from_azure(connection_string, container_name, local_directory):
    """
    Downloads all blobs from an Azure Blob Storage container

    Args:
        connection_string (str): Azure Storage account connection string
        container_name (str): Name of the container to download from
        local_directory (str): Local directory to save downloaded files
    """
    try:
        # Create the BlobServiceClient
        blob_service_client = BlobServiceClient.from_connection_string(connection_string)

        # Get the container client
        container_client = blob_service_client.get_container_client(container_name)

        # Create local directory if it doesn't exist
        os.makedirs(local_directory, exist_ok=True)

        print(f"Downloading blobs from container '{container_name}'...")

        # List and download all blobs in the container
        blob_list = container_client.list_blobs()
        for blob in blob_list:
            # Skip directories (blob names ending with '/')
            if blob.name.endswith('/'):
                continue

            local_path = os.path.join(local_directory, blob.name)

            # Create subdirectories if needed
            os.makedirs(os.path.dirname(local_path), exist_ok=True)

            # Download the blob
            blob_client = container_client.get_blob_client(blob)
            with open(local_path, "wb") as file:
                file.write(blob_client.download_blob().readall())

            print(f"Downloaded: {blob.name}")

        print("Download completed successfully!")

    except Exception as e:
        print(f"Error: {str(e)}")

def load_documents(DOCS_DIR):
    """
    Load text and docx documents from a specified directory.

    Args:
        DOCS_DIR (str): Directory containing the documents

    Returns:
        list: List of document dictionaries with filename, id, meta, and text
    """

    docs = [
            {
                "filename": "Loan_Eligibility_Policies.pdf",
                "id": "Loan_Eligibility",
                "meta": {"priority": "low to medium"}
            },
            {
                "filename": "Fraud_Detection_Policies.txt",
                "id": "Fraud_Detection",
                "meta": {"priority": "high"}
            },
            {
                "filename": "Customer_Support_Policies.docx",
                "id": "Customer_Support",
                "meta": {"priority": "low to medium"}
            }]

    for doc in docs:
        if doc["filename"].endswith(".txt"):
            with open(os.path.join(DOCS_DIR, doc["filename"]), "r+", encoding="utf-8") as f:
                doc["text"]=f.read()
        elif doc["filename"].endswith(".docx"):
            doc["text"]=read_docx(os.path.join(DOCS_DIR, doc["filename"]))
        elif doc["filename"].endswith(".pdf"):
            doc["text"]=read_pdf(os.path.join(DOCS_DIR, doc["filename"]))
    return docs

def seed_collection_from_txt(coll, docs):
    """Seed ChromaDB collection with documents from TXT files."""
    if coll.count() > 0:
        print(f"Collection already has {coll.count()} items.")
        return

    ids = [d["id"] for d in docs]
    texts = [d["text"] for d in docs]
    metas = [d["meta"] for d in docs]

    coll.add(ids=ids, documents=texts, metadatas=metas,)
    print(f"Seeded {len(docs)} documents into Chroma from TXT files.")

def print_collection_contents(client, collection_name=None, collection_obj=None, max_items=20):
    """
    Provide either collection_obj (the collection) or collection_name (string).
    Will attempt several common API calls to fetch stored ids, docs, metadata.
    """
    if collection_obj is None:
        # try to get collection from client
        try:
            # common signature
            collection_obj = client.get_collection(collection_name)
        except Exception:
            try:
                collection_obj = client.get_collection(name=collection_name)
            except Exception as e:
                print("Couldn't obtain collection object:", e)
                return

    # print count if available
    try:
        print("Collection count:", collection_obj.count())
    except Exception:
        pass

    # Try to get documents. Different versions expose different args.
    result = None
    get_variants = [
        lambda: collection_obj.get(),                        # no-arg
        lambda: collection_obj.get(limit=max_items),         # limit
        lambda: collection_obj.get(n_results=max_items),     # n_results
        lambda: collection_obj.get(ids=[]),                  # empty ids -> all (some versions)
        lambda: collection_obj.peek(max_results=max_items),  # peek (some versions)
    ]
    for fn in get_variants:
        try:
            result = fn()
            if result:
                break
        except Exception:
            continue

    if not result:
        print("Failed to fetch documents with common `get()`/`peek()` signatures. "
              "Show me the client/collection creation code and I will adapt.")
        return

    # result is commonly a dict with keys 'ids','documents','metadatas','embeddings' etc.
    keys_to_print = ["ids", "documents", "metadatas"]
    for k in keys_to_print:
        if k in result:
            print(f"\n{k} (first {max_items}):")
            vals = result[k]
            # handle numpy arrays etc.
            try:
                to_show = vals[:max_items]
            except Exception:
                to_show = vals
            for i, v in enumerate(to_show, 1):
                print(f" {i}. {v}")

    # Useful quick access by id:
    if "ids" in result and "documents" in result:
        id_to_doc = dict(zip(result["ids"], result["documents"]))
        print("\nExample lookup - print one document by id:")
        example_id = result["ids"][0]
        print("id:", example_id)
        print("text:", id_to_doc[example_id])