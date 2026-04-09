from lxml import etree
import os
import numpy as np
import opensim as osim
from scipy.interpolate import interp1d
def get_base_setup_info(base_setup_path):
    """
    Retrieves base setup information from the provided XML path.

    :param base_setup_path: Path to the XML file containing base setup information.
    :type base_setup_path: str

    :return: A dictionary containing the following keys and their corresponding values:
        - male_basemodel_path (str): Path to the male base model.
        - male_marker_set_path (str): Path to the male marker set.
        - male_basemodel_height (float): Male base model generic height in meter.
        - female_basemodel_path (str): Path to the female base model.
        - female_marker_set_path (str): Path to the female marker set.
        - female_basemodel_height (float): Female base model generic height in meter.
        - ccc_basemodel_path (str): Path to the CCC base model.
        - scale_setup_path (str): Path to the scale setup file.
    :rtype: dict{str:str/float}
    """
    tree = etree.parse(base_setup_path)
    base_setup_info = {}

    base_setup_info['male_basemodel_path'] = tree.xpath('.//male_basemodel_path')[0].text
    base_setup_info['male_marker_set_path'] = tree.xpath('.//male_marker_set_path')[0].text
    base_setup_info['male_basemodel_height'] = float(tree.xpath('.//male_basemodel_height')[0].text)

    base_setup_info['female_basemodel_path'] = tree.xpath('.//female_basemodel_path')[0].text
    base_setup_info['female_marker_set_path'] = tree.xpath('.//female_marker_set_path')[0].text
    base_setup_info['female_basemodel_height'] = float(tree.xpath('.//female_basemodel_height')[0].text)

    base_setup_info['ccc_basemodel_path'] = tree.xpath('.//ccc_basemodel_path')[0].text
    base_setup_info['scale_setup_path'] = tree.xpath('.//scale_setup_path')[0].text

    return base_setup_info

def create_folder(folder_path_list):
    """
    Creates folders for the provided list of paths if they don't exist.

    :param folder_path_list: List of folder paths to be created.
    :type folder_path_list: list of str
    """
    for folder_path in folder_path_list:
        if not os.path.exists(folder_path):
            os.makedirs(folder_path)

    for folder_path in folder_path_list:
        if not os.path.exists(folder_path):
            os.makedirs(folder_path)

def get_patient_setup_info(patient_setup_path):
    """
    Retrieves patient setup information from the provided XML path.

    :param patient_setup_path: Path to the XML file containing patient setup information.
    :type patient_setup_path: str

    :return: A dictionary containing the following keys and their corresponding values:
        - patient_directory_path (str): Path to the patient's directory.
        - patient_ID (str): ID of the patient.
        - info_file_path (str): Path to the info.mat file.
        - calibration_trial_path (str): Path to the calibration trial file.
        - output_model_path (str): Path to the output model.
        - scaled_model_path (str): Path to the output Fullyscaled_model.osim.
        - output_setups_path (str): Path to the output setups.
        - output_spine_loading_path (str): Path to the output spine loading.
    :rtype: dict
    """
    tree = etree.parse(patient_setup_path)
    patient_setup_info = {}
    patient_setup_info['patient_directory_path'] = tree.xpath('.//patient_directory_path')[0].text
    patient_setup_info['patient_ID'] = tree.xpath('.//patient_ID')[0].text
    patient_setup_info['info_file_path'] = tree.xpath('.//info_file_path')[0].text
    patient_setup_info['calibration_trial_path'] = tree.xpath('.//calibration_trial_path')[0].text

    patient_setup_info['output_model_path'] = tree.xpath('.//output_model_path')[0].text
    patient_setup_info['scaled_model_path'] = tree.xpath('.//scaled_model_path')[0].text
    patient_setup_info['output_setups_path'] = tree.xpath('.//output_setups_path')[0].text
    #patient_setup_info['output_spine_loading_path'] = tree.xpath('.//output_spine_loading_path')[0].text

    return patient_setup_info

