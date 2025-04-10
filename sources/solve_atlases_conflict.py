#!/usr/bin/env python3
import glob
import json
import os
import shutil
from collections import defaultdict

PACKS_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../packs"))

def load_json(filepath):
    with open(filepath, "r") as file:
        data = json.load(file)
    return data

def save_json(filepath, data):
    with open(filepath, "w", newline="\n") as file:
        json.dump(data, file, indent=4)


ATLASES_MODULE = "zz_atlases_resolvers"

def read_atlases(source_dir):
    rslt = {}
    for file in glob.iglob("**/atlases/*.json", root_dir=source_dir, recursive=True):
        rslt[file] = load_json(os.path.join(source_dir, file))["sources"]
    return rslt

def buid_new_atlases(source_dir):
    rslt = defaultdict(list)
    root, dirs, files = next(os.walk(source_dir))
    for subdir in dirs:
        if subdir in ("assets", ATLASES_MODULE):
            continue
        for k,v in read_atlases(os.path.join(source_dir, subdir)).items():
            rslt[k].extend(v)
    return rslt

def write_atlases(target_dir, atlases):
    for file,sources in atlases.items():
        os.makedirs(os.path.join(target_dir, os.path.dirname(file)), exist_ok=True)
        save_json(os.path.join(target_dir, file), {"sources": sources})


def solve_atlases_conflict(target_dir):
    atlases_original = read_atlases(os.path.join(target_dir, ATLASES_MODULE))
    atlases_new = buid_new_atlases(os.path.abspath(target_dir))
    
    if atlases_original != atlases_new:
        try:
            shutil.rmtree(os.path.join(target_dir, ATLASES_MODULE, "assets"))
        except FileNotFoundError:
            pass
        write_atlases(os.path.join(target_dir, ATLASES_MODULE), atlases_new)
        return True
    else:
        return False


if __name__ == "__main__":
    print("> Merging 'visuals' atlases...")
    if solve_atlases_conflict(os.path.join(PACKS_DIR, "visuals")):
        print("INFO: 'visuals' atlases files has been updated.")
    else:
        print("INFO: 'visuals' atlases files not changed.")
    
    print("> Merging 'blocks' atlases...")
    if solve_atlases_conflict(os.path.join(PACKS_DIR, "blocks")):
        print("INFO: 'blocks' atlases files has been updated.")
    else:
        print("INFO: 'blocks' atlases files not changed.")
    
    print("Enter to exit.")
    input()
