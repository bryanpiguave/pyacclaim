from pyacclaim import loadASF, loadAMC

import numpy as np
import matplotlib.pyplot as plt
import matplotlib.animation as animation


def main():
    asf = loadASF("test.asf")
    amc = loadAMC(asf, "test.amc")

    draw(asf, amc)


def update(num, asf, amc, lines):
    bones = asf["bones"]
    bones["root"].set_pose(amc[num])

    vertices = np.zeros((len(bones), 3))
    for bone in bones:
        vertices[bones[bone].id, :] = bones[bone].global_coordinate

    i = 0
    for bone in bones:
        if bones[bone].parent is not None:
            pid = bones[bone].parent.id
            cid = bones[bone].id
            # There is no .set_data() for 3 dim data...
            lines[i].set_data(
                [
                    [vertices[pid][0], vertices[cid][0]],
                    [vertices[pid][1], vertices[cid][1]],
                ]
            )
            lines[i].set_3d_properties([vertices[pid][2], vertices[cid][2]])
            i += 1

    return lines


def draw(asf, amc):
    fig = plt.figure()
    ax = fig.add_subplot(projection="3d")

    lines = []
    bones = asf["bones"]
    vertices = np.zeros((len(bones), 3))
    for bone in bones:
        vertices[bones[bone].id, :] = bones[bone].global_coordinate

    for bone in bones:
        if bones[bone].parent is not None:
            pid = bones[bone].parent.id
            cid = bones[bone].id
            lines.append(
                # ax.plot([vertices[pid][0], vertices[cid][0]], [vertices[pid][1], vertices[cid][1]], [vertices[pid][2], vertices[cid][2]])[0]
                ax.plot([], [], [])[0]
            )

    # Setting the axes properties
    ax.view_init(elev=123, azim=-79, roll=10)
    ax.set(xlim3d=(-50, 50), xlabel="X")
    ax.set(ylim3d=(0, 100), ylabel="Y")
    ax.set(zlim3d=(-50, 50), zlabel="Z")

    # Creating the Animation object
    ani = animation.FuncAnimation(
        fig, update, len(amc), fargs=(asf, amc, lines), interval=16.67
    )

    plt.show()


if __name__ == "__main__":
    main()
