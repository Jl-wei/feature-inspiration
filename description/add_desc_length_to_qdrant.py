from qdrant_client import QdrantClient


if __name__ == "__main__":
    client = QdrantClient(url="http://localhost:6333")

    offset=None
    while(True):
        result = client.scroll(
            collection_name="app_description",
            limit=1,
            offset=offset,
            with_payload=True,
            with_vectors=False,
        )
        id = result[0][0].id
        description = result[0][0].payload['description']
        
        client.set_payload(
            collection_name="app_description",
            payload={
                "desc_length": len(description),
            },
            points=[id],
        )
        
        offset = result[1]
        if not offset: break

        print(result[0][0].payload['appId'])