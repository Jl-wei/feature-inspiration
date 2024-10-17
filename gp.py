import json
import google_play_scraper
from langchain.chains import LLMChain
from langchain_openai import ChatOpenAI
from langchain_core.prompts import (
    PromptTemplate,
    ChatPromptTemplate,
    HumanMessagePromptTemplate,
)
from langchain_core.messages import SystemMessage
# from qdrant_client import QdrantClient, models
# from sentence_transformers import SentenceTransformer
from utils import *

import os
os.environ["TOKENIZERS_PARALLELISM"] = "false"


def get_system_message():
    message = SystemMessage(content='''
You are an expert in mobile app development and requirements engineering. 
You excel at decomposing high-level features into detailed sub-features.
Additionally, your expertise extends to extracting app features from descriptions, enabling you to identify key functionalities like "step count," "group chats," and "multi-device synchronization."
''')
    return message

def get_feature_extraction_template():
    template = '''
**App description**
```
{app_description}
```
From the app description above, please extract the sub-features of this following feature.
Ensure that all sub-features are from the app description.
**Feature**
```
{feature_with_desc}
```

The output should be a list of JSON formatted objects like this:
[{{
"sub-feature": sub-feature,
"description": description
}}]
    '''
    prompt = HumanMessagePromptTemplate(
        prompt=PromptTemplate(
            template=template,
            input_variables=["feature_with_desc", "app_description"],
        )
    )
    prompt_template = ChatPromptTemplate.from_messages([get_system_message(), prompt])
    return prompt_template

def get_feature_with_super_feature_extraction_template():
    template = '''
**Super Feature**
```
super-feature: {super_feature}
description: {super_feature_description}
```
Knowing that the feature "{super_feature}" above is refined into a list of the following sub-features:
```
{sub_features}
```

**App description**
```
{app_description}
```
From the app description above, please extract the sub-features of this following feature.
Ensure that all sub-features are from the app description.
**Feature**
```
{feature_with_desc}
```

The output should be a list of JSON formatted objects like this:
[{{
"sub-feature": sub-feature,
"description": description
}}]
    '''
    prompt = HumanMessagePromptTemplate(
        prompt=PromptTemplate(
            template=template,
            input_variables=["super_feature", "super_feature_description", "sub_features", "feature_with_desc", "app_description"],
        )
    )
    prompt_template = ChatPromptTemplate.from_messages([get_system_message(), prompt])
    return prompt_template

def get_select_feature_template():
    template = '''
```json
{features}
```
Given the JSON list of app features provided above, please combine them into a single list. 
Ensure that similar sub-features are merged into one.
You should only keep 5 sub-features that are most relevant to the following feature description:
```
{feature_with_desc}
```

The output should be a list of JSON formatted like this:
[{{
"sub-feature": sub-feature,
"description": description,
"source-app-id": source-app-id
}}]
'''
    prompt = HumanMessagePromptTemplate(
        prompt=PromptTemplate(
            template=template,
            input_variables=["features", "feature_with_desc"],
        )
    )
    prompt_template = ChatPromptTemplate.from_messages([get_system_message(), prompt])
    return prompt_template


class GPData:
    def __init__(self, model_name="gpt-4o", from_local=True, print_debug=False):
        self.from_local = from_local
        self.print_debug = print_debug
        # self.encoder = SentenceTransformer('BAAI/bge-small-en-v1.5')
        # if self.from_local:
        #     self.qdrant_client = QdrantClient(url="http://localhost:6333")
        chat_model = ChatOpenAI(model=model_name, temperature=0, openai_api_key=os.environ["OPENAI_API_KEY"])
        
        self.feature_extraction_chain = LLMChain(llm=chat_model, prompt=get_feature_extraction_template())
        self.feature_with_super_extraction_chain = LLMChain(llm=chat_model, prompt=get_feature_with_super_feature_extraction_template())
        self.select_feature_chain = LLMChain(llm=chat_model, prompt=get_select_feature_template())
    
    def inspire(self, query):
        if all(item in query.keys() for item in ["super_feature", "super_feature_description", "feature", "sibling_features"]):
            super_feature = f"{query['super_feature']}: {query['super_feature_description']}"
        else:
            super_feature = ""
        if "feature" in query and "feature_description" in query:
            q_feature = f"{query['feature']}: {query['feature_description']}"
        else:
            q_feature = query['feature']

        id_descs = self.search(super_feature + "; " + q_feature)
        output = self.extract(q_feature, id_descs, query)        
        output = self.select(q_feature, output)
        
        return output

    def search(self, query, limit=3):
        # if self.from_local:
        #     id_descs = self.search_from_local(query, limit=limit)
        # else:
        #     id_descs = self.search_from_gp(query, limit=limit)
        id_descs = self.search_from_gp(query, limit=limit)
        
        return id_descs

    # def search_from_local(self, query, limit=3):
    #     query_embedding = self.encoder.encode(query, device="cuda").tolist()
        
    #     search_results = self.qdrant_client.search(
    #         collection_name="app_description",
    #         query_vector=query_embedding,
    #         query_filter=models.Filter(
    #             should=[
    #                 models.FieldCondition(
    #                     key="desc_length",
    #                     range=models.Range(gt=200)
    #                 )
    #             ]
    #         ),
    #         with_payload=True,
    #         limit=limit,
    #     )
    #     id_descs = [{"id": item.payload['appId'], "desc": item.payload['description']} for item in search_results]
    #     if self.print_debug:
    #         print(*[item["desc"] for item in id_descs], sep="\n==========================\n\n")
        
    #     return id_descs
    
    def search_from_gp(self, query, limit=3):
        search_results = google_play_scraper.search(
            query, lang="en", country="us", n_hits=30
        )
        id_descs = [{"id": app['appId'], "desc": app['description']} for app in search_results]
        id_descs = [item for item in id_descs if len(item["desc"]) >= 200]
        id_descs = id_descs[:limit]
        if self.print_debug:
            print(*[item["desc"] for item in id_descs], sep="\n==========================\n\n")
        
        return id_descs
    
    def extract(self, q_feature, id_descs, query):
        if all(item in query.keys() for item in ["super_feature", "super_feature_description", "feature", "sibling_features"]):
            batch_input = []
            for item in id_descs:
                input = {"feature_with_desc": q_feature, "app_description": item["desc"], 
                         "super_feature": query["super_feature"], 
                         "super_feature_description": query["super_feature_description"], 
                         "sub_features": query["sibling_features"]}
                batch_input.append(input)
            batch_output = self.feature_with_super_extraction_chain.batch(batch_input)
        else:
            batch_input = [{"feature_with_desc": q_feature, "app_description": item["desc"]} for item in id_descs]
            batch_output = self.feature_extraction_chain.batch(batch_input)
        
        # add app id for each feature
        feature_jsons = []
        for i in range(len(id_descs)):
            output = batch_output[i]
            output = select_code_block(output['text'])
            
            if self.print_debug: print(output)
            output = json.loads(output)
            for feature in output:
                feature["source-app-id"] = id_descs[i]["id"]
            output = json.dumps(output, indent=2)
            feature_jsons.append(output)
        
        return feature_jsons
    
    def select(self, q_feature, feature_jsons):
        output = self.select_feature_chain.predict(feature_with_desc=q_feature, features="\n\n".join(feature_jsons))
        output = select_code_block(output)
        
        if self.print_debug: print(output)        
        output = json.loads(output)

        return output


if __name__ == "__main__":
    gp = GPData(print_debug=True)
    output = gp.inspire(query={"feature": "health monitoring for elderly"})
    # output = gp.inspire(query={"feature": "Parking Space Finder", "feature_description": "This app connects drivers with available parking spaces through a marketplace, letting space owners rent their spots or helping users find free and paid parking nearby, while generating revenue through commissions and listing fees."})

    output = json.dumps(output, indent=2)
    print(output)
