import numpy as np


def _euler2rot(radians, order="xyz"):
    R = np.eye(3)
    for base, theta in zip(order, radians):
        c = np.cos(theta)
        s = np.sin(theta)
        if base.lower() == "x":
            T = np.array([[1, 0, 0], [0, c, -s], [0, s, c]])
        if base.lower() == "y":
            T = np.array([[c, 0, s], [0, 1, 0], [-s, 0, c]])
        if base.lower() == "z":
            T = np.array([[c, -s, 0], [s, c, 0], [0, 0, 1]])
        R = np.matmul(T, R)
    return R


class Bone:
    def __init__(self, id, name, direction, length, axis, dof=None, limits=None):
        self.id = id
        self.name = name
        self.parent = None
        self.children = []

        self.direction = np.array(direction)  # Direction of the segment
        self.length = length
        self.parent = None
        self.children = []
        self.frame = _euler2rot(axis)
        self.frame_inv = np.linalg.inv(self.frame)

        self.limits = None
        if dof is not None:
            self.limits = np.zeros((3, 2))
            for limit, dof_name in zip(limits, dof):
                if dof_name == "rx":
                    self.limits[0] = limit
                elif dof_name == "ry":
                    self.limits[1] = limit
                elif dof_name == "rz":
                    self.limits[2] = limit
                else:
                    raise ValueError("'dof' must be either 'rx', 'ry', or 'rz'.")

        self.transformation = np.eye(4)
        self.global_coordinate = np.zeros(3)

    def set_pose(self, pose=None):
        if self.parent is None:  # root
            if pose is None:
                self.transformation = np.eye(4)
            else:
                p = pose[self.name]
                self.transformation[:3, 3] = p[:3]
                self.transformation[:3, :3] = self.frame.dot(_euler2rot(p[3:])).dot(
                    self.frame_inv
                )
            self.global_coordinate = self.transformation[:3, 3]
        else:
            transformation = np.eye(4)
            if pose is not None and self.limits is not None:
                rotation = np.zeros(3)
                idx = 0
                p = pose[self.name]
                zero = np.zeros(2)
                for axis, lm in enumerate(self.limits):
                    if not np.array_equal(lm, zero):
                        rotation[axis] = p[idx]
                        idx += 1
                transformation[:3, :3] = _euler2rot(rotation)

            self.transformation[:3, :3] = (
                self.parent.transformation[:3, :3]
                .dot(self.frame)
                .dot(transformation[:3, :3])
                .dot(self.frame_inv)
            )
            self.global_coordinate = (
                self.parent.global_coordinate
                + self.length * self.transformation[:3, :3].dot(self.direction)
            )

        for child in self.children:
            child.set_pose(pose)
