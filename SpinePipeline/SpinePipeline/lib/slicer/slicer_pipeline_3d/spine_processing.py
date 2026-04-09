import numpy as np
#from TPTBox import NII, Location, calc_poi_from_subreg_vert
#from TPTBox.core.poi_fun.vertebra_direction import (
#    calc_orientation_of_vertebra_PIR,
#    get_vert_direction_PIR,
#)
#from TPTBox.core.vert_constants import v_idx2name

def get_distance_3d(point1, point2):
    assert len(point1) == len(point2) == 3, f'Points must be 3-dimensional. Point1: {point1}, Point2: {point2}'
    
    # Convert points to numpy arrays
    point1_np_array = np.array(point1)
    point2_np_array = np.array(point2)

    # Calculate the vector between the points
    vector = point2_np_array - point1_np_array
    # AP (Anterior-Posterior) Distance along the X-axis
    distance_ap = (vector[1])
    
    # SI (Superior-Inferior) Distance along the Z-axis
    distance_si = (vector[2])
    
    # ML (Medio-Lateral) Distance along the Y-axis
    distance_ml = (vector[0])
    
    return distance_ap, distance_si, distance_ml


def get_angle_3d(ivj_lower, ivj_higher, vertebrae_centroid):
    """
    Calculate the 3D angles of the vertebrae centroid relative to a vertical vector defined by two points (ivj_lower and ivj_higher).

    :param ivj_lower: Coordinates of the lower IVJ point [x, y, z].
    :type ivj_lower: list[float] or tuple[float]

    :param ivj_higher: Coordinates of the higher IVJ point [x, y, z].
    :type ivj_higher: list[float] or tuple[float]

    :param vertebrae_centroid: Coordinates of the vertebrae centroid [x, y, z].
    :type vertebrae_centroid: list[float] or tuple[float]

    :return: The angles (in degrees) along the ML, AP, and SI axes relative to the vertical vector.
    :rtype: tuple of floats
    """
    # Convert points to NumPy arrays
    lower = np.array(ivj_lower)
    higher = np.array(ivj_higher)
    centroid = np.array(vertebrae_centroid)

    # Define the vertical vector as the direction from lower to higher
    vertical_vector = higher - lower

    # Normalize the vertical vector to unit length
    vertical_unit = vertical_vector / np.linalg.norm(vertical_vector)

    # Project the centroid onto the vertical vector
    projection_length = np.dot(centroid - lower, vertical_unit)
    projection_vector = projection_length * vertical_unit

    # Calculate the directional vector (difference between projection and the centroid)
    direction_vector = centroid - (lower + projection_vector)

    # Compute angles using direction vector components
    diff_ml = direction_vector[0]  # x-component (Medial-Lateral)
    diff_ap = direction_vector[1]  # y-component (Anterior-Posterior)
    diff_si = direction_vector[2]  # z-component (Superior-Inferior)

    # Angles along the anatomical axes (in degrees)
    angle_ml = np.degrees(-np.arctan2(diff_ml, diff_si))  # ML vs. SI
    angle_ap = np.degrees(-np.arctan2(diff_ap, diff_si))  # AP vs. SI
    angle_si = np.degrees(-np.arctan2(diff_ap, diff_ml))  # AP vs. ML

    return angle_ap, angle_si, angle_ml

def calculate_spine_curvature_3d(IVJ_centroids,vertebrae_centroids, level_names, L5_key='L5'):
    """
    Calculate the spine curvature based on intervertebral joint (IVJ) centroids.

    This function computes the distance and angle between successive IVJ centroids 
    to describe the spine's curvature. If a centroid is missing (represented as 9999),
    a placeholder value of 9999 is used for both distance and angle.

    :param IVJ_centroids: List of IVJ centroids (in 3D) used to compute the spine curvature.
    :type IVJ_centroids: list[tuple[float, float, float]]

    :param L5_key: Key name of L5. Default 'L5'.
    :type L5_key: str

    :param four_points_array_dict: Dictionary mapping level names to their corresponding four morphometry points in the order of [top_left,top_right,bottom_right,bottom_left]
    :type four_points_array_dict: dict{str: numpy.ndarray}

    :return: Two lists representing the joint distances and joint angles based on the IVJ centroids.
    The first two items in joint_dist and joint_angel are always 9999. The last item in joint_dist is always 9999.
    :rtype: tuple[list[float], list[float]]

    :Example:

    >>> centroids = [(1, 2, 3), (2, 3, 4), (9999, 9999, 9999), (4, 5, 6)]
    >>> joint_distances, joint_angles = calculate_spine_curvature(centroids)
    >>> print(joint_distances, joint_angles)

    :Note: 
    1. The function considers missing centroids as having a value of (9999, 9999, 9999) and 
       assigns placeholder values accordingly.
    2. The angles for the L5 vertebra are calculated differently from the others, using specific 
       points on the L5 vertebra. Ensure that `four_points_array_dict` is defined and populated 
       with the required data in the calling context.
    3. Notice that the data in joint_dist and joint_angle is in the order of [9999, 'C7_T1 to T1_T2'(should also be 9999), 'T1_T2 to T2_T3', ..., 'L2_L3 to L3_L4', 9999 (for distance) or 'mean of L5 sup and inf angle' (for angle)]
    
    The T2 IVJ lies above the T2 vertebrae
    """

    joint_dist = [(9999,9999,9999)]
    joint_angle = [(9999,9999,9999)]
    for i,level in enumerate(level_names[:-1]):
        if (IVJ_centroids[level] == (9999,9999,9999)) or (IVJ_centroids[level_names[i+1]] == (9999,9999,9999)):
            joint_dist.append((9999,9999,9999))
            joint_angle.append((9999,9999,9999))
        else:
            joint_dist.append((get_distance_3d(
                IVJ_centroids[level_names[i+1]], IVJ_centroids[level])))
            joint_angle.append((get_angle_3d(IVJ_centroids[level_names[i+1]], IVJ_centroids[level],vertebrae_centroids[level])))
    
    #have to calculate it for the 3d case for l5 
    joint_dist.append((9999,9999,9999))
    joint_angle.append((9999,9999,9999))
    
    joint_dist = np.array(joint_dist)
    joint_angle = np.array(joint_angle)

    return joint_dist, joint_angle

def calculate_centroid_distance(IVJ_centroids,level_names, L5_key='L5'):
    """
    Calculate the spine curvature based on intervertebral joint (IVJ) centroids.

    This function computes the distance and angle between successive IVJ centroids 
    to describe the spine's curvature. If a centroid is missing (represented as 9999),
    a placeholder value of 9999 is used for both distance and angle.

    :param IVJ_centroids: List of IVJ centroids (in 3D) used to compute the spine curvature.
    :type IVJ_centroids: list[tuple[float, float, float]]

    :param L5_key: Key name of L5. Default 'L5'.
    :type L5_key: str

    :param four_points_array_dict: Dictionary mapping level names to their corresponding four morphometry points in the order of [top_left,top_right,bottom_right,bottom_left]
    :type four_points_array_dict: dict{str: numpy.ndarray}

    :return: Two lists representing the joint distances and joint angles based on the IVJ centroids.
    The first two items in joint_dist and joint_angel are always 9999. The last item in joint_dist is always 9999.
    :rtype: tuple[list[float], list[float]]

    :Example:

    >>> centroids = [(1, 2, 3), (2, 3, 4), (9999, 9999, 9999), (4, 5, 6)]
    >>> joint_distances, joint_angles = calculate_spine_curvature(centroids)
    >>> print(joint_distances, joint_angles)

    :Note: 
    1. The function considers missing centroids as having a value of (9999, 9999, 9999) and 
       assigns placeholder values accordingly.
    2. The angles for the L5 vertebra are calculated differently from the others, using specific 
       points on the L5 vertebra. Ensure that `four_points_array_dict` is defined and populated 
       with the required data in the calling context.
    3. Notice that the data in joint_dist and joint_angle is in the order of [9999, 'C7_T1 to T1_T2'(should also be 9999), 'T1_T2 to T2_T3', ..., 'L2_L3 to L3_L4', 9999 (for distance) or 'mean of L5 sup and inf angle' (for angle)]
    
    The T2 IVJ lies above the T2 vertebrae
    """

    joint_dist = [(9999,9999,9999)]
    for i,level in enumerate(level_names[:-1]):
        if (IVJ_centroids[level] == (9999,9999,9999)) or (IVJ_centroids[level_names[i+1]] == (9999,9999,9999)):
            joint_dist.append((9999,9999,9999))
        else:
            joint_dist.append((get_distance_3d(
                IVJ_centroids[level_names[i+1]], IVJ_centroids[level])))
            print(level_names[i+1], level, IVJ_centroids[level_names[i+1]], IVJ_centroids[level], )
    #have to calculate it for the 3d case for l5 
    #joint_dist.append((9999,9999,9999))
    
    joint_dist = np.array(joint_dist)

    return joint_dist

def calculate_vertebral_axes(IVJ_centroids,vertebrae_centroids, spine_segment_centroids, level_names, L5_key='L5'):
    """
    Calculate the axes of each vertebra based on intervertebral joint (IVJ) centroids, vertebral body centroids, and full vertebrae centroids
    
    This function computes the axes of each vertebral body in the world (CT) frame.  
    If an input centroid is missing (represented as 9999),
    a placeholder value of 9999 is used for the axes. 
    
    :param IVJ_centroids: List of IVJ centroids (in 3D) used to compute the spine curvature.
    :type IVJ_centroids: list[tuple[float, float, float]]
    
    :param vertebrae_centroids: List of vertebral BODY centroids (in 3D) used to compute the spine curvature.
    :type vertebrae_centroids: list[tuple[float, float, float]]
    
    :param spine_segment_centroids: List of whole vertebrae centroids (in 3D) used to compute the spine curvature.
    :type spine_segment_centroids: list[tuple[float, float, float]]
    
    
    :param L5_key: Key name of L5. Default 'L5'.
    :type L5_key: str
    
    :param fct: Dictionary mapping level names to their corresponding four morphometry points in the order of [top_left,top_right,bottom_right,bottom_left]
    :type four_points_array_dict: dict{str: numpy.ndarray}
    
    :return: Two lists representing the joint distances and joint angles based on the IVJ centroids.
    The first two items in joint_dist and joint_angel are always 9999. The last item in joint_dist is always 9999.
    :rtype: tuple[list[float], list[float]]
    
    :Example:
    
    >>> centroids = [(1, 2, 3), (2, 3, 4), (9999, 9999, 9999), (4, 5, 6)]
    >>> joint_distances, joint_angles = calculate_vertebral_axes(IVJ_centroids, vertebra_centroids, spine_segments)
    >>> print(joint_distances, joint_angles)
    
    :Note: 
    1. The function considers missing centroids as having a value of (9999, 9999, 9999) and 
       assigns placeholder values accordingly.
    
    """
    SI = [(9999,9999,9999)]  #Needs to start with  9999,9999,9999 because joint over T1 is not defined
    AP = [(9999,9999,9999)]
    ML = [(9999,9999,9999)]
    
    vertebral_axes = {}
        
    for i,level in enumerate(level_names[:-1]):
        if (IVJ_centroids[level] == (9999,9999,9999)) or (IVJ_centroids[level_names[i+1]] == (9999,9999,9999)):
            SI.append((9999,9999,9999))
            AP.append((9999,9999,9999))
            ML.append((9999,9999,9999))

            vertebral_axes[level] = {'SI':(9999,9999,9999),'AP':(9999,9999,9999),'ML':(9999,9999,9999)}
        else:
            point1_array = np.array(IVJ_centroids[level])  # Upper joint for level
            point2_array = np.array(IVJ_centroids[level_names[i+1]])  # lower joint for level
            v1 = (point1_array - point2_array)
            uv1 = v1 / np.linalg.norm(v1)
            SI.append((uv1))
            point3_array = np.array(vertebrae_centroids[level])
            point4_array = np.array(spine_segment_centroids[level])
  
            v3temp =  (point3_array - point4_array) # approximating an AP direction.
            v2 = np.cross(v3temp,v1)
            uv2 = v2 / np.linalg.norm(v2)
            ML.append((uv2))
            uv3 = np.cross(uv1, uv2)
            AP.append((uv3))

            vertebral_axes[level] = {'SI':uv1,'AP':uv3,'ML':uv2}
  
    return vertebral_axes

"""
def calculate_vertebra_properties(instance_nii_path, semantic_nii_path):
    semantic_nii = NII.load(semantic_nii_path, seg=True)
    instance_nii = NII.load(instance_nii_path, seg=True)
    poi = calc_poi_from_subreg_vert(
        instance_nii,
        semantic_nii,
        subreg_id=[
            Location.Vertebra_Corpus,
            Location.Vertebra_Disc,
            Location.Vertebra_Disc_Superior,
            Location.Vertebra_Disc_Inferior,
            Location.Spinal_Cord,
            Location.Spinal_Canal,
        ],
    )
    poi, _ = calc_orientation_of_vertebra_PIR(
        poi=poi, vert=instance_nii, subreg=semantic_nii
    )
    vertebra_properties = {}
    for (vert_idx, point_id) in poi.centroids.keys():
        if point_id not in [50, 100]:
            continue
        point = poi.centroids[(vert_idx, point_id)]
        vert_name = v_idx2name.get(vert_idx, f"Unknown_{vert_idx}")
        if vert_name not in vertebra_properties:
            vertebra_properties[vert_name] = {
                "centroid": [9999.0, 9999.0, 9999.0],
                "lower_disk_center": [9999.0, 9999.0, 9999.0],
                "rotation": get_vert_direction_PIR(poi, vert_idx),
            }
        if point_id == 50:
            vertebra_properties[vert_name]["centroid"] = point
        elif point_id == 100:
            vertebra_properties[vert_name]["lower_disk_center"] = point
    return vertebra_properties

instance_nii_path = "/home/workstation/Desktop/dataset-bids_working_copy/derivatives_seg/sub-12252_ses-baseline_mod-T2w_seg-vert_msk.nii.gz"
semantic_nii_path = "/home/workstation/Desktop/dataset-bids_working_copy/derivatives_seg/sub-12252_ses-baseline_mod-T2w_seg-spine_msk.nii.gz"
results = calculate_vertebra_properties(instance_nii_path, semantic_nii_path)
"""
