import os


def remove_duplicate_items(l: list):
    final_list = []
    for item in l:
        if item not in final_list:
            final_list.append(item)
    return final_list


material_pairs = []

for file in os.listdir(os.getcwd()):
    material_pair = []
    with open(file, "r") as f:
        for line in f.readlines():
            line = line.lstrip().rstrip()
            if line.startswith("material:"):
                material_pair.append(line)
            if line.startswith("sub_material:"):
                material_pair.append(line)
                material_pairs.append(material_pair)
                material_pair = []

sorted_mat_pairs = sorted(remove_duplicate_items(material_pairs))
m = f"Confirmed material pair number: {len(sorted_mat_pairs)}\n"
lines = ""
lines += m
for pair in sorted_mat_pairs:
    lines += "\n\n"
    lines += "\n".join(pair)
lines += "\n"

with open("../confirmed_material_pairs.yml", "w") as f:
    f.write(lines)
