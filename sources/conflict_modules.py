#!/usr/bin/env python3
import glob
import json
import hashlib
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


def test_conflict_files(root_dir):
    file_map = defaultdict(dict)
    root, dirs, files = next(os.walk(root_dir))
    for module in dirs:
        if module in ("assets", ATLASES_MODULE):
            continue
        for file in glob.iglob("assets/**/*.*", root_dir=os.path.join(root_dir, module), recursive=True):
            split = file.split(os.path.sep)
            if split[2] == "atlases":
                continue
            with open(os.path.join(root_dir, module, file), "rb") as f:
                hash = hashlib.file_digest(f, "sha1")
            file_map[file.replace("\\", "/")][hash.hexdigest()] = module
    
    rslt = {}
    for file,hash_map in file_map.items():
        if len(hash_map) > 1:
            rslt[file] = sorted(hash_map.values())
    return rslt

def print_conflicts(conflict_map):
    for file,modules in conflict_map.items():
        print(f"ERROR: A file has a conflict error: {file!r}")
        print("\tModules in conflict:", ", ".join(modules))


def iter_pack_names():
    _, dirs, _ = next(os.walk(PACKS_DIR))
    dirs.remove('items')
    yield "items"
    for name in dirs:
        yield name

if __name__ == "__main__":
    for name in iter_pack_names():
        print(f"> Check for conflict files {name!r}...")
        conflicts = test_conflict_files(os.path.join(PACKS_DIR, name))
        if conflicts:
            print_conflicts(conflicts)
        else:
            print("INFO: {name!r} no conflict files.")
        
        print()
        print(f"> Merging {name!r} atlases...")
        if solve_atlases_conflict(os.path.join(PACKS_DIR, name)):
            print("INFO: {name!r} atlases files has been updated.")
        else:
            print("INFO: {name!r} atlases files not changed.")
        
        print()
    
    print("Enter to exit.")
    input()
