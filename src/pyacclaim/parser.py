# https://research.cs.wisc.edu/graphics/Courses/cs-838-1999/Jeff/ASF-AMC.html

import numpy as np
import warnings
from . import Bone


def loadASF(filepath, verbose=True):
    if verbose:
        print("[loadASF] Reading contents of", filepath)

    with open(filepath) as f:
        data = f.read().splitlines()

    # Find all the sections
    sections = {}
    prev_section = None
    for line_index, line in enumerate(data):
        if line[0] == ":":
            tokens = line.strip().split()
            section_name = tokens[0][1:]
            assert (
                section_name not in sections.keys()
            ), f"Duplicated key {section_name} exists."
            sections[section_name] = [line_index, None]
            if prev_section is not None:
                sections[prev_section][1] = line_index
            prev_section = section_name

    assert "root" in sections.keys(), "Root joint information cannot be found."
    assert "bonedata" in sections.keys(), "Bone data cannot be found."
    assert "hierarchy" in sections.keys(), "Bone hierarchy information cannot be found."

    # Read all metadata
    version = "unknown"
    name = "noname"
    description = ""
    units = {"mass": "n/a", "length": "n/a", "angle": "n/a"}

    if "version" in sections.keys():
        ibegin, iend = sections["version"]
        lines = " ".join(data[ibegin:iend])
        tokens = lines.strip().split()
        version = tokens[1]

    if "name" in sections.keys():
        ibegin, iend = sections["name"]
        lines = " ".join(data[ibegin:iend])
        tokens = lines.strip().split()
        name = tokens[1]

    if "documentation" in sections.keys():
        ibegin, iend = sections["documentation"]
        lines = " ".join(data[ibegin:iend])
        tokens = lines.strip().split()
        description = " ".join(tokens[1:])

    if "units" in sections.keys():
        ibegin, iend = sections["units"]
        lines = data[ibegin:iend]
        for line in lines:
            tokens = line.strip().split()
            if tokens[0] == "mass":
                units["mass"] = float(tokens[1])
            elif tokens[0] == "length":
                units["length"] = float(tokens[1])
            elif tokens[0] == "angle":
                units["angle"] = tokens[1]

    if verbose:
        print("... Version:", version)
        print("... Name:", name)
        print("... Description:", description)
        print("... Units:")
        print("        Mass:", units["mass"])
        print("        Length:", units["length"])
        print("        Angle:", units["angle"])

    # Parse root
    ibegin, iend = sections["root"]
    order, axis, position, orientation = None, None, None, None
    for line in data[ibegin + 1 : iend]:
        tokens = line.strip().split()
        if tokens[0] == "order":
            order = tokens[1:]
        elif tokens[0] == "axis":
            axis = tokens[1]
        elif tokens[0] == "position":
            position = np.array([float(tokens[1]), float(tokens[2]), float(tokens[3])])
        elif tokens[0] == "orientation":
            orientation = np.array(
                [float(tokens[1]), float(tokens[2]), float(tokens[3])]
            )
    assert order is not None, "The 'order' keyword of the root joint cannot be found."
    if axis is None:
        warnings.warn(
            "The 'axis' keyword of the root joint cannot be found. It will be assumed 'XYZ'"
        )
        axis = "XYZ"
    if position is None:
        warnings.warn(
            "The 'position' keyword of the root joint cannot be found. It will be assumed [0, 0, 0]"
        )
        position = np.zeros(3)
    if orientation is None:
        warnings.warn(
            "The 'orientation' keyword of the root joint cannot be found. It will be assumed [0, 0, 0]"
        )
        orientation = np.zeros(3)

    bone_id = 0

    bones = {
        "root": Bone(
            id=bone_id,
            name="root",
            direction=np.zeros(3),
            length=0,
            axis=np.zeros(3),
            dof=[],
            limits=[],
        )
    }

    # Parse bone data
    ibegin, iend = sections["bonedata"]
    bonedata = []
    reading = False
    for line in data[ibegin + 1 : iend]:
        line = line.strip()
        if line == "begin":
            bone = []
            reading = True
        elif line == "end":
            bonedata.append(" ".join(bone))
            reading = False
        else:
            assert reading, "The contents of 'bonedata' appears to be broken."
            bone.append(line)
    assert not reading, "The contents of 'bonedata' appears to be broken."

    for bone in bonedata:
        tokens = bone.split()
        bone_sections = {}
        prev_section = None
        for i, token in enumerate(tokens):
            token = token.lower()
            curr_section = None
            if token in ["id", "name", "direction", "length", "axis", "dof", "limits"]:
                bone_sections[token] = [i + 1, None]
                if prev_section is not None:
                    bone_sections[prev_section][1] = i
                prev_section = token
        bone_sections[prev_section][1] = i + 1
        keys = bone_sections.keys()
        assert "name" in keys, "The 'name' keyword is missing in a bone."
        ibegin, iend = bone_sections["name"]
        name = "_".join(tokens[ibegin:iend])
        for keyword in [
            "id",
            "direction",
            "length",
            "axis",
        ]:  # 'dof' and 'limits' can be missing if a joint doesn't move.
            assert keyword in keys, f"The {keyword} keyword is missing in '{name}'."

        bone_id = bone_id + 1
        val = int(tokens[bone_sections["id"][0]])
        if val != bone_id:
            warnings.warn(
                f"Expected bone_id = {bone_id}, but found {val}. It will be automatically corrected."
            )

        ibegin, iend = bone_sections["direction"]
        assert iend - ibegin == 3, "The 'direction' vector must be in 3-dimensions."
        direction = np.array([float(x) for x in tokens[ibegin:iend]])

        length = float(tokens[bone_sections["length"][0]]) / units["length"]

        ibegin, iend = bone_sections["axis"]
        assert (
            iend - ibegin == 4
        ), "The 'axis' keyword must contain a 3-dimensional vector and a string specifying the order of rotations (e.g. 'XYZ')."
        axis = np.array([float(x) for x in tokens[ibegin : iend - 1]])
        if units["angle"] in ["deg", "degree", "degrees"]:
            axis = np.deg2rad(axis)
        order = tokens[iend - 1]

        dof = None
        limits = None
        if "dof" in keys:
            ibegin, iend = bone_sections["dof"]
            dof = tokens[ibegin:iend]
            ibegin, iend = bone_sections["limits"]
            limits = np.array(
                [
                    float(x.replace("(", "").replace(")", ""))
                    for x in tokens[ibegin:iend]
                ]
            ).reshape(len(dof), 2)

        bones[name] = Bone(bone_id, name, direction, length, axis, dof, limits)

    # Parse bone hierarchy
    ibegin, iend = sections["hierarchy"]
    for line in data[ibegin + 1 : iend]:
        line = line.strip().split()

        # there should be no cases where separate (disconnected) hierachies exist. otherwise, there must be two or more roots.
        if line[0] in ["begin", "end"]:
            continue

        for i, token in enumerate(line[1:]):
            bones[token].parent = bones[line[0]]
            bones[line[0]].children.append(bones[token])

    bones["root"].set_pose()

    print("[loadASF] Success.")

    return {
        "version": version,
        "name": name,
        "description": description,
        "units": {
            "mass": units["mass"],
            "length": units["length"],
            "angle": units["angle"],
        },
        "bones": bones,
    }


def loadAMC(asfdata, filepath):
    with open(filepath) as f:
        data = f.read().splitlines()

    for idx, line in enumerate(data):
        if line[0] not in [':', '#']:
            data = data[idx:]
            break

    isdegree = asfdata["units"]["angle"] in ["deg", "degree", "degrees"]

    frames = []
    pose = {}
    for line in data:
        if line.isnumeric():
            frames.append(pose)
            pose = {}
        else:
            tokens = line.strip().split()
            values = np.array([float(x) for x in tokens[1:]])
            if isdegree:
                if tokens[0] == "root":
                    values[3:] = np.deg2rad(values[3:])
                else:
                    values = np.deg2rad(values)
            pose[tokens[0]] = values
    frames.pop(0)

    for pose in frames:
        pose["root"][:3] /= asfdata["units"]["length"]

    return frames
