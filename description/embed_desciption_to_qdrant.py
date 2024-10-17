import os
import re
import argparse
import uuid

from tqdm import tqdm
from qdrant_client import QdrantClient, models

from pymongo.mongo_client import MongoClient
from sentence_transformers import SentenceTransformer
from langchain_text_splitters import RecursiveCharacterTextSplitter

import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from preprocessing import process_desc

# https://support.google.com/googleplay/android-developer/answer/13393723?hl=en
# The description length limit is 4000

CHUNK_SIZE = 2000


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('-c', '--clean_old_collection', type=bool, default=False)
    args = parser.parse_args()
    
    encoder = SentenceTransformer('BAAI/bge-small-en-v1.5')
    
    uri = os.environ['MONGODB_URI']
    mongo_client = MongoClient(uri)
    mongo_coll = mongo_client['google_play']['app_v2']
    
    qdrant_client = QdrantClient(url="http://localhost:6333")
    if args.clean_old_collection:
        qdrant_client.delete_collection(collection_name="app_description")
    if not qdrant_client.collection_exists("app_description"):
        qdrant_client.create_collection(
            collection_name="app_description",
            vectors_config=models.VectorParams(
                size=encoder.get_sentence_embedding_dimension(),
                distance=models.Distance.COSINE,
            ),
        )

    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=200,
        length_function=len,
        is_separator_regex=False,
    )

    pbar = tqdm(mongo_coll.find({"genreId": {"$not": re.compile('GAME')}}, no_cursor_timeout=True), 
                total=mongo_coll.count_documents({"genreId": {"$not": re.compile('GAME')}}))

    for doc in pbar:
        pbar.set_description(f"App Id: {doc['appId']}")
        description = process_desc(doc['description'])
        if len(description) == 0: continue

        chunks = text_splitter.create_documents([description])
        i = 0
        for chunk in chunks:
            try:
                text = chunk.page_content
                embedding = encoder.encode(text, device="cuda").tolist()
                
                payload = {
                            "appId": doc['appId'], 
                            "genreId": doc['genreId'], 
                            "description": text, 
                        }
                qdrant_client.upsert(
                    collection_name="app_description",
                    points=[
                        models.PointStruct(
                            id=str(uuid.uuid3(uuid.NAMESPACE_DNS, f"{doc['appId']}.{i}")),
                            vector=embedding,
                            payload=payload
                        )
                    ]
                )
                i += 1
            except Exception as e:
                print("===============", doc['appId'])
                print(e)
                print(text)
                print("===============", doc['appId'])
                print()
