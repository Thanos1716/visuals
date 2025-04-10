#!/usr/bin/env python3
import json
import os

from solve_atlases_conflict import solve_atlases_conflict

TARGET_DIR = "../packs/items"
# move the working diretory to the target diretory
os.chdir(os.path.abspath(os.path.join(os.path.dirname(__file__), TARGET_DIR)))

def load_json(filepath):
    with open(filepath, "r") as file:
        data = json.load(file)
    return data

def save_json(filepath, data):
    with open(filepath, "w", newline="\n") as file:
        json.dump(data, file, indent=2)


if solve_atlases_conflict(os.path.abspath(".")):
    print("INFO: atlases files has been updated.")
    print()


print("type exit or none to close.")
EXIT_NAME = ("", "exit", "none")
while True:
    print()
    print("Type the name of the new module to add to Visuals:")
    name = input("> ").strip().lower().replace(" ", "_")
    if name in EXIT_NAME:
        break
    if os.path.exists(name):
        print(f"Aborted: A module with the name {name} already exist.")
        continue
    
    mcmeta = load_json("pack.mcmeta")
    new_mcmeta = mcmeta.copy()
    new_mcmeta.pop("overlays")
    os.makedirs(name, exist_ok=True)
    save_json(os.path.join(name, "pack.mcmeta"), new_mcmeta)
    os.makedirs(os.path.join(name, "assets/minecraft/items"), exist_ok=True)
    os.makedirs(os.path.join(name, "assets/minecraft/models/item"), exist_ok=True)
    os.makedirs(os.path.join(name, "assets/minecraft/textures/item"), exist_ok=True)
    # os.makedirs(os.path.join(name, "assets/minecraft/models/block"), exist_ok=True)
    # os.makedirs(os.path.join(name, "assets/minecraft/textures/block"), exist_ok=True)
    
    overlays = mcmeta["overlays"]["entries"]
    overlays.append({
        "directory": name,
        "formats": [55, 1000] # ensure that the overlay is enable by default
    })
    mcmeta["overlays"]["entries"] = list(sorted(overlays, key=lambda x: x["directory"]))
    save_json("pack.mcmeta", mcmeta)
