import time
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from llm import LLM
from gp import GPData
from utils import process_query

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["GET"],
)

@app.get("/")
def read_root():
    return []

llm = LLM()
gp = GPData(print_debug=True, from_local=False)
@app.get("/inspire")
def inspiration(query: str=''):
    query = process_query(query)
    
    if ("api_key" not in query) or (query["api_key"] != "custom-api-key"):
        return [{"sub-feature": "ERROR", "description": "Incorrect"}]
    
    error_msg = ""
    for i in range(3):
        try:
            if query["source"].lower() == "llm":
                return llm.inspire(query=query)
            elif query["source"].lower() == "gp":
                return gp.inspire(query=query)
            else:
                return [{"sub-feature": "ERROR", "description": "Incorrect"}]
        except Exception as e:
            error_msg = str(e)
            continue
    return [{"sub-feature": "ERROR", "description": error_msg}]
