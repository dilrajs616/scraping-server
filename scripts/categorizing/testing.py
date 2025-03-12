import json

category = {}

with open('cleaned_predefined_categories.json', 'r') as f:
    category = json.load(f)

count = []

for key in category.keys():
    count.append(key)

print(count)
