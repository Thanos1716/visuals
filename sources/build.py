#!/usr/bin/env python3
import glob
import json
import os
import shutil
from contextlib import suppress

from conflict_modules import (
    ATLASES_MODULE,
    buid_new_atlases,
    print_conflicts,
    test_conflict_files,
    write_atlases,
)

PACKS_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../packs"))
BUILD_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../build"))

def load_json(filepath):
    with open(filepath, "r") as file:
        data = json.load(file)
    return data

def save_json(filepath, data):
    with open(filepath, "w", newline="\n") as file:
        json.dump(data, file, indent=2)


def copyfile(src, dst):
    shutil.copy(src, dst)

def copytree(src, dst):
    shutil.copytree(src, dst,
        copy_function=copyfile,
        dirs_exist_ok=True,
    )

def makedirs(name):
    os.makedirs(name, exist_ok=True)


def iter_modules(root_dir):
    _, dirs, _ = next(os.walk(root_dir))
    for module in dirs:
        if module in ("assets", ATLASES_MODULE):
            continue
        yield module

def test_conflict_exit(root_dir):
    conflicts = test_conflict_files(root_dir)
    if conflicts:
        print_conflicts(conflicts)
        print("Aborted. Enter to exit.")
        input()
        exit(1)

def copy_root_files(source_dir, ouptput_dir):
    makedirs(os.path.join(ouptput_dir))
    
    # copy pack.mcmeta without the overlays
    pack_mcmeta = load_json(os.path.join(source_dir, "pack.mcmeta"))
    pack_mcmeta.pop("overlays", None)
    save_json(os.path.join(ouptput_dir, "pack.mcmeta"), pack_mcmeta)
    
    # use inner pack.png
    path_icon = os.path.join(source_dir, "pack.png")
    if not os.path.exists(path_icon):
        # use top/global pack.png
        path_icon = os.path.join(source_dir, "..", "pack.png")
    copyfile(
        path_icon,
        os.path.join(ouptput_dir, "pack.png")
    )
    
    # copy license.txt
    copyfile(
        os.path.join(PACKS_DIR, "..", "license.txt"),
        os.path.join(ouptput_dir, "license.txt")
    )


print("-=< Building resource packs >=-")

###################
## visuals/items ##
###################
print()
print("> Building 'visuals-items'...")

items_source = os.path.join(PACKS_DIR, "items")
items_ouptput = os.path.join(BUILD_DIR, "items")
items_modules = os.path.join(BUILD_DIR, "items-modules")
items_modules_zip = os.path.join(BUILD_DIR, "items-modules-zip")
items_ouptput_zip = os.path.join(BUILD_DIR, "visuals-items")

# clean previous build files
shutil.rmtree(items_ouptput, ignore_errors=True)
shutil.rmtree(items_modules, ignore_errors=True)
shutil.rmtree(items_modules_zip, ignore_errors=True)
with suppress(FileNotFoundError):
    os.remove(items_ouptput_zip+".zip")

makedirs(items_ouptput)
makedirs(items_modules)

print(">> Check for conflict files 'items'...")
test_conflict_exit(items_source)

print(">> Copy 'visuals-items' root files...")
copy_root_files(items_source, items_ouptput)

for module in iter_modules(items_source):
    print(f">> Processing module {module!r} (items)...")
    
    # step 1:
    # create the individual module resource pack
    copy_root_files(
        os.path.join(items_source, module),
        os.path.join(items_modules, module),
    )
    copytree(
        os.path.join(items_source, module, "assets"),
        os.path.join(items_modules, module, "assets")
    )
    
    # step 2:
    # merge the module into the main resource pack
    copytree(
        os.path.join(items_modules, module, "assets"),
        os.path.join(items_ouptput, "assets")
    )
    for atlases in glob.iglob("assets/**/atlases/", root_dir=items_ouptput, recursive=True):
        shutil.rmtree(os.path.join(items_ouptput, atlases))

print(">> Merging 'visuals-items' atlases...")
write_atlases(items_ouptput, buid_new_atlases(items_modules))


####################
## visuals/blocks ##
####################
print()
print("> Building 'visuals-blocks'...")

blocks_source = os.path.join(PACKS_DIR, "blocks")
blocks_ouptput = os.path.join(BUILD_DIR, "blocks")
blocks_modules = os.path.join(BUILD_DIR, "blocks-modules")
blocks_modules_zip = os.path.join(BUILD_DIR, "blocks-modules-zip")
blocks_ouptput_zip = os.path.join(BUILD_DIR, "visuals-blocks")

# clean previous build files
shutil.rmtree(blocks_ouptput, ignore_errors=True)
shutil.rmtree(blocks_modules, ignore_errors=True)
shutil.rmtree(blocks_modules_zip, ignore_errors=True)
with suppress(FileNotFoundError):
    os.remove(blocks_ouptput_zip+".zip")

makedirs(blocks_ouptput)
makedirs(blocks_modules)

print(">> Check for conflict files 'blocks'...")
test_conflict_exit(blocks_source)

print(">> Copy 'visuals-blocks' root files...")
copy_root_files(blocks_source, blocks_ouptput)

for module in iter_modules(blocks_source):
    print(f">> Processing module {module!r}  (block)...")
    
    # step 1:
    # create the individual module resource pack
    copy_root_files(
        os.path.join(blocks_source, module),
        os.path.join(blocks_modules, module),
    )
    
    # step 2:
    # first, importing the items module (if exist)
    # then apply the block module
    with suppress(FileNotFoundError):
        copytree(
            os.path.join(items_source, module, "assets"),
            os.path.join(blocks_modules, module, "assets")
        )
    copytree(
        os.path.join(blocks_source, module, "assets"),
        os.path.join(blocks_modules, module, "assets")
    )
    
    # step 3:
    # merge the module into the main resource pack
    copytree(
        os.path.join(blocks_modules, module, "assets"),
        os.path.join(blocks_ouptput, "assets")
    )
    for atlases in glob.iglob("assets/**/atlases/", root_dir=blocks_ouptput, recursive=True):
        shutil.rmtree(os.path.join(blocks_ouptput, atlases))

print(">> Merging 'visuals-blocks' atlases...")
write_atlases(blocks_ouptput, buid_new_atlases(blocks_modules))


##############
## Make zip ##
##############
print()
print("> Make zip 'visuals-items'...")
shutil.make_archive(items_ouptput_zip, "zip", os.path.join(items_ouptput))

for module in iter_modules(items_modules):
    print(f">> Make zip {module!r} (items)...")
    shutil.make_archive(os.path.join(items_modules_zip, module), "zip", os.path.join(items_modules, module))

print()
print("> Make zip 'visuals-blocks'...")
shutil.make_archive(blocks_ouptput_zip, "zip", os.path.join(blocks_ouptput))

for module in iter_modules(blocks_modules):
    print(f">> Make zip {module!r} (blocks)...")
    shutil.make_archive(os.path.join(blocks_modules_zip, module), "zip", os.path.join(blocks_modules, module))
