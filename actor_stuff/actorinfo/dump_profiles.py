import os
import re


def remove_dup(l1: list):
    final_list = []
    for item in l1:
        if not item in final_list:
            final_list.append(item)
    return final_list


with open(os.path.join(os.getcwd(), "ActorInfo.product.yml"), "r") as f:
    matches = re.findall("(profile: )(.*)(\n|,)", f.read())
    uniq = remove_dup(matches)
    matches2 = []
    for match in uniq:
        matches2.append("profile: " + re.sub("(,| )(.*)(,| )", "", match[1]).rstrip("}").rstrip(","))
    uniq2 = sorted(remove_dup(matches2))

with open("../actorinfo_profiles.yml", "w") as f:
    f.write("\n".join(uniq2) + "\n")
