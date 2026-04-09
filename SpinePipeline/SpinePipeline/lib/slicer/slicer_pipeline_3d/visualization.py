import slicer
import numpy as np
from transformation import get_coordinate_by_rotation_matrix

def get_mid_sagittal_x_coordinate(centroids_dict, level_name_list):
    """
    Compute the mean x-coordinate of specified centroids to determine the mid-sagittal x-coordinate in RAS coordinate system. 
    This function is used to find the best fit mid-sagittal plane given the list of vertebra body centroids.
    The functino assumes that centroids are in RAS space.

    :param centroids_dict: A dictionary mapping segment names to their centroid coordinates.
    :type centroids_dict: dict{str:list-like (tuple, list, ndarray)}
    :param level_name_list: A list of segment names.
    :type level_name_list: list[str] 
    :return: The x-coordinate of the mid-sagittal plane computed from the mean of the specified centroids.
    :rtype: float
    """
    sagittal_plane_x = np.mean([centroids_dict[key][0]
                               for key in level_name_list if key in centroids_dict])
    return sagittal_plane_x

def get_axial_i_coordinate_dict(centroids_ras_dict, level_name_list, ras_to_ijk_array):
    """
    Computes the axial plane's i-coordinate (slice number) for the given vertebral levels. The planes are selected based on the z-coordinate of the vertebral body centroids.

    This function calculates the axial plane's i-coordinate based on the centroids' z-coordinate in the RAS 
    space for each vertebral body. It then returns a dictionary 
    mapping each level to its axial plane's i-coordinate.

    :param centroids_ras_dict: Dictionary containing the centroids of vertebral levels in the RAS coordinate system.
    :type centroids_ras_dict: dict{str:tuple(int)}

    :param level_name_list: List of vertebral level names.
    :type level_name_list: list

    :param ras_to_ijk_array: Rotation matrix to transform from RAS to IJK coordinates.
    :type ras_to_ijk_array: np.array

    :return: Dictionary mapping vertebral levels to their respective axial plane's i-coordinates.
    :rtype: dict{str: int}

    :Example:

    >>> centroids_sample = {"L1": [10, 15, 20], "L2": [11, 16, 21]}
    >>> levels = ["L1", "L2"]
    >>> ras_to_ijk_sample = np.array([[1, 0, 0], [0, 1, 0], [0, 0, 1]])
    >>> result = get_axial_i_coordinate_dict(centroids_sample, levels, ras_to_ijk_sample)
    >>> print(result)
    {"L1": 20, "L2": 21}
    """

    axial_plane_i_dict = {}
    for level_name in level_name_list:
        level_centroid_ijk = get_coordinate_by_rotation_matrix(
            centroids_ras_dict[level_name], ras_to_ijk_array)
        axial_plane_i_dict[level_name] = int(level_centroid_ijk[2])
    return axial_plane_i_dict

def display_point(markup_list, coordinate, name):
    """
    Add a control point to the given markup list with a specified coordinate and label.

    :param markup_list: The MarkupsFiducialNode to which the control point will be added.
    :type markup_list: vtkMRMLMarkupsFiducialNode

    :param coordinate: A tuple or list containing the x, y, and z coordinates of the control point.
    :type coordinate: tuple or list

    :param name: The label to be assigned to the control point.
    :type name: str

    :Example:

    # Assuming this is some initialized markup list.
    >>> markup_list = slicer.mrmlScene.AddNewNodeByClass("vtkMRMLMarkupsFiducialNode")
    >>> coordinate = (1.0, 2.0, 3.0)
    >>> display_point(markup_list, coordinate, "SamplePoint")
    """
    point_index = markup_list.GetNumberOfControlPoints()
    markup_list.AddControlPoint(*coordinate)
    markup_list.SetNthControlPointLabel(point_index, name)

def display_plane(center, normal, size=None, color=None, opacity=None, name=None):
    """
    Displays a plane in the 3D slicer scene.

    :param center: List or tuple containing the coordinates of the plane's center.
    :type center: list or tuple of length 3

    :param normal: List or tuple containing the normal vector of the plane.
    :type normal: list or tuple of length 3

    :param size: Optional. A list or tuple containing the width and length of the plane in RAS coordinates. Default is None.
    :type size: list or tuple of length 2, optional

    :param color: Optional. RGB tuple specifying the plane's color. Default is None.
    :type color: tuple of length 3, optional

    :param opacity: Optional. Opacity value of the plane ranging from 0.0 (transparent) to 1.0 (opaque). Default is None.
    :type opacity: float, optional

    :param name: Optional. Name of the plane to be displayed in the slicer environment. Default is None.
    :type name: str, optional

    :return: Node representing the plane in the slicer environment.
    :rtype: vtkMRMLMarkupsPlaneNode

    :Example:

    >>> center = [0, 0, 0]
    >>> normal = [0, 0, 1]
    >>> plane = display_plane(center, normal, size=5, color=(1, 0, 0), opacity=0.5, name="Example Plane")
    """
    plane_node = slicer.mrmlScene.AddNewNodeByClass('vtkMRMLMarkupsPlaneNode')
    plane_node.SetCenter(center)
    plane_node.SetNormal(normal)

    if size != None:
        plane_node.SetSizeWorld(size)

    display_node = plane_node.GetDisplayNode()
    if display_node == None:
        display_node = slicer.mrmlScene.AddNewNodeByClass(
            "vtkMRMLMarkupsDisplayNode")
        plane_node.SetAndObserveDisplayNodeID(display_node.GetID())

    if color != None:
        display_node.SetSelectedColor(*color)

    if opacity != None:
        display_node.SetOpacity(opacity)
    if name != None:
        plane_node.SetName(name)
    return plane_node


def display_sagittal_plane(sagittal_plane_i, volume_shape, ijk_to_ras_array, color=(1, 1, 0), opacity=0.3):
    """
    Displays a sagittal plane in the 3D slicer environment that has the same size of the CT sagittal plane.
    Used to display mid-sagittal plane.

    :param sagittal_plane_i: The i-index of the sagittal plane.
    :type sagittal_plane_i: int

    :param volume_shape: The shape of the 3D volume data as (z, y, x).
    :type volume_shape: tuple of length 3

    :param ijk_to_ras_array: Array used to transform ijk voxel coordinates to RAS coordinates.
    :type ijk_to_ras_array: array-like, shape (4, 4)

    :param color: Optional. RGB tuple specifying the plane's color. Default is (1, 1, 0) for yellow.
    :type color: tuple of length 3, optional

    :param opacity: Optional. Opacity value of the plane ranging from 0.0 (transparent) to 1.0 (opaque). Default is 0.3.
    :type opacity: float, optional

    :Example:

    >>> volume_shape = (128, 256, 256)
    >>> ijk_to_ras = np.eye(4)  # For this example, identity matrix
    >>> display_sagittal_plane(127, volume_shape, ijk_to_ras)
    """

    normal = [1.0, 0.0, 0.0]

    y_size = volume_shape[1]
    z_size = volume_shape[0]
    y_pixel_size = ijk_to_ras_array[1, 1]
    slice_height = ijk_to_ras_array[2, 2]
    size = [z_size*slice_height, y_size*y_pixel_size]

    center_x = get_coordinate_by_rotation_matrix(
        sagittal_plane_i, ijk_to_ras_array, [0])
    center_y = get_coordinate_by_rotation_matrix(
        y_size/2, ijk_to_ras_array, [1])
    center_z = get_coordinate_by_rotation_matrix(
        z_size/2, ijk_to_ras_array, [2])
    center = [center_x, center_y, center_z]

    display_plane(center, normal, size, color, opacity, 'Mid-Sagittal')


def display_axial_planes(axial_plane_i_dict, display_level_name_list, volume_shape, ijk_to_ras_array, color=(1, 1, 0), opacity=0.3):
    """
    Displinput_multiple axial planes in the 3D slicer environment that have the same size of the CT axial plane.
    Used to display axial plane for all vertebra levels.

    :param axial_plane_i_dict: Dictionary mapping level names to their respective axial plane i-indices.
    :type axial_plane_i_dict: dict{str:int}

    :param display_level_name_list: List of level names for which axial planes are to be displayed. The output of :func:`get_axial_i_coordinate_dict`.
    :type display_level_name_list: list of str

    :param volume_shape: The shape of the 3D volume data as (z, y, x).
    :type volume_shape: tuple of length 3

    :param ijk_to_ras_array: Array used to transform ijk voxel coordinates to RAS coordinates.
    :type ijk_to_ras_array: array-like, shape (4, 4)

    :param color: Optional. RGB tuple specifying the plane's color. Default is (1, 1, 0) for yellow.
    :type color: tuple of length 3, optional

    :param opacity: Optional. Opacity value of the plane ranging from 0.0 (transparent) to 1.0 (opaque). Default is 0.3.
    :type opacity: float, optional

    :Example:

    >>> volume_shape = (128, 256, 256)
    >>> ijk_to_ras = np.eye(4)  # For this example, identity matrix
    >>> axial_plane_i_dict = {'L1': 63, 'L2': 95}
    >>> display_level_name_list = ['L1']
    >>> display_axial_planes(axial_plane_i_dict, display_level_name_list, volume_shape, ijk_to_ras)
    """
    normal = [0.0, 0.0, 1.0]
    x_size = volume_shape[2]
    y_size = volume_shape[1]

    x_pixel_size = ijk_to_ras_array[0, 0]
    y_pixel_size = ijk_to_ras_array[1, 1]

    size = [x_size*x_pixel_size, y_size*y_pixel_size]

    for level_name in display_level_name_list:

        axial_plane_i = axial_plane_i_dict[level_name]

        center_x = get_coordinate_by_rotation_matrix(
            x_size/2, ijk_to_ras_array, [0])
        center_y = get_coordinate_by_rotation_matrix(
            y_size/2, ijk_to_ras_array, [1])
        center_z = get_coordinate_by_rotation_matrix(
            axial_plane_i, ijk_to_ras_array, [2])
        center = [center_x, center_y, center_z]
        display_plane(center, normal, size, color,
                      opacity, 'Axial - ' + level_name)