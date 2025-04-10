#!/usr/bin/env python3
import numpy as np
from PIL import Image
import json
import os
import shutil
import itertools
import copy

verbose = True

# make sure that the script use the rigth working diretory
os.chdir(os.path.dirname(__file__))

OUTPUT_DIR = "../../build/armor_trim/assets"

def load_json(filepath):
    with open(filepath, "r") as file:
        data = json.load(file)
    return data

def save_json(filepath, data):
    with open(filepath, "w", newline="\n") as file:
        json.dump(data, file, indent=4)

def get_data(path):
    img = Image.open(path).convert("RGBA")
    return np.array(img)

# COLORIZE
def colorise(trim_image, color_index):
    new_trim_image = np.zeros([*trim_image.shape], dtype=np.uint8)
    for y in range(len(trim_image)):
        for x in range(len(trim_image[y])):
            new_trim_image[y,x] = trim_image[y,x]#[255, 255, 255, 255]#colors[color_index,i]
            for i in range(len(colors[0])):
                # print(colors[0,i], trim_image[y,x])
                if tuple(colors[0,i]) == tuple(trim_image[y,x]):
                    # try:
                    new_trim_image[y,x] = colors[color_index + 1,i]
                    # print(trim_image[y,x])
                        # print(new_trim_image[y,x])
                    # except KeyError:
                        # new_trim_image[y,x] = [0, 0, 0, 255]
    return new_trim_image

colors = np.array(Image.open("armor_trim_palette.png").convert("RGBA"))

palettes = ["redstone", "copper", "gold", "emerald", "diamond", "lapis", "amethyst", "quartz", "iron", "netherite", "resin"]
# trims = ["sentry", "vex", "wild", "coast", "dune", "wayfinder", "raiser", "shaper", "host", "ward", "silence", "tide", "snout", "rib", "eye", "spire"]
# armor_types = ["helmet", "chestplate", "leggings", "boots"]
# armor_materials = ["leather", "iron", "chainmail", "gold", "diamond", "netherite", "turtle"]

# trim_paths = [f"{armor_material}/{trim}" for trim in trims for armor_material in armor_materials]

PREPROCESS_EXT = ".preprocess"

def create_model(pwd, texture_path, cutout_path, texture_dest_dir, model_dest_path, model_template, cit_dest_path, cit_template):
    # model_dest_path = model_dest_path.replace("{palette}", palette)
    # print(cit_template)

    _, _, _, _, _, armor_type, material, trim, palette = model_dest_path.split("/")
    real_palette = palette
    if real_palette in material:
        real_palette = palette + "_darker"

    template_copy = copy.deepcopy(model_template)  # unnecessary copies
    cit_template_copy = copy.deepcopy(cit_template)
    if material == "leather":
        template_copy["textures"]["layer2"] = template_copy["textures"]["layer1"]
        template_copy["textures"]["layer1"] = "minecraft:item/{armor_type}/base/leather_overlay/{trim}"
    if material == "leather_overlay":
        return

    string = json.dumps(template_copy)
    string = replace_strings(pwd, string, material, trim, palette, real_palette, armor_type)
    model = json.loads(string)

    cit_template_string = "\n".join(cit_template_copy)
    cit_template_string = replace_strings(pwd, cit_template_string, material, trim, palette, real_palette, armor_type)

    path = model_dest_path + ".json"#f"{material}/{armor_type}/{trim}_{palette}.json"
    cit_path = cit_dest_path + ".properties"

    # print(cit_path)
    try:
        os.makedirs(os.path.join(pwd, os.path.dirname(path)))
    except FileExistsError:
        pass

    try:
        os.makedirs(os.path.join(pwd, os.path.dirname(cit_path)))
    except FileExistsError:
        pass

    save_json(os.path.join(pwd, path), model)
    with open(os.path.join(pwd, cit_path), "w") as f:
        f.write(cit_template_string)

def cutout(pwd, texture_path, cutout_path, texture_dest_dir, model_dest_path, model_template, cit_dest_path, cit_template):
    # print(model_dest_path)

    for palette in palettes:
        create_model(pwd, texture_path, cutout_path, texture_dest_dir, model_dest_path.replace("{palette}", palette), model_template, cit_dest_path.replace("{palette}", palette), cit_template)

    # cut out trim shape from armor to avoid z-fighting in item frames, in hand, on ground etc.
    texture_data = get_data(os.path.join(pwd, texture_path))
    cutout_data = get_data(os.path.join(pwd, cutout_path))

    for y in range(len(cutout_data)):
        for x in range(len(cutout_data[y])):
            if cutout_data[y, x, 3] != 0:
                texture_data[y, x] = [0, 0, 0, 0]

    texture = Image.fromarray(texture_data)
    dest_path = texture_dest_dir + ".png"
    try:
        os.mkdir(os.path.join(pwd, os.path.dirname(dest_path)))
    except FileExistsError:
        pass
    # print("Saving '" + os.path.join(pwd, dest_path) + "'")
    texture.save(os.path.join(pwd, dest_path))

def multi_cutout(pwd, texture_path, cutout_dir, cutout_names, texture_dest_dir, model_dest_path, model_template, cit_dest_path, cit_template):
    # print(texture_path, cutout_dir)
    for cutout_name in cutout_names:
        cutout_base_name = os.path.splitext(cutout_name)[0]
        # os.mkdir(os.path.join(pwd, texture_dest_dir, cutout_base_name))
        cutout(pwd, texture_path, os.path.join(cutout_dir, cutout_name), os.path.join(texture_dest_dir, cutout_base_name), model_dest_path.replace("{trim}", cutout_base_name), model_template, cit_dest_path.replace("{trim}", cutout_base_name), cit_template)

def override_multi_cutout(pwd, texture_path, cutout_dir, cutout_names, texture_dest_dir, model_dest_path, model_template, cit_dest_path, cit_template):
    cutout_override_dir = os.path.join(cutout_dir, os.path.splitext(os.path.basename(texture_path))[0])
    if os.path.exists(os.path.join(pwd, cutout_override_dir)):
        cutout_dir = cutout_override_dir
        # model_dest_path = model_dest_path.replace("{material2}", texture_base_name + "/")
    # model_dest_path = model_dest_path.replace("{material2}", "")
    multi_cutout(pwd, texture_path, cutout_dir, cutout_names, texture_dest_dir, model_dest_path, model_template, cit_dest_path, cit_template)
    os.remove(os.path.join(pwd, texture_path))

def multi_override_multi_cutout(pwd, texture_dir, texture_names, cutout_dir, cutout_names, texture_dest_dir, model_dest_path, model_template, cit_dest_path, cit_template):
    for texture_name in texture_names:
        texture_base_name = os.path.splitext(texture_name)[0]
        # os.mkdir(os.path.join(pwd, texture_dest_dir, texture_base_name))
        override_multi_cutout(pwd, os.path.join(texture_dir, texture_name), cutout_dir, cutout_names, os.path.join(texture_dest_dir, texture_base_name), model_dest_path.replace("{material}", texture_base_name), model_template, cit_dest_path.replace("{material}", texture_base_name), cit_template)

def replace_strings(pwd, string, material, trim, palette, real_palette, armor_type):
    override = os.path.isdir(os.path.join(f"../assets/minecraft/textures/item/{armor_type}/trim/{material}"))
    # print(override)

    string = string.replace("{material}", material)
    string = string.replace("{material2}", material + "/" if override else "")
    string = string.replace("{trim}", trim)
    string = string.replace("{palette}", palette)
    string = string.replace("{real_palette}", real_palette)
    string = string.replace("{armor_type}", armor_type)

    return string
#
# def multi_override_multi_model(pwd, variables, model_template, texture_dest_dir):
#     for armor_type in variables["type"]:
#         for material in variables["material"]:
#             for trim in variables["trim"]:
#                 for palette in variables["palette"]:
#                     template_copy = copy.deepcopy(model_template)
#                     if material == "leather":
#                         template_copy["textures"]["layer2"] = template_copy["textures"]["layer1"]
#                         template_copy["textures"]["layer1"] = "minecraft:item/helmet/base/{trim}"
#
#                     string = json.dumps(template_copy)
#                     string = replace_strings(pwd, string, material, trim, palette)
#
#                     model = json.loads(string)
#                     path = f"{material}_{armor_type}/{trim}_{palette}.json"
#
#                     try:
#                         os.makedirs(os.path.join(pwd, os.path.dirname(path)))
#                     except FileExistsError:
#                         pass
#                     save_json(os.path.join(pwd, path), model)
#

    # for key, lst in variables:
    #     for value in lst:
    #         string.replace("{" + key + "}", value)


def preprocess(file_path):
    json = load_json(os.path.join(file_path))
    print("Processing textures in '" + file_path + "' as " + json["mode"])
    match json["mode"]:
        case "multi_override_multi_cutout":
            multi_override_multi_cutout(os.path.dirname(file_path), json["texture_dir"], json["texture_names"], json["cutout_dir"], json["cutout_names"], json["texture_dest_dir"], json["model_dest_path"], json["model_template"], json["cit_dest_path"], json["cit_template"])
        case "multi_override_multi_model":
            multi_override_multi_model(os.path.dirname(file_path), json["variables"], json["model_template"], json["texture_dest_dir"])
        case _:
            raise ValueError("Invalid mode for " + file_path)

try:
    shutil.rmtree(OUTPUT_DIR)
except FileNotFoundError:
    pass

shutil.copytree("assets", OUTPUT_DIR)

for root, dirs, files in os.walk(OUTPUT_DIR):
    # print(root, dirs, files)
    for file_name in files:
        file_base_name, file_ext = os.path.splitext(file_name)
        if file_ext == PREPROCESS_EXT:
            # print("Preprocessing " + os.path.join(root, file_name))
            preprocess(os.path.join(root, file_name))


# try:
#     shutil.rmtree("../../../32/visual_armor_trims/assets")
# except FileNotFoundError:
#     pass

# shutil.copytree("../assets", "../../../22/visual_armor_trims/assets")


#
# for armor_type in armor_types:
    # for armor_material in armor_materials:
#
#
#     for trim_path in trims + trim_paths:  # FIX: try trim paths last so will overwrite any short trim paths
#
#
#
#
#
#
#
#
#
#
#         trim = trim_path.split("/")[-1]
#         partial_trim_dir_path = f"item/{armor_type}_trim/{trim_path}"
#         trim_dir_path = f"assets/minecraft/textures/{partial_trim_dir_path}"
#
#         try:
#             trim_image_data = get_data(f"{trim_dir_path}.png")
#         except FileNotFoundError:
#             continue
#
#         for trim_palette_index in range(len(palettes)):
#
#             trim_palette = palettes[trim_palette_index]
#
#             partial_trim_file_path = f"{partial_trim_dir_path}/{trim_palette}"
#             trim_file_path = f"{trim_dir_path}/{trim_palette}"
#
#             try:
#                 os.makedirs(f"../{trim_dir_path}")
#             except FileExistsError:
#                 pass
#
#             trim_image = Image.fromarray(colorise(trim_image_data, trim_palette_index))
#             trim_image.save(f"../{trim_file_path}.png")
#
#             verbose and print(f"Created output {trim_file_path}")
#
#
#         for armor_material in armor_materials:
#
#             if armor_material == "turtle" and armor_type != "helmet":
#                 continue
#
#             item_name = "{}_{}".format("golden" if armor_material == "gold" else armor_material, armor_type)
#
#             partial_dir_path = f"item/{item_name}"
#             partial_file_path = f"{partial_dir_path}/{trim}"
#             dir_path = f"assets/minecraft/textures/{partial_dir_path}"
#             file_path = f"assets/minecraft/textures/{partial_file_path}"
#
#             try:
#                 os.makedirs(f"../{dir_path}")
#             except FileExistsError:
#                 pass
#
#             # cut out trim shape from armor to avoid z-fighting in item frames, in hand, on ground etc.
#             item_image_mask_data = get_data(f"{dir_path}.png")
#
#             for y in range(len(trim_image_data)):
#                 for x in range(len(trim_image_data[y])):
#                     if trim_image_data[y, x, 3] != 0:
#                         item_image_mask_data[y, x] = [0, 0, 0, 0]
#
#             item_image_mask = Image.fromarray(item_image_mask_data)
#             item_image_mask.save(f"../{file_path}.png")
#
#
#             # also perform cut out on the leather overlay (trims display over overlays)
#             if armor_material == "leather":
#
#                 try:
#                     os.makedirs(f"../{dir_path}_overlay")
#                 except FileExistsError:
#                     pass
#
#                 item_image_overlay_mask_data = get_data(f"{dir_path}_overlay.png")
#
#                 for y in range(len(trim_image_data)):
#                     for x in range(len(trim_image_data[y])):
#                         if trim_image_data[y, x, 3] != 0:
#                             item_image_overlay_mask_data[y, x] = [0 ,0, 0, 0]
#
#                 item_image_overlay_mask = Image.fromarray(item_image_overlay_mask_data)
#                 item_image_overlay_mask.save(f"../{dir_path}_overlay/{trim}.png")
#
#
#             for trim_palette_index in range(len(palettes)):
#
#                 if palettes[trim_palette_index] in ["gold_darker", "diamond_darker", "iron_darker", "netherite_darker"]:
#                     continue
#
#                 trim_material = palettes[trim_palette_index]
#                 trim_palette = palettes[trim_palette_index + (1 if armor_material == trim_material else 0)]
#
#                 # trim_palette == armor_material and print(trim_palette, trim_material)
#
#                 partial_trim_file_path = f"{partial_trim_dir_path}/{trim_palette}"
#                 trim_file_path = f"{trim_dir_path}/{trim_palette}"
#
#                 if armor_material == "leather":
#                     model_data = {
#                             "parent": "minecraft:item/generated",
#                             "textures": {
#                                 "layer0": f"minecraft:{partial_file_path}",
#                                 "layer1": f"minecraft:{partial_dir_path}_overlay/{trim}",
#                                 "layer2": f"minecraft:{partial_trim_file_path}"
#                             }
#                         }
#
#                 else:
#                     model_data = {
#                             "parent": "minecraft:item/generated",
#                             "textures": {
#                                 "layer0": f"minecraft:{partial_file_path}",
#                                 "layer1": f"minecraft:{partial_trim_file_path}"
#                             }
#                         }
#
#                 partial_model_dir_path = f"item/{item_name}/{trim}"
#                 partial_model_file_path = f"item/{item_name}/{trim}/{trim_material}"
#                 model_dir_path = f"assets/minecraft/models/{partial_model_dir_path}"
#                 model_file_path = f"{model_dir_path}/{trim_material}"
#
#                 try:
#                     os.makedirs(f"../{model_dir_path}")
#                 except FileExistsError:
#                     pass
#
#                 save_json(f"../{model_file_path}.json", model_data)
#
#                 verbose and print(f"Created model {model_file_path}.json")
#
#
#                 cit_dir_path = f"assets/minecraft/optifine/cit/{partial_model_dir_path}"
#                 cit_file_path = f"{cit_dir_path}/{trim_material}"
#
#                 try:
#                     os.makedirs(f"../{cit_dir_path}")
#                 except FileExistsError:
#                     pass
#
#                 with open(f"../{cit_file_path}.properties", 'w') as f:
#
#                     f.write(
# f"""type=item
# matchItems={item_name}
# model={partial_model_file_path}
# nbt.Trim.material=minecraft:{trim_material}
# nbt.Trim.pattern=minecraft:{trim}
# """
# )
#
#                 verbose and print(f"Created CIT {cit_file_path}.properties")
