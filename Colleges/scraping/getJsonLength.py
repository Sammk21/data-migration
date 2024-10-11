import json

# Open and read the JSON file
with open('./new10.json', 'r') as file:
    data = json.load(file)

# Check if the data is a list (array)
if isinstance(data, list):
    number_of_elements = len(data)
    print("Number of elements:", number_of_elements)
else:
    print("The JSON data is not an array.")
