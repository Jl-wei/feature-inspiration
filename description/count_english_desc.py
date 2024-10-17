import os
import re

from tqdm import tqdm

from pymongo.mongo_client import MongoClient

import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from preprocessing import process_desc



if __name__ == "__main__":
    uri = os.environ['MONGODB_URI']
    mongo_client = MongoClient(uri)
    mongo_coll = mongo_client['google_play']['app_v2']

    pbar = tqdm(mongo_coll.find({"genreId": {"$not": re.compile('GAME')}}, no_cursor_timeout=True), 
                total=mongo_coll.count_documents({"genreId": {"$not": re.compile('GAME')}}))

    i = 0
    for doc in pbar:
        desc = process_desc(doc['description'])
        if len(desc) > 200: i += 1
    print (i)
