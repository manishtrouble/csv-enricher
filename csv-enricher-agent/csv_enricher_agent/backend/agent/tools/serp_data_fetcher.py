from langchain.tools import tool
import json
import requests
import serpapi
from serpapi import GoogleSearch
@tool
def search(query:str) -> json:
    """Performs a google search for a query and returns a json""" 
    SERP_API_KEY = "cc6b0293dc8ff5eeeb96f3442e940f51d9103682588e23f3ea9f337b0aba532c"
    search_url = "https://serpapi.com/search.json"

    params = {
        "q": f"{query}",  
        "api_key": SERP_API_KEY,

    }

    search = GoogleSearch(params)
    results = search.get_dict()
    related_questions = results.get("related_questions", [])
    organic_results = results.get("organic_results", [])

    # Combine them into a dictionary
    combined_results = {
        "related_questions": related_questions,
        "organic_results": organic_results
    }
    # ai_overview = results["ai_overview"]
    with open('data.json', 'w', encoding='utf-8') as f:
        json.dump(combined_results, f, ensure_ascii=False, indent=4)
    return combined_results