#!/usr/bin/env python3
import glob
import os
import shutil
from contextlib import suppress
from helpers import load_json, save_json

from conflict_modules import (
    ATLASES_MODULE,
    buid_new_atlases,
    print_conflicts,
    test_conflict_files,
    write_atlases,
)

PACKS_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../packs"))
BUILD_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../build"))

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


class PacksFolders:
    def __init__(self, name):
        self.name = name
        self.full_name = f"visuals-{name}"
        self.source = os.path.join(PACKS_DIR, name)
        self.ouptput = os.path.join(BUILD_DIR, name)
        self.modules = os.path.join(BUILD_DIR, f"{name}-modules")
        self.modules_zip = os.path.join(BUILD_DIR, f"{name}-modules-zip")
        # don't add '.zip', since shutil.make_archive automaticly add it
        self.ouptput_zip = os.path.join(BUILD_DIR, self.full_name)
        
        self.all = [
            self.source,
            self.ouptput,
            self.modules,
            self.modules_zip,
            self.ouptput_zip,
        ]

def iter_packs():
    _, dirs, _ = next(os.walk(PACKS_DIR))
    dirs.remove("items")
    yield PacksFolders("items")
    for name in dirs:
        yield PacksFolders(name)


print("-=< Building resource packs >=-")

# clean previous builds
#######################
print()
for pack in iter_packs():
    print(f"> Cleaning previous {pack.name!r} builds files...")
    shutil.rmtree(pack.ouptput, ignore_errors=True)
    shutil.rmtree(pack.modules, ignore_errors=True)
    shutil.rmtree(pack.modules_zip, ignore_errors=True)
    with suppress(FileNotFoundError):
        os.remove(pack.ouptput_zip+".zip")


# build each packs
# each packs is a "overlays" of 'items'
#######################################
items_pack = PacksFolders("items")
for pack in iter_packs():
    print()
    print(f"> Building {pack.full_name!r}...")
    
    makedirs(pack.ouptput)
    makedirs(pack.modules)
    
    print(f">> Check for conflict files {pack.full_name!r}...")
    test_conflict_exit(pack.source)
    
    print(f">> Copy {pack.full_name!r} root files...")
    copy_root_files(pack.source, pack.ouptput)
    
    for module in iter_modules(pack.source):
        print(f">> Processing module {module!r} ({pack.name})...")
        
        # step 1:
        # create the individual module resource pack
        copy_root_files(
            os.path.join(pack.source, module),
            os.path.join(pack.modules, module),
        )
        
        # step 2.1:
        # if not 'items' pack,
        # first importing the corresponding 'items' module (if exist)
        if pack.name != "items":
            with suppress(FileNotFoundError):
                copytree(
                    os.path.join(items_pack.source, module, "assets"),
                    os.path.join(pack.modules, module, "assets")
                )
        # step 2.2:
        # import the module content
        copytree(
            os.path.join(pack.source, module, "assets"),
            os.path.join(pack.modules, module, "assets")
        )
        
        # step 3:
        # merge the module into the main resource pack
        copytree(
            os.path.join(pack.modules, module, "assets"),
            os.path.join(pack.ouptput, "assets")
        )
    
    print(f">> Merging {pack.full_name!r} atlases...")
    for atlases in glob.iglob("assets/**/atlases/", root_dir=pack.ouptput, recursive=True):
        shutil.rmtree(os.path.join(pack.ouptput, atlases))
    write_atlases(pack.ouptput, buid_new_atlases(pack.modules))


## Make zip
###########
for pack in iter_packs():
    print()
    print(f"> Make zip {pack.full_name!r}...")
    shutil.make_archive(pack.ouptput_zip, "zip", os.path.join(pack.ouptput))
    
    for module in iter_modules(pack.modules):
        print(f">> Make zip {module!r} ({pack.name})...")
        shutil.make_archive(os.path.join(pack.modules_zip, module), "zip", os.path.join(pack.modules, module))
