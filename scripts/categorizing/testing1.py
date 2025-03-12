import requests
import json
from url_type import check_url
from rapidfuzz import process, fuzz
from sentence_transformers import SentenceTransformer
import numpy as np

# Load embedding model
model = SentenceTransformer("all-MiniLM-L6-v2")

# Load predefined categories
with open("cleaned_predefined_categories.json", "r", encoding="utf-8") as f:
    predefined_categories = json.load(f)

# Convert predefined categories to embeddings
category_names = list(predefined_categories.keys())
category_embeddings = model.encode(category_names, normalize_embeddings=True)

def get_best_semantic_match(input_text):
    """Find the best category match based on semantic similarity."""
    input_embedding = model.encode([input_text], normalize_embeddings=True)
    
    # Compute cosine similarity with all predefined categories
    similarities = np.dot(category_embeddings, input_embedding.T).flatten()

    # Get the best match
    best_index = np.argmax(similarities)
    best_category = category_names[best_index]
    best_score = similarities[best_index]

    print(f"Semantic Match: {input_text} → {best_category} (Score: {best_score})")
    return best_category if best_score > 0.5 else "Uncategorized"


# Flatten subcategories for easier lookup
subcategories_mapping = {}
for main_cat, sub_cats in predefined_categories.items():
    for sub_cat in sub_cats:
        subcategories_mapping[sub_cat.lower()] = main_cat

def normalize_category(input_category, category_list):
    """Find the best matching category from the predefined list using fuzzy matching."""
    if not input_category:  # If input is empty, return a fallback category
        print("Skipping normalization for empty category")
        return "General"  # Return a sensible fallback category

    print(f"Normalizing category: {input_category}")
    match = process.extractOne(input_category, category_list, scorer=fuzz.token_sort_ratio)

    if not match or len(match) < 2:
        print("No match found or invalid match format")
        return next(iter(category_list), "General")  # Return first available category or "General" if empty

    matched_category, score = match[:2]  # Extract first two values safely
    print(f"Matched: {matched_category} with score: {score}")

    return matched_category  # Always return the best match


def process_llama_response(llama_response):
    """Normalize LLaMA response categories using semantic similarity."""
    print(f"Raw LLaMA response: {llama_response}")

    try:
        response = json.loads(llama_response.replace("'", "\""))
    except json.JSONDecodeError as e:
        print(f"JSON Decode Error: {e}")
        return {"error": "Invalid JSON response from LLaMA"}

    print(f"Parsed response: {response}")

    original_category = response.get("Category", "").strip()
    original_alt_category = response.get("Alternate Category", "").strip()

    # Use semantic matching instead of fuzzy matching
    category = get_best_semantic_match(original_category)
    alt_category = get_best_semantic_match(original_alt_category)

    return {
        "Category": category,
        "Sub Category": "",
        "Alternate Category": alt_category,
        "Alternate Sub Category": ""
    }


# Define the API URL
model_url = "http://localhost:11434/api/generate"

def ask_llama(payload):
    print(f"Sending payload: {payload}")
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
    format = {'Category': 'Category Name', 'Sub Category':'if exists here', 'Alternate Category':'if exists here', 'Alternate Sub Category': 'if exists here'}
    if prompt_type == "category":
        return {
            "model": "llama3:8b-instruct-fp16",
            "prompt": f"{content}, \n\nThis is content from website. Ignore useless information like cookies and login, forms etc from this content. What is the most probable category of this website. If content is ambiguous and can fall in two categories then tell both. Give response in this format {format}. NO NEED TO EXPLAIN ANYTHING, JUST TELL CATEGORY."
        }
    return {}

def categorize(url: str, content: str):
    try:
        print(f"Categorizing URL: {url}")
        result = check_url(url)
        if result:
            return result 
        
        # Generate the first prompt to determine category
        payload = generate_payload(f"{url.strip()} {content.strip()}", "category")
        response = ask_llama(payload)

        if response:
            response = response.strip()
            print(f"Raw model response: {response}")
            normalized_response = process_llama_response(response)
            print(f"Normalized response: {normalized_response}")
            return json.dumps(normalized_response, indent=4)
        else:
            return "did not get a response"
    except Exception as e:
        print(f"Exception occurred: {e}")
        return f"error occurred: {e}"
