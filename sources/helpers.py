import json

def load_json(filepath):
    with open(filepath, "r") as file:
        data = json.load(file)
    return data

def save_json(filepath, data):
    with open(filepath, "w", newline="\n") as file:
        json.dump(data, file, indent=2)
