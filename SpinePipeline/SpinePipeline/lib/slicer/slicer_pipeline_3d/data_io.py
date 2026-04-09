import slicer
import pandas as pd
import slicer
import numpy as np
#import pandas as pd
import json
import os
from scipy.io import savemat
from visualization import display_point


def load_IVJ_centroids_3d(centroid_file_path, level_name_list_whole, display=True):
    """
    Load the 3D coordinates of the Intervertebral Joint (IVJ) centroids from a fcsv file.

    The function reads the JSON file containing the 3D coordinates of the IVJ centroids and returns the data as a dictionary.

    :param centroid_file_path: The path to the JSON file containing the IVJ centroid data.
    :type centroid_file_path: str

    :return: A dictionary containing the IVJ centroid data.
    :rtype: dict

    :Example:

    >>> centroid_file_path = "C:/Users\danders7\OpenSim-Spine-Project\OpenSim-Spine-Project\opensim_pipeline\patient_data\10355\IVJ_centroids.json"
    >>> ivj_centroids = load_IVJ_centroids_3d(centroid_file_path)
    """
    centroids = {}

    if display:
        markup_list = slicer.mrmlScene.AddNewNodeByClass(
            "vtkMRMLMarkupsFiducialNode")
        markup_list.SetName("IVJ Centroids")
    IVJ_df = pd.read_csv(centroid_file_path, comment='#')
    for level in level_name_list_whole:
        if "IVJ-" + level in IVJ_df['label'].values:

            centroid = IVJ_df[IVJ_df['label'] == "IVJ-"+level].values[0][1:4]

            centroid_3D = (centroid[0], centroid[1], centroid[2])
            centroids[level] = centroid_3D

            if display:
                display_point(markup_list, centroid_3D,
                              'IVJ_ctr_' + level)
        else:
            centroids[level] = (9999, 9999, 9999)

    return centroids


def input_demographic_data():
    """
    Collects and returns patient's demographic information interactively.

    :return: 
        - patient_id: Patient's ID
        - sex: Patient's gender. 'M' for male and 'F' for female.
        - height: Patient's height in cm.
        - weight: Patient's weight in kg.
    :rtype: tuple (str, float, float)

    :Note:
    - User interaction is required. Should be intergrated in to a slicer GUI.
    """
    patient_id = input('Enter patient ID.')
    sex = ''
    while sex not in ['M', 'F']:
        sex = input('Enter patient gender. M for male, F for female')
    height = float(input('Enter patient height in cm'))
    weight = float(input('Enter patient weight in kg'))
    return patient_id, sex, height, weight


def print_info_file_3D(patient_id, sex, height, weight, age, joint_dist, vertebral_axes, ivjs, muscledataCSA_L, muscledataCSA_R, muscledataMAX_L, muscledataMAX_R, muscledataMAZ_L, muscledataMAZ_R, info_path):
    """
    Save the info file with 3D information is .json format.

    :param sex: Gender of the patient. Can be 'M' (Male) or 'F' (Female).
    :type sex: str

    :param height: Height of the patient in centimeters.
    :type height: float

    :param weight: Weight of the patient in kilograms.
    :type weight: float

    :param joint_dist: Distances between patient inter-vertebra joints. See :func:`calculate_IVJ_centroids`
    :type joint_dist: list or np.ndarray

    :param joint_angle: Angles of the patient's inter-vertebra joints. See :func:`calculate_IVJ_centroids`
    :type joint_angle: list or np.ndarray

    :param muscledataCSA (_L and _R): Data for muscle Cross-sectional Areas (CSA), left and right sides. See :func:`get_muscle_info_from_database_3D`
    :type muscledataCSA: np.ndarray

    :param muscledataMAX (_L and _R): Data for muscle's AP moment arm (left and right). See :func:`get_muscle_info_from_database_3D`
    :type muscledataMAX: np.ndarray

    :param muscledataMAZ(_L and _R): Data for muscle's ML moment arm (left and right). See :func:`get_muscle_info_from_database_3D`
    :type muscledataMAZ: np.ndarray

    :param info_path: Path to the output file where the data will be saved. Defaults to 'osim_info.json'.
    :type info_path: str
    """

    # Create a new dictionary to save info data to....
    osim_info = dict()
    osim_info['Height'] = height
    osim_info['Weight'] = weight
    osim_info['Age'] = age
    osim_info['Sex'] = sex

    cols = ['T1', 'T2', 'T3', 'T4', 'T5', 'T6', 'T7', 'T8',
            'T9', 'T10', 'T11', 'T12', 'L1', 'L2', 'L3', 'L4', 'L5']
    '''
    # this still needs to be updated for 3D orientations, once they're created.
    vert_trans = pd.DataFrame(np.zeros((3,17)),columns = cols,index = ['AP','SI','ML'])
    vert_trans.loc['SI'] = joint_dist
    osim_info['vert_translations'] = vert_trans.to_json()
    vert_rot = pd.DataFrame(np.zeros((3,17)),columns = cols,index = ['AP','SI','ML'])
    vert_rot.loc['ML'] = joint_angle
    osim_info['vert_rotations'] = vert_rot.to_json()
    '''

    vert_trans = pd.DataFrame(
        np.zeros((3, 17)), columns=cols, index=['AP', 'SI', 'ML'])
    translations = [[joint_dist[i][0] for i in range(17)], [
        joint_dist[i][1] for i in range(17)], [joint_dist[i][2] for i in range(17)]]
    vert_trans.loc[['AP', 'SI', 'ML']] = translations

    osim_info['vert_translations'] = vert_trans.to_json()
    osim_info['vert_axes_in_world'] = pd.DataFrame(vertebral_axes).to_json()
    osim_info['IVJ_centers_in_world'] = pd.DataFrame(ivjs).to_json()

    musclerows = ['PM', 'RA', 'SA', 'lD', 'TR',
                  'EO', 'IO', 'ES', 'TS', 'PS', 'QL']
    # the muscle CSA
    muscle_L1 = pd.DataFrame(muscledataCSA_L, columns=cols, index=musclerows)
    muscle_R1 = pd.DataFrame(muscledataCSA_R, columns=cols, index=musclerows)

    osim_info['muscleCSA_L'] = muscle_L1.to_json()
    osim_info['muscleCSA_R'] = muscle_R1.to_json()

    # the muscle AP positions = MAX
    muscle_L2 = pd.DataFrame(muscledataMAX_L, columns=cols, index=musclerows)
    muscle_R2 = pd.DataFrame(muscledataMAX_R, columns=cols, index=musclerows)

    osim_info['muscleAP_L'] = muscle_L2.to_json()
    osim_info['muscleAP_R'] = muscle_R2.to_json()

    # the muscle ML positions = MAZ
    muscle_L3 = pd.DataFrame(muscledataMAZ_L, columns=cols, index=musclerows)
    muscle_R3 = pd.DataFrame(muscledataMAZ_R, columns=cols, index=musclerows)

    osim_info['muscleML_L'] = muscle_L3.to_json()
    osim_info['muscleML_R'] = muscle_R3.to_json()

    out_file_path = os.path.join(info_path, f'sub-{patient_id}_osim_info.json')
    out_file = open(out_file_path, 'w+')
    json.dump(osim_info, out_file)
    out_file.close()

    print(f'Save osim_info.json to {info_path}')
    return osim_info

# Ignoring muscle data for now (not available)
def print_info_file_3D_no_muscle(patient_id, sex, height, weight, age, joint_dist, vertebral_axes, ivjs, info_path):
    """
    Save the info file with 3D information is .json format.

    :param sex: Gender of the patient. Can be 'M' (Male) or 'F' (Female).
    :type sex: str

    :param height: Height of the patient in centimeters.
    :type height: float

    :param weight: Weight of the patient in kilograms.
    :type weight: float

    :param joint_dist: Distances between patient inter-vertebra joints. See :func:`calculate_IVJ_centroids`
    :type joint_dist: list or np.ndarray

    :param joint_angle: Angles of the patient's inter-vertebra joints. See :func:`calculate_IVJ_centroids`
    :type joint_angle: list or np.ndarray

    :param info_path: Path to the output file where the data will be saved. Defaults to 'osim_info.json'.
    :type info_path: str
    """

    # Create a new dictionary to save info data to....
    osim_info = dict()
    osim_info['Height'] = height
    osim_info['Weight'] = weight
    osim_info['Age'] = age
    osim_info['Sex'] = sex

    cols = ['T1', 'T2', 'T3', 'T4', 'T5', 'T6', 'T7', 'T8',
            'T9', 'T10', 'T11', 'T12', 'L1', 'L2', 'L3', 'L4', 'L5']
    '''
    # this still needs to be updated for 3D orientations, once they're created.
    vert_trans = pd.DataFrame(np.zeros((3,17)),columns = cols,index = ['AP','SI','ML'])
    vert_trans.loc['SI'] = joint_dist
    osim_info['vert_translations'] = vert_trans.to_json()
    vert_rot = pd.DataFrame(np.zeros((3,17)),columns = cols,index = ['AP','SI','ML'])
    vert_rot.loc['ML'] = joint_angle
    osim_info['vert_rotations'] = vert_rot.to_json()
    '''

    vert_trans = pd.DataFrame(
        np.zeros((3, 17)), columns=cols, index=['AP', 'SI', 'ML'])
    translations = [[joint_dist[i][0] for i in range(17)], [
        joint_dist[i][1] for i in range(17)], [joint_dist[i][2] for i in range(17)]]
    vert_trans.loc[['AP', 'SI', 'ML']] = translations

    osim_info['vert_translations'] = vert_trans.to_json()
    osim_info['vert_axes_in_world'] = pd.DataFrame(vertebral_axes).to_json()
    osim_info['IVJ_centers_in_world'] = pd.DataFrame(ivjs).to_json()

    out_file_path = os.path.join(info_path, f'sub-{patient_id}_osim_info.json')
    out_file = open(out_file_path, 'w+')
    json.dump(osim_info, out_file)
    out_file.close()

    print(f'Save osim_info.json to {info_path}')
    return osim_info


def format_centroids_from_properties(veretebra_properties, level_C7_S1,centroid_name, display=True):
    """
    Load the 3D coordinates of the Intervertebral Joint (IVJ) centroids from a fcsv file.

    The function reads the JSON file containing the 3D coordinates of the IVJ centroids and returns the data as a dictionary.

    :param centroid_file_path: The path to the JSON file containing the IVJ centroid data.
    :type centroid_file_path: str

    :return: A dictionary containing the IVJ centroid data.
    :rtype: dict

    :Example:

    >>> centroid_file_path = "C:/Users\danders7\OpenSim-Spine-Project\OpenSim-Spine-Project\opensim_pipeline\patient_data\10355\IVJ_centroids.json"
    >>> ivj_centroids = load_IVJ_centroids_3d(centroid_file_path)
    """
    centroids = {}
    if display:
        markup_list = slicer.mrmlScene.AddNewNodeByClass(
            "vtkMRMLMarkupsFiducialNode")
        markup_list.SetName("IVJ Centroids")
    for i,level in enumerate(level_C7_S1[:-1]):
        if level in veretebra_properties:

            centroid = veretebra_properties[level][centroid_name]

            centroid_3D = (centroid[0], centroid[1], centroid[2])
            centroids[level_C7_S1[i+1]] = centroid_3D

            if display:
                display_point(markup_list, centroid_3D,
                              centroid_name+ "_" + level)
        else:
            centroids[level_C7_S1[i+1]] = (9999, 9999, 9999)

    return centroids

def load_vertebra_properties(vertebra_properties_path):
    """
    Load the vertebral properties from a JSON file and return the data as a dictionary.

    :param vertebra_properties_path: The path to the JSON file containing the vertebral properties.
    :type vertebra_properties_path: str

    :return: A dictionary containing the vertebral properties.
    :rtype: dict

    :Example:

    >>> vertebra_properties_path = "C:/Users\danders7\OpenSim-Spine-Project\OpenSim-Spine-Project\opensim_pipeline\patient_data\10355\vertebra_properties.json"
    >>> vertebra_properties = vertebra_properties_to_dict(vertebra_properties_path)
    """
    with open(vertebra_properties_path) as f:
        vertebra_properties = json.load(f)
    
    return vertebra_properties


def format_rotations_from_properties(veretebra_properties, level_name_list_whole, display=True):
    rotations = {}
    for level in level_name_list_whole:
        if level in veretebra_properties:

            rotation = np.array(veretebra_properties[level]['rotation'])

            rotations[level] = {'ML': (rotation[0]), 
                                'AP': (rotation[1]), 
                                'SI': (rotation[2])}
        else:

            rotations[level] = {'ML': [9999,9999,9999],
                                'AP': [9999,9999,9999],
                                'SI': [9999,9999,9999]}
                                

    return rotations

def load_patient_data(patient_data_path, patient_id):
    """
    Load the patient data from a csv file and return the data as a dictionary.

    :param patient_data_path: The path to the JSON file containing the patient data.
    :type patient_data_path: str

    :return: A dictionary containing the patient data.
    :rtype: dict

    :Example:

    >>> patient_data_path = "C:/Users\danders7\OpenSim-Spine-Project\OpenSim-Spine-Project\opensim_pipeline\patient_data\10355\patient_data.csv"
    >>> patient_data = load_patient_data(patient_data_path, '10355')
    """
    patient_data = pd.read_csv(patient_data_path)

    patient = {
        'sex': patient_data[patient_data['broadband_id'] == patient_id]['sex'].values[0],
        'height': patient_data[patient_data['broadband_id'] == patient_id]['height'].values[0],
        'weight': patient_data[patient_data['broadband_id'] == patient_id]['weight'].values[0],
        'age': patient_data[patient_data['broadband_id'] == patient_id]['age'].values[0],
        'patient_id': patient_id

    }
    return patient