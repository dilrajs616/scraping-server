import json
from rapidfuzz import process, fuzz

categories_dict = {}

with open("cleaned_predefined_categories.json", 'r') as f:
    categories_dict = json.load(f)

count = 0

for key in categories_dict.keys():
    count += 1

print(count)