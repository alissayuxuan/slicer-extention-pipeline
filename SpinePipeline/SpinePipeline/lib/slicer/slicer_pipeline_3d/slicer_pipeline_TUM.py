from data_io import print_info_file_3D, print_info_file_3D_no_muscle, format_centroids_from_properties,format_rotations_from_properties, load_vertebra_properties
from muscle_processing import calculate_muscle_measurement_database, get_muscle_info_from_database_3D
from visualization import display_axial_planes, get_axial_i_coordinate_dict
from spine_processing import calculate_centroid_distance, calculate_vertebral_axes
from transformation import get_ijk_to_ras_array, get_ras_to_ijk_array
from utils import set_segments_name_by_map, get_segment_arrays_dict, get_existing_segment_list, get_existing_list
import slicer
import os
import importlib
import json
import re
import sys
import argparse

# Import your modules
import utils
import transformation
import data_io
import spine_processing
import visualization
import muscle_processing

# Reload the modules to ensure the latest changes are used
importlib.reload(utils)
importlib.reload(transformation)
importlib.reload(data_io)
importlib.reload(spine_processing)
importlib.reload(visualization)
importlib.reload(muscle_processing)

# Init
muscle_segment_map = {
    'Segment_1': 'L_PM',  # Pectoralis Major
    'Segment_2': 'R_PM',  # Pectoralis Major
    'Segment_3': 'L_RA',  # Rectus Abdominus
    'Segment_4': 'R_RA',  # Rectus Abdominus
    'Segment_5': 'L_SA',  # Serratus Anterior
    'Segment_6': 'R_SA',  # Serratus Anterior
    'Segment_7': 'L_LD',  # Latissimus Dorsi
    'Segment_8': 'R_LD',  # Latissimus Dorsi
    'Segment_9': 'L_TR',  # Trapezius
    'Segment_10': 'R_TR',  # Trapezius
    'Segment_11': 'L_EO',  # External Obliques
    'Segment_12': 'R_EO',  # External Obliques
    'Segment_13': 'L_IO',  # Internal Obliques
    'Segment_14': 'R_IO',  # Internal Obliques
    'Segment_15': 'L_ES',  # Erector Spinae
    'Segment_16': 'R_ES',  # Erector Spinae
    'Segment_17': 'L_TS',  # Transversospinalis
    'Segment_18': 'R_TS',  # Transversospinalis
    'Segment_21': 'L_PS',  # Psoas Major
    'Segment_22': 'R_PS',  # Psoas Major
    'Segment_23': 'L_QL',  # Quadratus Lumborum
    'Segment_24': 'R_QL',  # Quadratus Lumborum
    'Segment_26': 'L5',
    'Segment_27': 'L4',
    'Segment_28': 'L3',
    'Segment_29': 'L2',
    'Segment_30': 'L1',
    'Segment_31': 'T12',
    'Segment_32': 'T11',
    'Segment_33': 'T10',
    'Segment_34': 'T9',
    'Segment_35': 'T8',
    'Segment_36': 'T7',
    'Segment_37': 'T6',
    'Segment_38': 'T5',
    'Segment_39': 'T4',
    'Segment_40': 'T3',
    'Segment_41': 'T2',
    'Segment_42': 'T1'
}
vertebra_segment_map = {
    'Segment_7': 'C7',
    'Segment_8': 'T1',
    'Segment_9': 'T2',
    'Segment_10': 'T3',
    'Segment_11': 'T4',
    'Segment_12': 'T5',
    'Segment_13': 'T6',
    'Segment_14': 'T7',
    'Segment_15': 'T8',
    'Segment_16': 'T9',
    'Segment_17': 'T10',
    'Segment_18': 'T11',
    'Segment_19': 'T12',
    'Segment_20': 'L1',
    'Segment_21': 'L2',
    'Segment_22': 'L3',
    'Segment_23': 'L4',
    'Segment_24': 'L5',
    'Segment_25': 'Sacrum'
}
level_L5_T1 = ['L5', 'L4', 'L3', 'L2', 'L1', 'T12', 'T11',
               'T10', 'T9', 'T8', 'T7', 'T6', 'T5', 'T4', 'T3', 'T2', 'T1']
level_C7_S1 = ['C7', 'T1', 'T2', 'T3', 'T4', 'T5', 'T6', 'T7', 'T8', 'T9',
               'T10', 'T11', 'T12', 'L1', 'L2', 'L3', 'L4', 'L5', 'S1']
level_name_map = {
    'T1': 1,
    'T2': 2,
    'T3': 3,
    'T4': 4,
    'T5': 5,
    'T6': 6,
    'T7': 7,
    'T8': 8,
    'T9': 9,
    'T10': 10,
    'T11': 11,
    'T12': 12,
    'L1': 13,
    'L2': 14,
    'L3': 15,
    'L4': 16,
    'L5': 17}

# %%
muscle_index_list = [1,    2,    3,    4,    5,
                     7,    8,   10,    11,   13,   14]

# %% [markdown]
# # Main


#def main(patient_id, patient_id_int, sex, height, weight, data_path, volume_filename=None, muscle_segmentation_filename=None, vertebra_segmentation_filename=None, vertebra_properties_filename=None, info_file_name='info.mat'):

# removed muscle segmentation for now (not available) -> adjust function definition accordingly
def main(patient_id, patient_id_int, age, sex, height, weight, data_path, volume_filename=None, vertebra_segmentation_filename=None, vertebra_properties_filename=None, info_file_name='info.mat'):

    print("start main: slicer pipeline")
    # setting up file paths
    volume_path = os.path.join(
        data_path, volume_filename)
    #muscle_segmentation_path = os.path.join(
    #    data_path, muscle_segmentation_filename)
    vertebra_segmentation_path = os.path.join(
        data_path, vertebra_segmentation_filename)
    vertebra_properties_path = os.path.join(
        data_path, vertebra_properties_filename)
    
    # load files only if all available (into slicer)
    #if data_path and volume_filename and muscle_segmentation_filename and vertebra_segmentation_filename:
    if data_path and volume_filename and vertebra_segmentation_filename:

        print("load files into slicer")

        slicer.util.loadVolume(volume_path)
        slicer.util.loadSegmentation(vertebra_segmentation_path)

        print("finish loading files into slicer")
        #slicer.util.loadSegmentation(muscle_segmentation_path)

    volume_node = slicer.util.getNodesByClass('vtkMRMLScalarVolumeNode')[0]
    if volume_node:
        print("volume_node -> volume_3D_array")
        volume_3D_array = slicer.util.arrayFromVolume(volume_node)
    else:
        print('Volume node not found. Please check the file name or node name.')

    segmentation_node_list = slicer.util.getNodesByClass(
        'vtkMRMLSegmentationNode')
    print("segmentation_node_list")
    # calculate dictionary with (level name : vertebral body segmentation centroids)
    # rename segments, create 3D-array (mask) for each vertebra
    print("calculate dictionary, rename segments, create 3D-array for each vertebra")
    vertebra_segmentation_node = segmentation_node_list[0]
    set_segments_name_by_map(vertebra_segmentation_node, vertebra_segment_map)
    vertebra_segment_arrays_dict = get_segment_arrays_dict(
        vertebra_segmentation_node, volume_node)

    # vertebra_segment_centroids_dict = get_segment_centroids_dict(
    #    vertebra_segmentation_node, display=False, markup_node_name='Vertebra_Centroids')

    # load centroids from property file
    print("load centroids from property file")
    vertebra_properties = load_vertebra_properties(vertebra_properties_path)

    vertebra_segment_centroids_dict = {
        level: vertebra_properties[level]['centroid'] for level in vertebra_properties.keys()}

    # calculate muscle segmentation centroids and mask (same as before with vertebra)
    
    """
    muscle_segmentation_node = segmentation_node_list[1]
    set_segments_name_by_map(muscle_segmentation_node, muscle_segment_map)
    muscle_segment_arrays_dict = get_segment_arrays_dict(
        muscle_segmentation_node, volume_node)
    """
    

    #  calculate spine (geometical) measurements in 3d
    print("caculate spine measurements in 3d")
    print("calculate IVJ_centroids_3D")
    IVJ_centroids_3D = format_centroids_from_properties(
        vertebra_properties, level_C7_S1[::-1], 'lower_disk_center', display=True)

    print("calculaze joint_dist_3D")
    joint_dist_3D = calculate_centroid_distance(
        IVJ_centroids_3D, level_L5_T1[::-1])
    
    print("calculate vertebral_axes")
    vertebral_axes = format_rotations_from_properties(vertebra_properties, level_L5_T1, display=True)

    # setup variables for display and muscle csa calculation
    # coordinate transformation from voxel space (ijk) to world space (RAS) and vice versa 
    print("setup variables for display")
    ijk_to_ras_array = get_ijk_to_ras_array(volume_node)
    ras_to_ijk_array = get_ras_to_ijk_array(volume_node)
    print(vertebra_segmentation_node)
    level_name_list = get_existing_segment_list(
        vertebra_segmentation_node, level_L5_T1)

    level_name_list= get_existing_list(level_name_list, vertebra_properties)

    # calculate vertebrae centroid plane for muscle measurements and displays plane
    print("calculate vertebrae centroid plane")
    axial_plane_i_dict = get_axial_i_coordinate_dict(
        vertebra_segment_centroids_dict, level_name_list, ras_to_ijk_array)

    display_axial_planes(axial_plane_i_dict, level_name_list,
                         volume_3D_array.shape, ijk_to_ras_array)

    # calculate muscle crosssection(CSA), horizontal distance(MAX) and vertical distance(MAZ) in slice
    """
    database = calculate_muscle_measurement_database(
        patient_id_int,
        volume_3D_array, vertebra_segment_arrays_dict, muscle_segment_arrays_dict,
        level_name_list,
        axial_plane_i_dict, ijk_to_ras_array, level_name_map)

    muscledataCSA_L, muscledataCSA_R, muscledataMAX_L, muscledataMAX_R, muscledataMAZ_L, muscledataMAZ_R = get_muscle_info_from_database_3D(
        database, muscle_index_list, level_L5_T1)
    """

    out_path = os.path.join(os.path.join(data_path, 'derivatives'), patient_id)

    # ---------------------------------Make (opensim) Info File--------------------------------- 
    #osim_info = print_info_file_3D(patient_id, sex, height, weight, age, joint_dist_3D, vertebral_axes, IVJ_centroids_3D, muscledataCSA_L,
    #                               muscledataCSA_R, muscledataMAX_L, muscledataMAX_R, muscledataMAZ_L, muscledataMAZ_R, out_path)
    print("create osim_info")
    osim_info = print_info_file_3D_no_muscle(patient_id, sex, height, weight, age, joint_dist_3D, vertebral_axes, IVJ_centroids_3D, out_path)

if __name__ == '__main__':

    #data_path, patient_id, age, sex, height, weight, volume_filename, vb_segmentation_filename, muscle_segmentation_filename, vertebra_properties_filename = sys.argv[1:11]
    data_path, patient_id, age, sex, height, weight, volume_filename, vb_segmentation_filename, vertebra_properties_filename = sys.argv[1:10]

    print(f"Processing {patient_id}")
    match = re.search(r'\d+', patient_id)
    patient_id_int = int(match.group()) if match else None
    #main(patient_id, patient_id_int, sex, height, weight, data_path,
    #        volume_filename, muscle_segmentation_filename, vb_segmentation_filename, vertebra_properties_filename)
    main(patient_id, patient_id_int, sex, height, weight, data_path,
        volume_filename, vb_segmentation_filename, vertebra_properties_filename)

    slicer.util.quit()
