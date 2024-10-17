import re
import json

def select_code_block(text):
    match = re.search(rf"```(.*?)\n(.*?)```", text, re.DOTALL)
    if match:
        return match.groups()[1]
    else:
        return text

def process_query(query):
    query = query.replace("\n", "")
    query = json.loads(query)
    return query