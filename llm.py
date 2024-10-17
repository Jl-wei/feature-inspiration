import os
import json
from langchain.chains import LLMChain
from langchain_community.chat_models import ChatOpenAI
from langchain_core.prompts import (
    PromptTemplate,
    ChatPromptTemplate,
    HumanMessagePromptTemplate,
)
from langchain_core.messages import SystemMessage
from utils import *



def get_system_message():
    message = SystemMessage(content='''
You are an expert in mobile app development and requirements engineering. 
You excel at decomposing high-level features into detailed sub-features.
''')
    return message

def get_feature_refine_template():
    template = '''
**Feature**
```
{feature}: {feature_description}
```
Given the mobile app feature above, please refine it to a list of sub-features.
Ensure that the number of sub-features is 5.
The output should be a list of JSON formatted objects like this:
[{{
"sub-feature": sub-feature,
"description": description
}}]
'''
    prompt = HumanMessagePromptTemplate(
        prompt=PromptTemplate(
            template=template,
            input_variables=["feature", "feature_description"],
        )
    )
    prompt_template = ChatPromptTemplate.from_messages([get_system_message(), prompt])
    return prompt_template

def get_feature_with_super_feature_refine_template():
    template = '''
**Super Feature**
```
super-feature: {super_feature}
description: {super_feature_description}
```
Knowing that the feature "{super_feature}" above is refined into a list of the following features:
```
{sub_features}
```

Please refine the following to a list of sub-features.
Ensure that the number of sub-features is 5.

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
            input_variables=["feature_with_desc", "super_feature", "super_feature_description", "sub_features"],
        )
    )
    prompt_template = ChatPromptTemplate.from_messages([get_system_message(), prompt])
    return prompt_template


class LLM:
    def __init__(self, model_name="gpt-4o"):
        chat_model = ChatOpenAI(model=model_name, temperature=0, openai_api_key=os.environ["OPENAI_API_KEY"])
        self.feature_refine_chain = LLMChain(llm=chat_model, prompt=get_feature_refine_template())
        self.feature_with_super_feature_refine_chain = LLMChain(llm=chat_model, prompt=get_feature_with_super_feature_refine_template())
    
    def inspire(self, query):
        if all(item in query.keys() for item in ["super_feature", "super_feature_description", "feature", "sibling_features"]):
            output = self.feature_with_super_feature_refine_chain.predict(
                feature_with_desc=query["feature"] + ":" + query["feature_description"], 
                super_feature=query["super_feature"],
                super_feature_description=query["super_feature_description"],
                sub_features=query["sibling_features"]
            )
        elif "feature" in query:
            if "feature_description" not in query: query["feature_description"] = ""
            
            output = self.feature_refine_chain.predict(
                feature=query["feature"],
                feature_description=query["feature_description"]
            )
        else:
            output = ""
        output = select_code_block(output)
        json_output = json.loads(output)
        
        return json_output

if __name__ == "__main__":
    llm = LLM()
    output = llm.inspire(query={"feature": "health monitoring for elderly"})
    # output = llm.inspire(query={"feature": "Parking Space Finder", "feature_description": "This app connects drivers with available parking spaces through a marketplace, letting space owners rent their spots or helping users find free and paid parking nearby, while generating revenue through commissions and listing fees."})

    output = json.dumps(output, indent=2)
    print(output)
