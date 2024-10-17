from qdrant_client import QdrantClient

if __name__ == "__main__":
    client = QdrantClient(url="http://localhost:6333")

    client.create_payload_index(
        collection_name="app_description",
        field_name="desc_length",
        field_schema="integer",
    )