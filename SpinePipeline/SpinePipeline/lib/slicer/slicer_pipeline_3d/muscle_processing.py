import numpy as np
from scipy import ndimage
from transformation import get_coordinate_by_rotation_matrix

muscle_name_list = ['PM', 'RA', 'SA', 'LD', 'TR', 'N/A',
                    'EO', 'IO', 'N/A', 'ES', 'TS', 'N/A', 'PS', 'QL']
side_name_list = ['L', 'R']
Muscle_Xsect = np.array([
    [0,   1,   2,   3,   4,   5,   6,   7,   8,   9,   10,  11,  12,  13,  14,  20],
    [1,   1,   0,   0,   1,   1,   0,   0,   0,   0,   1,   1,   0,   0,   0,   1],
    [2,   1,   0,   0,   1,   1,   0,   0,   0,   0,   1,   1,   0,   0,   0,   1],
    [3,   1,   0,   0,   1,   1,   0,   0,   0,   0,   1,   1,   0,   0,   0,   1],
    [4,   1,   0,   0,   1,   1,   0,   0,   0,   0,   1,   1,   0,   0,   0,   1],
    [5,   1,   0,   0,   1,   1,   0,   0,   0,   0,   1,   1,   0,   0,   0,   1],
    [6,   1,   0,   1,   1,   1,   0,   0,   0,   0,   1,   1,   0,   0,   0,   1],
    [7,   1,   0,   1,   1,   1,   0,   0,   0,   0,   1,   1,   0,   0,   0,   1],
    [8,   1,   0,   1,   1,   1,   0,   0,   0,   0,   1,   1,   0,   0,   0,   1],
    [9,   1,   0,   1,   1,   1,   0,   0,   0,   0,   1,   1,   0,   0,   0,   1],
    [10,  0,   1,   1,   1,   1,   0,   1,   0,   0,   1,   1,   0,   0,   0,   1],
    [11,  0,   1,   1,   1,   0,   0,   1,   0,   0,   1,   1,   0,   0,   0,   1],
    [12,  0,   1,   0,   1,   0,   0,   1,   0,   0,   1,   1,   0,   0,   0,   1],
    [13,  0,   1,   0,   1,   0,   0,   1,   0,   0,   1,   1,   0,   1,   1,   1],
    [14,  0,   1,   0,   1,   0,   0,   1,   1,   0,   1,   1,   0,   1,   1,   1],
    [15,  0,   1,   0,   1,   0,   0,   1,   1,   0,   1,   1,   0,   1,   1,   1],
    [16,  0,   1,   0,   0,   0,   0,   1,   1,   0,   1,   1,   0,   1,   1,   1],
    [17,  0,   1,   0,   0,   0,   0,   1,   1,   0,   1,   1,   0,   1,   0,   1]
])
def get_HU_coordinate(CT_slice, HU_offset=-1024):
    """
    Extracts the coordinates and Hounsfield Unit (HU) values of voxels from a CT slice that do not match the HU offset.

    This function finds and returns the x and y coordinates of all the voxels in the given CT slice 
    whose HU values is equal to air's HU value.

    :param CT_slice: A 2D array representing the CT slice.
    :type CT_slice: np.array

    :param HU_offset: This typically represents the value of air for the stored value or the 'Rescale Intercept' found in the DICOM metadata. Default is -1024.
    :type HU_offset: int

    :return: 
        - X_cur: x-coordinates of voxels that do not match the HU offset.
        - Y_cur: y-coordinates of voxels that do not match the HU offset.
        - HU_cur: HU values of voxels that do not match the HU offset.

    :rtype: tuple (np.array, np.array, np.array)

    :Example:

    >>> sample_CT_slice = np.array([[1, -1024], [3, 4]])
    >>> X_cur, Y_cur, HU_cur = get_HU_coordinate(sample_CT_slice)
    >>> print(X_cur, Y_cur, HU_cur)
    [0, 1] [0, 0] [1, 3]
    """
    Y_cur, X_cur = np.where(CT_slice != HU_offset)
    HU_cur = CT_slice[CT_slice != HU_offset]
    return X_cur, Y_cur, HU_cur
def insertval(leftval, rightval):
    """
    Computes the average of left and right values, with special handling for missing data.

    Given two input values, this function:
    - Returns their average if both sides are valid.
    - Returns the non-missing value if only one side is missing.
    - Returns 0 if both are missing.

    :param leftval: The left-side value.
    :type leftval: float

    :param rightval: The right-side value.
    :type rightval: float

    :return: The computed result based on the provided logic.
    :rtype: float

    :Example:
    >>> insertval(4, 6)
    5.0
    >>> insertval(9999, 6)
    6
    >>> insertval(9999, 9999)
    0
    """
    if leftval != 9999 and rightval != 9999:
        result = (leftval + rightval) / 2
    elif leftval != 9999 and rightval == 9999:
        result = leftval
    elif leftval == 9999 and rightval != 9999:
        result = rightval
    else:
        result = 0
    return result


def insertval_abs(leftval, rightval):
    """
    Computes the average of the absolute values of two inputs, with special handling for a sentinel value of 9999.

    Given two input values, this function:
    - Returns the average of their absolute values if both sides are valid.
    - Returns the non-missing value if only one side is missing.
    - Returns 0 if both are missing.

    :param leftval: The left-side value.
    :type leftval: float or int

    :param rightval: The right-side value.
    :type rightval: float or int

    :return: The computed result based on the provided logic.
    :rtype: float

    :Example:

    >>> insertval_abs(-4, 6)
    5.0

    >>> insertval_abs(9999, -6)
    6.0

    >>> insertval_abs(9999, 9999)
    0
    """
    if leftval != 9999 and rightval != 9999:
        result = (abs(leftval) + abs(rightval)) / 2
    elif leftval != 9999 and rightval == 9999:
        result = abs(leftval)
    elif leftval == 9999 and rightval != 9999:
        result = abs(rightval)
    else:
        result = 0
    return result

def musclecalcs(x_array, y_array, HU_array, HU_upper_bound, HU_lower_bound, ijk_to_ras_array, image_size=(512, 512)):
    """
    Calculate various muscle parameters based on pixel data and HU (Hounsfield Unit) values for one muscle on one level.

    This function computes the area, centroid, mean HU, standard deviation of HU, interquartile range (IQR),
    and mean HU of the peeled region for muscle pixels that fall within a specified HU range.

    :param x_array: Array of x-coordinates of muscle pixels.
    :type x_array: np.array[int]

    :param y_array: Array of y-coordinates of muscle pixels.
    :type y_array: np.array[int]

    :param HU_array: Array of HU values corresponding to each pixel.
    :type HU_array: np.array[float]

    :param HU_upper_bound: Upper bound for HU to consider in calculations.
    :type HU_upper_bound: float

    :param HU_lower_bound: Lower bound for HU to consider in calculations.
    :type HU_lower_bound: float

    :param ijk_to_ras_array: Array used to transform ijk voxel coordinates to RAS coordinates.
    :type ijk_to_ras_array: array-like, shape (4, 4)

    :param image_size: Size of the image, default is (512, 512).
    :type image_size: tuple[int, int]

    :return: Various computed muscle parameters including area, centroids, mean HU, std HU, IQR, and peel HU.
    :rtype: tuple[float, float, float, float, float, float, float]

    :Note:
    1. Pixels that do not fall within the specified HU range are filtered out.
    2. Ensure the provided arrays (`x_array`, `y_array`, `HU_array`) have the same length.
    """

    assert len(x_array) == len(y_array) and len(y_array) == len(
        HU_array), 'x_array, y_array, HU_array should have the same length'

    muscle_image_bool = np.zeros(image_size).astype(bool)
    muscle_image_HU = np.zeros(image_size)
    for i in range(len(x_array)):
        muscle_image_bool[x_array[i], y_array[i]] = True
        muscle_image_HU[x_array[i], y_array[i]] = HU_array[i]

    # Filter out the data where the HU values are out of range
    mask = (HU_array > HU_upper_bound) | (HU_array < HU_lower_bound)
    x_array = x_array[~mask]
    y_array = y_array[~mask]
    HU_array = HU_array[~mask]

    # Count the number of pixels left
    pixel_count = len(HU_array)
    x_pixel_size = ijk_to_ras_array[0, 0]
    y_pixel_size = ijk_to_ras_array[1, 1]
    x_array_ras = np.array([get_coordinate_by_rotation_matrix(
        x_ijk, ijk_to_ras_array, [0]) for x_ijk in x_array])
    y_array_ras = np.array([get_coordinate_by_rotation_matrix(
        y_ijk, ijk_to_ras_array, [1]) for y_ijk in y_array])

    # Calculate the muscle parameters
    area = abs(pixel_count * x_pixel_size * y_pixel_size)
    centroid_x = np.mean(x_array_ras)
    centroid_y = np.mean(y_array_ras)
    mean_HU = np.mean(HU_array)
    # np.std() in Python uses a normalization factor of N by default. ddof = 1 changes it to N-1
    std_HU = np.std(HU_array, ddof=1)
    median_HU = np.median(HU_array)
    Q1 = np.median(HU_array[HU_array < median_HU])
    Q3 = np.median(HU_array[HU_array > median_HU])
    IQR = Q3 - Q1

    # Dilate the non-ROI region (i.e., shrink the ROI)
    muscle_image_bool_eroded = ndimage.binary_erosion(
        muscle_image_bool, structure=np.ones((4, 4)), origin=-1)
    # In Python's scipy.ndimage.binary_dilation, the structuring element is centered at the
    #  origin by default. However, in MATLAB, the center of the structuring element is the
    #  rounded up value of half its size, or (size(strel)+1)/2.
    #  Add origin = -1 parameter to fix this.

    if len(muscle_image_HU[muscle_image_bool_eroded]) == 0:
        peel_HU = 9999
    else:
        peel_HU = np.mean(muscle_image_HU[muscle_image_bool])

    return area, centroid_x, centroid_y, mean_HU, std_HU, IQR, peel_HU


# %%
def level_rotation(DB):
    """
    Compute and apply the rotation to align the centroids of muscles with the horizontal axis.

    Given a database with muscle data, this function first calculates the rotation angle required to
    align the centroids of the muscles with the horizontal axis. Then, it applies the computed rotation
    to the centroids in the database.

    :param DB: A database containing all objects for a level. Format see :func:`calculate_muscle_measurement_database`
    :type DB: np.array

    :return: Modified database with rotated centroids.
    :rtype: np.array

    :Note:
    1. It's important for the input database to have the appropriate structure and data for this function to work correctly.
    2. If no valid rotation angles are computed, the function defaults to 0 degrees rotation.
    3. The rotation is counter-clockwise for positive angles.
    """
    muscle_list = np.unique(DB[:, 1])
    rotation_angle = []

    for i in range(len(muscle_list)):
        if muscle_list[i] == 0:  # check to see if it's the vertebral body
            continue
        else:
            musclemat = DB[muscle_list[i] == DB[:, 1]]

            # If only one side is available, then it cannot be used to calculate rotation
            if len(musclemat) < 2 or np.any(musclemat[:, 6] == 9999):
                continue
            else:  # Otherwise, we'll calculate the angle between the centroids off the horizontal
                rotation_angle.append(-np.arctan(
                    (musclemat[1, 6] - musclemat[0, 6]) / (musclemat[1, 5] - musclemat[0, 5])))

    if len(rotation_angle) == 0:
        theta = 0
    else:
        theta = -np.mean(rotation_angle)

    for i in range(len(DB)):
        if DB[i, 5] != 9999:
            new_cent = np.array(
                [[np.cos(theta), -np.sin(theta)], [np.sin(theta), np.cos(theta)]]) @ DB[i, 5:7]
            if DB[i, 1] == 0:
                vertebral_centroid = new_cent

            DB[i, 5:7] = new_cent - vertebral_centroid

    return DB


# %%
def get_segment_slice(volume_3D_array, segment_3D_mask, plane_coordinate, axis, HU_offset=-1024):
    """
    Extracts a slice from a 3D volume based on the given plane coordinate and axis.

    :param volume_3D_array: A 3D array representing the CT volume.
    :type volume_3D_array: np.array

    :param segment_3D_mask: A 3D boolean mask that indicates the region of interest.
    :type segment_3D_mask: np.array

    :param plane_coordinate: Index along the specified axis at which the slice is to be taken.
    :type plane_coordinate: int

    :param axis: The axis along which the slice is to be taken (0 for x-axis, 1 for y-axis, 2 for z-axis).
    :type axis: int

    :param HU_offset: Offset value to be applied to the extracted slice. 
    This typically represents the value of air for the stored value or the 'Rescale Intercept' found in the DICOM metadata. Default is -1024.
    :type HU_offset: int

    :return: A 2D slice from the 3D volume with the applied mask and HU offset.
    :rtype: np.array

    :raises AssertionError: If the specified axis is not one of 0, 1, or 2.

    :Example:

    >>> volume_sample = np.random.rand(10, 10, 10)
    >>> mask_sample = np.ones((10, 10, 10))
    >>> extracted_slice = get_segment_slice(volume_sample, mask_sample, 0, 0)
    >>> print(extracted_slice)

    :Note:
    1. The function assumes that the `segment_3D_mask` uses the same coordinate system and has the same dimensions as `volume_3D_array`.
    2. The `HU_offset` is used to preserve the original values within the mask and set the values outside the mask to the `HU_offset` value.
    3. Ensure that the `volume_3D_array` and `segment_3D_mask` have the same dimensions and coordinate system.
    """
    assert axis in (
        0, 1, 2), 'axis can only be 0 (x-axis),1 (y-axis),2 (z-axis)'
    if axis == 0:
        volume_slice = volume_3D_array[:, :, plane_coordinate]
        mask_slice = segment_3D_mask[:, :, plane_coordinate]
    elif axis == 1:
        volume_slice = volume_3D_array[:, plane_coordinate, :]
        mask_slice = segment_3D_mask[:, plane_coordinate, :]
    elif axis == 2:
        volume_slice = volume_3D_array[plane_coordinate, :, :]
        mask_slice = segment_3D_mask[plane_coordinate, :, :]

    CT_slice = (volume_slice-HU_offset) * mask_slice + HU_offset
    return CT_slice

def calculate_muscle_measurement_database(
        patient_id,
        volume_3D_array, vertebra_segment_arrays_dict, muscle_segment_arrays_dict,
        level_name_list,
        axial_plane_i_dict, ijk_to_ras_array,level_name_mapping, 
        HU_vertebra_upper_bound=2000, HU_vertebra_lower_bound=-500,
        HU_muscle_upper_bound=150, HU_muscle_lower_bound=-50):
    """
    Generate a database containing all measurements on all levels related to vertebra and muscle from a 3D volume.

    This function processes each vertebra and muscle segmentation axial slice on each vertebra level,
    extracting area, centroid coordinates, mean HU (Hounsfield Unit), standard deviation of HU, 
    interquartile range of HU, and peel HU. The function then rotates the centroid for each level using the
    :func:`level_rotation` function and appends it to the database.

    :param patient_id: Patient's ID. Only appended to database. No other use.
    :type patient_id: str

    :param volume_3D_array: 3D array containing the volume data.
    :type volume_3D_array: numpy.ndarray, shape (z, y, x)

    :param vertebra_segment_arrays_dict: Dictionary mapping level names to their respective vertebra body segment arrays.
    :type vertebra_segment_arrays_dict: dict{str: numpy.ndarray}

    :param muscle_segment_arrays_dict: Dictionary mapping muscle names to their respective muscle segment arrays.
    :type muscle_segment_arrays_dict: dict{str: numpy.ndarray}

    :param level_name_list: List of level names to be processed.
    :type level_name_list: list of str

    :param axial_plane_i_dict: Dictionary mapping level names to their respective axial plane i-indices.
    :type axial_plane_i_dict: dict{str: int}

    :param ijk_to_ras_array: Array used to transform ijk voxel coordinates to RAS coordinates.
    :type ijk_to_ras_array: array-like, shape (4, 4)

    :param HU_vertebra_upper_bound: Optional. Upper HU bound for vertebra processing. Default is 2000.
    :type HU_vertebra_upper_bound: int, optional

    :param HU_vertebra_lower_bound: Optional. Lower HU bound for vertebra processing. Default is -500.
    :type HU_vertebra_lower_bound: int, optional

    :param HU_muscle_upper_bound: Optional. Upper HU bound for muscle processing. Default is 150.
    :type HU_muscle_upper_bound: int, optional

    :param HU_muscle_lower_bound: Optional. Lower HU bound for muscle processing. Default is -50.
    :type HU_muscle_lower_bound: int, optional

    :return: A database containing measurements related to vertebra and muscle for each level.

        Format:
        - (patient_id, object_no, side, level, area, cent_x, cent_y, mean_HU, std_HU, IQR, peel_HU)
        - patient_id: Patient's ID.
        - object_no: Object ID (see Object Mapping section).
        - side: Either object side or vertebra level.
            For muscles: 1 (left) or 2 (right).
            For vertebrae: Level, e.g., T12 -> 12, L5 -> 5.
        - level: Level number for vertebra, ranging from 1 to 17 for T1 - L5.
        - area: Cross-sectional area in the axial slice.
        - cent_x, cent_y: Centroid coordinates on the axial plane.
        - mean_HU: mean of HU
        - std_HU: standard deviation of HU
        - IQR: interquartile range of HU
        - peel_HU: mean HU of the peeled region

    :rtype: numpy.ndarray

    :Note:
        1. Object mapping:    
            ::         

                {'Vertebra': 0,
                'PM': 1,
                'RA': 2,
                'SA': 3,
                'LD': 4,
                'TR': 5,
                'EO': 7,
                'IO': 8,
                'ES': 10,
                'TS': 11,
                'PS': 13,
                'QL': 14}

        2. If an object is missing from the input, a placeholder is integrated into the database. The Matlab version includes this mechanism, but due to the 'continue' clause, the placeholder insertion is actually skipped.
        3. The function processes each vertebra level individually, rotating them separately.
    """
    database = []
    reversed_level_name_list = level_name_list[::-1]
    print(level_name_list)
    for level_i in range(len(reversed_level_name_list)):

        level_data = []
        level_name = reversed_level_name_list[level_i]
        level = level_name_mapping[level_name]
        vertebra_level = int(reversed_level_name_list[level_i][1:])

        # process vertebra body
        CT_slice = get_segment_slice(
            volume_3D_array, vertebra_segment_arrays_dict[level_name], axial_plane_i_dict[level_name], 2)

        X_cur, Y_cur, HU_cur = get_HU_coordinate(CT_slice)

        # If the muscle is not contoured at that level AT ALL then all variable are set to missing
        # and the next iteration of the script is executed
        '''The append is not actually exectuted in the Matlab code'''
        if len(X_cur) == 0:
            level_data.append((patient_id, 0, vertebra_level, level, 9999,
                              9999, 9999, 9999, 9999, 9999, 9999))  # 0 represents vertebra
            continue

        area, cent_x, cent_y, mean_HU, std_HU, IQR, peel_HU = musclecalcs(
            X_cur, Y_cur, HU_cur, HU_vertebra_upper_bound, HU_vertebra_lower_bound, ijk_to_ras_array)

        level_data.append((patient_id, 0, vertebra_level, level,
                          area, cent_x, cent_y, mean_HU, std_HU, IQR, peel_HU))
        # process muscle
        for muscle_j in range(len(muscle_name_list)):
            muscle_no = muscle_j+1
            if Muscle_Xsect[level, muscle_no] == 1:
                muscle = muscle_name_list[muscle_j]

                for side_k in range(len(side_name_list)):
                    side = side_name_list[side_k]
                    muscle_name = side + '_' + muscle
                    CT_slice = get_segment_slice(
                        volume_3D_array, muscle_segment_arrays_dict[muscle_name], axial_plane_i_dict[level_name], 2)

                    X_cur, Y_cur, HU_cur = get_HU_coordinate(CT_slice)
                    # print(f'Level= : {level}, Z_level: {axial_plane_i_dict[level_i]}, Muscle: {muscle_name},Side: {side}')

                    # If the muscle is not contoured at that level AT ALL then all variable are set to missing
                    # and the next iteration of the script is executed
                    '''The append is not actually exectuted in the Matlab code'''
                    if len(X_cur) == 0:
                        level_data.append((patient_id, muscle_no, side_k+1, level, 9999,
                                          9999, 9999, 9999, 9999, 9999, 9999))  # 0 represents vertebra
                        continue

                    # This will quickly check to see if the muscle is missing -- signified by a box outside of
                    # the FOV in the scan field. If so, move to the next muscle
                    '''The append is not actually exectuted in the Matlab code'''
                    if np.mean(HU_cur) < -500:
                        level_data.append((patient_id, muscle_no, side_k+1, level, 9999,
                                          9999, 9999, 9999, 9999, 9999, 9999))  # 0 represents vertebra
                        continue

                    area, cent_x, cent_y, mean_HU, std_HU, IQR, peel_HU = musclecalcs(
                        X_cur, Y_cur, HU_cur, HU_muscle_upper_bound, HU_muscle_lower_bound, ijk_to_ras_array)

                    level_data.append((patient_id, muscle_no, side_k+1, level,
                                      area, cent_x, cent_y, mean_HU, std_HU, IQR, peel_HU))

        level_data = np.array(level_data, dtype=np.float64)

        rotated_data = level_rotation(level_data)
        database.append(rotated_data)


    database = np.vstack(database)
    return database

def get_muscle_info_from_database(database, muscle_index_list, level_name_list,level_name_mapping):
    """
    Extracts and computes muscle information from the database. Generate necessary arrays for the info file.

    This function processes the given database to retrieve and calculate the muscle's Cross-sectional Area (CSA)
    and moment arms (MAX,MAZ).

    :param database: The database containing muscle data. See :func:`calculate_muscle_measurement_database`.
    :type database: numpy.ndarray

    :param muscle_index_list: List of muscle indices to be processed.
    :type muscle_index_list: list of int

    :param level_name_list: List of level names to be considered.
    :type level_name_list: list of str

    :return: 
        - muscledataCSA: Array containing computed CSA values for each muscle and level.
        - muscledataMAX: Array containing computed MAX values for each muscle and level.
        - muscledataMAZ: Array containing computed MAZ values for each muscle and level.
    :rtype: tuple of numpy.ndarray
    """
    muscledataCSA = np.zeros((len(muscle_index_list), len(level_name_list)))
    muscledataMAX = np.zeros((len(muscle_index_list), len(level_name_list)))
    muscledataMAZ = np.zeros((len(muscle_index_list), len(level_name_list)))

    for muscle_i in range(len(muscle_index_list)):
        for level_i in range(len(level_name_list)):
            muscle_no = muscle_index_list[muscle_i]
            level_no = level_name_mapping[level_name_list[level_i]]
            mask = (database[:, 1] == muscle_no) & (database[:, 3] == level_no)
            data = database[mask]
            #print(data)
            if len(data) > 0:
                muscledataCSA[muscle_i, level_no-1] = insertval(
                    leftval=data[data[:, 2] == 1][0, 4], rightval=data[data[:, 2] == 2][0, 4])
                muscledataMAX[muscle_i, level_no-1] = insertval(
                    leftval=data[data[:, 2] == 1][0, 6], rightval=data[data[:, 2] == 2][0, 6])
                muscledataMAZ[muscle_i, level_no-1] = insertval_abs(
                    leftval=data[data[:, 2] == 1][0, 5], rightval=data[data[:, 2] == 2][0, 5])

    return muscledataCSA, muscledataMAX, muscledataMAZ

# %%
def get_muscle_info_from_database_3D(database,muscle_index_list,level_name_list):
    """
    Extracts and computes muscle information from the database. Generate necessary arrays for the info file.

    This function processes the given database to retrieve and calculate the muscle's Cross-sectional Area (CSA)
    and moment arms (MAX,MAZ). The '3D' version keeps left and right side information separate

    :param database: The database containing muscle data. See :func:`calculate_muscle_measurement_database`.
    :type database: numpy.ndarray

    :param muscle_index_list: List of muscle indices to be processed.
    :type muscle_index_list: list of int

    :param level_name_list: List of level names to be considered.
    :type level_name_list: list of str

    :return: 
        - muscledataCSA_L: Array containing computed CSA values for each muscle and level on the left.
        - muscledataCSA_R: Array containing computed CSA values for each muscle and level on the right.
        - muscledataMAX_L: Array containing computed MAX values for each muscle and level on the left.
        - muscledataMAX_R: Array containing computed MAX values for each muscle and level on the right.
        - muscledataMAZ_L: Array containing computed MAZ values for each muscle and level on the left.
        - muscledataMAZ_R: Array containing computed MAZ values for each muscle and level on the right.
    :rtype: tuple of numpy.ndarray
    """
    muscledataCSA_L = np.zeros((len(muscle_index_list),len(level_name_list)))
    muscledataMAX_L = np.zeros((len(muscle_index_list),len(level_name_list)))
    muscledataMAZ_L = np.zeros((len(muscle_index_list),len(level_name_list)))
    muscledataCSA_R = np.zeros((len(muscle_index_list),len(level_name_list)))
    muscledataMAX_R = np.zeros((len(muscle_index_list),len(level_name_list)))
    muscledataMAZ_R = np.zeros((len(muscle_index_list),len(level_name_list)))
    
    for muscle_i in range(len(muscle_index_list)):
        for level_i in range(len(level_name_list)):
            muscle_no = muscle_index_list[muscle_i]
            level_no = level_i+1
            mask = (database[:,1] == muscle_no) & (database[:,3] == level_no)
            data = database[mask]
    
            if len(data)>0:
                muscledataCSA_L[muscle_i,level_i] = data[data[:,2]==1][0,4]
                muscledataCSA_R[muscle_i,level_i] = data[data[:,2]==2][0,4]
                muscledataMAX_L[muscle_i,level_i] = data[data[:,2]==1][0,6]
                muscledataMAX_R[muscle_i,level_i] = data[data[:,2]==2][0,6]
                muscledataMAZ_L[muscle_i,level_i] = data[data[:,2]==1][0,5]
                muscledataMAZ_R[muscle_i,level_i] = data[data[:,2]==2][0,5]
            
    return muscledataCSA_L, muscledataCSA_R,muscledataMAX_L, muscledataMAX_R ,muscledataMAZ_L, muscledataMAZ_R

