import requests
import json
from scripts.categorizing.url_type import check_url
from sentence_transformers import SentenceTransformer
import numpy as np

# Load embedding model
model = SentenceTransformer("all-MiniLM-L6-v2")

# Load predefined categories
with open("scripts/categorizing/cleaned_predefined_categories.json", "r", encoding="utf-8") as f:
    predefined_categories = json.load(f)

# Convert predefined categories to embeddings
category_names = list(predefined_categories.keys())
category_embeddings = model.encode(category_names, normalize_embeddings=True)

def get_best_semantic_match(input_text):
    """Find the best category match based on semantic similarity."""
    input_embedding = model.encode([input_text], normalize_embeddings=True)
    # Compute cosine similarity with all predefined categories
    similarities = np.dot(category_embeddings, input_embedding.T).flatten()
    best_index = np.argmax(similarities)
    best_category = category_names[best_index]
    best_score = similarities[best_index]
    return best_category if best_score > 0.5 else "Uncategorized"

def process_llama_response(llama_response):
    """Normalize LLaMA response categories using semantic similarity."""
    try:
        # Attempt to parse the response as JSON.
        response = json.loads(llama_response.replace("'", "\""))
    except json.JSONDecodeError as e:
        print(f"JSON Decode Error: {e}")
        return {"error": "Invalid JSON response from LLaMA"}
    
    original_category = response.get("Category")
    original_alt_category = response.get("Alternate Category")

    if not original_category or original_category.lower() == "null":
        original_category = "Uncategorized"
    if not original_alt_category or original_alt_category.lower() == "null":
        original_alt_category = "Uncategorized"
    
    # Use semantic matching to refine the category
    category = get_best_semantic_match(original_category.strip())
    alt_category = get_best_semantic_match(original_alt_category.strip())
    if alt_category == category:
        alt_category = ""
    
    return {
        "Category": category,
        "Alternate Category": alt_category
    }

# Define the API URL for Ollama
model_url = "http://localhost:11434/api/generate"

def ask_llama(payload):
    with requests.post(model_url, json=payload, stream=True) as response:
        if response.status_code == 200:
            full_response = ""
            for line in response.iter_lines():
                if line:
                    data = json.loads(line.decode('utf-8'))
                    full_response += data.get("response", "")
                    if data.get("done", False):
                        return full_response
            return full_response
        else:
            print(f"Request failed with status code {response.status_code}")
    return None

def generate_payload(content, prompt_type):
    example_format = '{"Category": "Category Name", "Alternate Category": "if exists here"}'
    if prompt_type == "category":
        return {
            "model": "my-llama3",
            "prompt": (f"{content}, \n\n"
                       f"This is content from a website. Ignore useless information like cookies, login forms, etc. "
                       f"Understand the context carefully and tell What is the most probable category of this website? "
                       f"Respond with a JSON object in this format: {example_format}. "
                       "NO NEED TO EXPLAIN ANYTHING, JUST TELL CATEGORY.")
        }
    return {}

def categorize(url: str, content: str):
    try:
        print(f"Categorizing URL: {url}")
        # If check_url returns a result, use that directly.
        result = check_url(url)
        if result:
            return result 
        
        # Generate payload and ask the model
        payload = generate_payload(f"{url.strip()} {content.strip()}", "category")
        response = ask_llama(payload)
        if response:
            print(f"response is {response}")
            normalized_response = process_llama_response(response)
            return json.dumps(normalized_response, indent=4)
        else:
            return json.dumps({
                "Category": "Uncategorized",
                "Alternate Category": ""
            }, indent=4)
    except Exception as e:
        print(f"Exception occurred: {e}")
        return json.dumps({
                "Category": "Uncategorized",
                "Alternate Category": ""
            }, indent=4)
