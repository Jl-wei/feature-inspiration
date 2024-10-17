import pandas as pd
import re
import demoji
import os

from lingua import Language, LanguageDetectorBuilder
from pymongo.mongo_client import MongoClient


def is_english(text):
    detector = LanguageDetectorBuilder.from_all_spoken_languages().build()
    if pd.isnull(text):
        return False
    else:
        return detector.detect_language_of(text) == Language.ENGLISH

def contain_url(sent):
    regex = r"(?i)\b((?:https?://|www\d{0,3}[.]|[a-z0-9.\-]+[.][a-z]{2,4}/)(?:[^\s()<>]+|\(([^\s()<>]+|(\([^\s()<>]+\)))*\))+(?:\(([^\s()<>]+|(\([^\s()<>]+\)))*\)|[^\s`!()\[\]{};:'\".,<>?«»“”‘’]))"
    url = re.match(regex, sent)
    return bool(url)

def contain_email(sent):
    regex = r'[^@]+@[^@]+\.[^@]+'
    email = re.match(regex, sent)
    return bool(email)

def contain_words(sent):
    word_list = ["privacy policy", "terms of service", "terms and conditions", 
                 "free trial", "free download", "subscription info", "try for free", "paid subscription",
                 "contact us", "about ads", "rated", "rating", "compatible device"]
    detected_words = [ele for ele in word_list if(ele in sent.lower())]
    return len(detected_words) > 0

def check_sent(sent):
    return not (contain_url(sent) or contain_email(sent) or contain_words(sent))

def hide_appname(text, full_app_name):
    app_name = full_app_name.split(":")[0].strip()
    text = text.replace(full_app_name, "<APP>")
    text = text.replace(app_name, "<APP>")
    return text

def process_desc(desc):
    result = ''
    
    if is_english(desc):
        desc = desc.replace("\r", "")
        desc= "\n".join(list(filter(check_sent, desc.split("\n"))))
        result = demoji.replace(desc, '')
        
    return result


if __name__ == "__main__":
    uri = os.environ['MONGODB_URI']
    mongo_client = MongoClient(uri)
    mongo_coll = mongo_client['google_play']['app_v2']
    
    result = mongo_coll.aggregate([{"$sample": {"size": 1}}])
    sample_app = result.next()
    
    print(sample_app['description'])
    print("================================")
    print(process_desc(sample_app['description']))
