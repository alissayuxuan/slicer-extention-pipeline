import vtk
import numpy as np
def get_ijk_to_ras_array(volume_node):
    """
    Return the IJK to RAS coordinate system rotation matrix.

    This function extracts the transformation matrix that converts coordinates from the IJK space (voxel indices) to RAS space (real-world anatomical coordinates in millimeters).


    :param volume_node: volume node for the CT image
    :type volume_node: vtkMRMLScalarVolumeNode

    :return: A 4*4 IJK to RAS rotation matrix.
    :rtype: numpy.ndarray
    """

    ijk_to_ras = vtk.vtkMatrix4x4()
    volume_node.GetIJKToRASMatrix(ijk_to_ras)
    ijk_to_ras_array = np.array(
        [[ijk_to_ras.GetElement(r, c) for c in range(4)] for r in range(4)])
    return ijk_to_ras_array


def get_ras_to_ijk_array(volume_node):
    """
    Return the RAS to IJK coordinate system rotation matrix.

    This function extracts the transformation matrix that converts coordinates from the RAS space (real-world anatomical coordinates in millimeters) to IJK space (voxel indices).

    :param volume_node: volume node for the CT image
    :type volume_node: vtkMRMLScalarVolumeNode

    :return: A 4*4 RAS to IJK rotation matrix.
    :rtype: numpy.ndarray
    """
    ras_to_ijk = vtk.vtkMatrix4x4()
    volume_node.GetRASToIJKMatrix(ras_to_ijk)
    ras_to_ijk_array = np.array(
        [[ras_to_ijk.GetElement(r, c) for c in range(4)] for r in range(4)])
    return ras_to_ijk_array


def get_pixel_size(ijk_to_ras_array):
    """
    Extracts the pixel size and slice height from the given IJK-to-RAS transformation array.

    :param ijk_to_ras_array: The IJK-to-RAS transformation array, typically a 4x4 matrix.
    :type ijk_to_ras_array: numpy.ndarray

    :return:
        - x_pixel_size: The size (or spacing) of a pixel in the X dimension.
        - y_pixel_size: The size (or spacing) of a pixel in the Y dimension.
        - slice_height: The height (or thickness) of a slice in the Z dimension.
    :rtype: tuple of float
    """
    x_pixel_size = abs(ijk_to_ras_array[0, 0])
    y_pixel_size = abs(ijk_to_ras_array[1, 1])
    slice_height = abs(ijk_to_ras_array[2, 2])
    return x_pixel_size, y_pixel_size, slice_height

# %%


def get_coordinate_by_rotation_matrix(point, rotation_matrix, axes=None):
    """
    Returns the rotated coordinates of a point after applying the given rotation matrix.

    The function can deal with 1D, 2D, or 3D coordinates. If the point is a scalar, it's treated as a 1D coordinate.

    :param point: A single point coordinate. Can be either a scalar (for 1D) or a vector (for 1D, 2D, 3D).
    :type point: scalar or list-like (tuple, list, ndarray)
    :param rotation_matrix: A 4x4 rotation matrix to apply to the point.
    :type rotation_matrix: numpy.ndarray
    :param axes: The axes indices that correspond to the point dimensions. For instance, if you're rotating a 2D
                 point in the XZ plane, axes would be [0, 2]. If not specified, defaults to [0, 1, 2] (i.e., XYZ).
    :type axes: list or tuple, optional

    :return: The rotated coordinate. Returns a scalar if the input point is a scalar, otherwise returns a vector.
    :rtype: scalar or numpy.ndarray

    :raises AssertionError: If the dimensions of the point and axes mismatch or if an invalid point type is provided.

    :Example:

    .. code-block:: python

        rotation_matrix = np.array(
            [[0, -1, 0, 0], [1, 0, 0, 0], [0, 0, 1, 0], [0, 0, 0, 1]])
        point = [1, 2]
        result = get_coordinate_by_rotation_matrix(
            point, rotation_matrix, axes=[0,1])
        print(result)  # output: array([-2.,  1.])
    """
    if axes is None:
        axes = range(3)

    point_4D = np.ones(4)
    if np.isscalar(point):
        assert len(
            axes) == 1, 'Point has only 1 dimension. len(axes) should be 1.'
    else:
        assert len(axes) == len(point), f'Point and dimension shape mismatch. Point has {len(point)} dimension. Axes have {len(axes)} dimension '
        point_arr = np.array(point)

    point_4D[axes] = point
    new_point = rotation_matrix @ point_4D

    if np.isscalar(point):
        return new_point[axes][0]
    return new_point[axes]
