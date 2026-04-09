import os
from pathlib import Path
import pandas as pd
import json
from TPTBox import NII, POI, Location, calc_poi_from_subreg_vert
from TPTBox.core.poi_fun.vertebra_direction import (
    calc_orientation_of_vertebra_PIR,
    get_direction, get_vert_direction_PIR
)
from TPTBox.core.vert_constants import v_idx2name
import numpy as np
from lxml import etree
from scipy.spatial import cKDTree


def create_labeled_subregs(path_vert: Path, path_subreg: Path, patient_id, subreg_ID, path_out: Path = None):
    """
    Create a labeled segmentation of any subregion from a vertebra segmentation and a subregion segmentation
    """
    from TPTBox import to_nii, NII

    # Define paths to segmentation files, clarify that the niftis are segmentations by setting seg=True
    vert_nii = NII.load(path_vert,True)
    subreg_nii = NII.load(path_subreg,True)

    # make sure the subregion segmentation is in the same space as the vertebra segmentation
    subreg_nii = subreg_nii.resample_from_to(vert_nii)

    # extract wanted label from subregion segmentation and multiply with vertebra segmentation
    nii_vb = subreg_nii.extract_label([subreg_ID])*vert_nii
    
    new_filename = f"sub-{patient_id}_seg-vb_msk.nii.gz"
    if path_out is None:
        path_out = path_vert/new_filename
    else:
        path_out = path_out/new_filename

    nii_vb.save(path_out)

    # convert to nrrd
    #out_nrrd = path_out.with_name(path_out.stem[:-4] + ".nrrd")
    #nii_vb.save_nrrd(str(out_nrrd))

    return path_out

def clean_muscle_segmentation(path_muscle_seg: Path, patient_id, path_out: Path):
    """
    This function loads a muscle segmentation NIfTI file, modifies the labels to remove vertebrae (segments >= 26),
    and saves the modified segmentation to a new nii- and nrrd-file.
    """
    # Load the muscle segmentation (nii.gz)
    muscle_seg = NII.load(path_muscle_seg,True)
    # get segmentation array and set labels >= 26 to 0
    labels = muscle_seg.get_array()
    labels[labels >=26] = 0
    muscle_seg.set_array_(labels)

    new_filename = f"sub-{patient_id}_seg-musc_clean_msk.nii.gz"
    if path_out is None:
        print(f"No derivatives folder for subject {patient_id}. Creating folder")
        path_out = Path(path_muscle_seg.parent.parent)/"derivatives"/patient_id
        path_out = Path(path_out)/new_filename
    else:
        path_out = path_out/new_filename

    # save as nii.gz
    muscle_seg.save(path_out)

    # convert to nrrd
    #out_nrrd = path_out.with_name(path_out.stem[:-4] + ".nrrd")
    #muscle_seg.save_nrrd(str(out_nrrd))

    return path_out

def convert_excel_to_json(excel_file_path: Path):
    # Load the Excel file and save as json
    df = pd.read_excel(excel_file_path, sheet_name=None)  
    for sheet_name, data in df.items():
        json_path = excel_file_path.with_suffix(".json")
        data.to_json(json_path, orient='records', indent=4)

    return json_path

def get_files(data_path: Path, patient_id, dir_out=None):
    """
    Finds the paths to the raw data, vertebral body segmentation, muscle segmentation,
    vertebra properties, and related files for a given patient ID in the specified data path.
    Moves files into derivatives/patient_id if needed and creates missing files if possible.
    """
    print(f"\nFinding files for patient {patient_id}.\n")
    # Initialize variables
    vol_fn = None
    dir_raw = None
    dir_deriv = None
    vb_seg_fn = None
    vert_seg_fn = None
    spine_seg_fn = None
    musc_seg_fn = None
    musc_seg_clean_fn = None
    vert_prop = None
    osim_info_fn = None

    # 2. Search all directories
    for root, dirs, files in os.walk(data_path):
        root_path = Path(root)

        print(f"root_path: {root_path}")

        # Raw data
        #if root_path.name == 'rawdata':
        # add session folder
        if 'rawdata' in root_path.parts and patient_id in root_path.parts:
            print("in rawdata")
            dir_raw = root_path
            for file in files:
                if patient_id in file and file.endswith('.nii.gz'):
                    vol_fn = root_path / file

        # Derivatives/<patient_id>
        #elif root_path.parts[-2:] == ('derivatives', patient_id):
        elif patient_id in root_path.parts:
            print("in derivatives")
            dir_deriv = root_path
            for file in files:
                if 'osim_info' in file and patient_id in file:
                    osim_info_fn = root_path / file
                if 'vert_msk.nii.gz' in file and patient_id in file:
                    vert_seg_fn = root_path / file
                elif 'spine_ctd.json' in file and patient_id in file:
                    spine_ctd_fn = root_path / file
                #elif 'spine_msk.nii.gz' in file and patient_id in file:
                elif ('spine_msk.nii.gz' in file or 'subreg_msk.nii.gz' in file) and patient_id in file:
                    spine_seg_fn = root_path / file
                elif 'vb_msk.nii.gz' in file and patient_id in file:
                    vb_seg_fn = root_path / file
                if 'musc_clean_msk' in file and patient_id in file:
                    musc_seg_clean_fn = root_path / file
                if 'vertebra_properties' in file and patient_id in file:
                    vert_prop = root_path / file


        # Muscles segmentation
        elif root_path.name == 'output_muscles':
            print("in muscle")
            for file in files:
                if patient_id in file and file.endswith('.nii.gz'):
                    musc_seg_fn = root_path / file

        # Vertebra properties
        elif 'vertebra_properties_resampled' in root_path.parts and root_path.name == patient_id:
            print("in vert prop")
            for file in files:
                if patient_id in file:
                    vert_prop = root_path / file

    # 3. Handle missing files
    if not vol_fn:
        print(f"Volume file not found for patient {patient_id}.")

    if not vb_seg_fn:
        print(f"Vertebral body segmentation file not found for patient {patient_id}. Attempt to create from vert_msk and spine_msk.")
        if not vert_seg_fn or not spine_seg_fn:
            print(f"Vertebra and subregion segmentation files not found for patient {patient_id}.")
        else:
            vb_seg_fn = create_labeled_subregs(vert_seg_fn, spine_seg_fn, patient_id, 49, dir_deriv)

    if not musc_seg_clean_fn:
        #print(f"Attempt to create clean muscle segmentation for patient {patient_id}.")
        #if not musc_seg_fn:
        #    print(f"Can't create clean muscle segmentation for patient {patient_id}. Please check for muscle segmentation file.")
        #else:
        #    musc_seg_clean_fn = clean_muscle_segmentation(musc_seg_fn, patient_id, dir_deriv)
        print(f"No muscle segmentation found for {patient_id} - skipping muscles.")

    if not vert_prop and vert_seg_fn and spine_seg_fn:
        print(f"Vertebra properties file not found for patient {patient_id}. Run vertebra_properties_main.")
        vert_prop_out = data_path / "vertebra_properties_resampled" / patient_id
        vert_prop_out.mkdir(parents=True, exist_ok=True)
        vert_prop = vertebra_properties_main(vert_seg_fn, spine_seg_fn, patient_id, output_path=vert_prop_out)
    elif vert_prop and (not vert_seg_fn or not spine_seg_fn):
        print(f"Can't create vertebra properties file for patient {patient_id}. Please check the vertebra and subregion segmentation files.")

    return (vol_fn, dir_raw, vb_seg_fn, musc_seg_clean_fn, vert_prop, osim_info_fn)


def calculate_vertebra_properties(vert_nii_path, subreg_nii_path):
    vert_nii = NII.load(vert_nii_path, seg=True)
    subreg_nii = NII.load(subreg_nii_path, seg=True)
    subreg_nii = subreg_nii.resample_from_to(vert_nii)

    poi = calc_poi_from_subreg_vert(
        vert_nii,
        subreg_nii,
        subreg_id=[
            Location.Vertebra_Corpus,
            Location.Vertebra_Disc,
            Location.Vertebra_Disc_Superior,
            Location.Vertebra_Disc_Inferior,
            Location.Spinal_Cord,
            Location.Spinal_Canal,
            Location.Vertebra_Direction_Posterior,
            Location.Vertebra_Direction_Inferior,
            Location.Vertebra_Direction_Right,
            Location.Additional_Vertebral_Body_Middle_Inferior_Median
        ],
    )
    return poi


def calculate_unit_vector(point1, point2):
    vector = np.array(point2) - np.array(point1)
    magnitude = np.linalg.norm(vector)
    return vector / magnitude if magnitude > 0 else np.zeros(3)


def create_vertebra_properties_json(poi_data, output_file):
    centroids = poi_data.extract_subregion(Location.Vertebra_Corpus)
    spline = centroids.fit_spline()
    spline_points = spline[0]
    tree = cKDTree(spline_points)
    vertebra_properties = {}

    for vertebra, points in poi_data.centroids.pois.items():

        vertebra_name = v_idx2name[vertebra]

        if 50 not in points:
            continue  # Skip vertebra if no centroid

        centroid = list(points[50])

        if 100 in points:
            lower_disk_center = list(points[100])
            distances, indices = tree.query(lower_disk_center)
            projected_point = spline_points[indices]
            lower_disk_center = projected_point.tolist() 

        elif 107 in points:
            lower_disk_center = list(points[107])
        else:
            lower_disk_center = [9999.0, 9999.0, 9999.0]

        if all(pid in points for pid in [50, 128, 129, 130]):
            rotation = [
                calculate_unit_vector(points[130], points[50]).tolist(),
                calculate_unit_vector(points[50], points[128]).tolist(),
                calculate_unit_vector(points[50], points[129]).tolist(),
            ]
        else:
            rotation = [[1.0, 0.0, 0.0], [0.0, 1.0, 0.0], [0.0, 0.0, 1.0]]

        vertebra_properties[vertebra_name] = {
            "centroid": centroid,
            "lower_disk_center": lower_disk_center,
            "rotation": rotation,
        }
        
    with open(output_file, "w") as f:
        json.dump(vertebra_properties, f, indent=4)

    return vertebra_properties


def vertebra_properties_main(vert_nii_path, subreg_nii_path, patient_id, output_path: Path):
    poi_result = calculate_vertebra_properties(vert_nii_path, subreg_nii_path).to_global()
    output_file = output_path / f"sub-{patient_id}_vertebra_properties.json"
    vertebra_properties = create_vertebra_properties_json(poi_result, output_file)
    return output_file


def create_base_setup(patient_id, data_path, base_model_dir, base_setup_dir):

    # Create the root element
    root = etree.Element('root')
    patient_directory_path = Path(data_path)/"derivatives"/patient_id

    # Add child elements
    model_creation_base_node = etree.SubElement(root, 'model_creation_base')
    basemodel_node = etree.SubElement(model_creation_base_node, 'base_model')

    basemodel_node.append(etree.Comment('Male basemodel path (.osim)'))
    male_basemodel_path_node = etree.SubElement(basemodel_node, 'male_basemodel_path')
    basemodel_node.append(etree.Comment('Male basemodel generic height in m'))
    male_basemodel_height_node = etree.SubElement(basemodel_node, 'male_basemodel_height')

    basemodel_node.append(etree.Comment('Female basemodel path (.osim)'))
    female_basemodel_path_node = etree.SubElement(basemodel_node, 'female_basemodel_path')
    basemodel_node.append(etree.Comment('Female basemodel generic height in m'))
    female_basemodel_height_node = etree.SubElement(basemodel_node, 'female_basemodel_height')

    basemodel_node.append(etree.Comment('CCC basemodel path (.osim)'))
    ccc_basemodel_path_node = etree.SubElement(basemodel_node, 'ccc_basemodel_path')

    marker_set_node = etree.SubElement(model_creation_base_node, 'marker_set')

    marker_set_node.append(etree.Comment('Male marker set file path (.xml)'))
    male_marker_set_path_node = etree.SubElement(marker_set_node, 'male_marker_set_path')
    marker_set_node.append(etree.Comment('Female marker set path (.xml)'))
    female_marker_set_path_node = etree.SubElement(marker_set_node, 'female_marker_set_path')


    scale_setup_node = etree.SubElement(model_creation_base_node, 'scale_setup')

    scale_setup_node.append(etree.Comment('Scale tool setup file path (.xml)'))
    scale_setup_path_node = etree.SubElement(scale_setup_node, 'scale_setup_path')


    #male_basemodel_path_node.text = rf'{base_model_dir}\MaleFullBodyModel_v2.0_OS4_no_marker.osim'
    male_basemodel_height_node.text = str(1.75)
    #female_basemodel_path_node.text = rf'{base_model_dir}\FemaleFullBodyModel_v2.0_OS4_no_marker.osim'
    female_basemodel_height_node.text = str(1.63)
    #ccc_basemodel_path_node.text = rf'{base_model_dir}\BaseFullbody_6DOF.osim'

    male_basemodel_path_node.text = str(Path(base_model_dir) / 'MaleFullBodyModel_v2.0_OS4_no_marker.osim')
    female_basemodel_path_node.text = str(Path(base_model_dir) / 'FemaleFullBodyModel_v2.0_OS4_no_marker.osim')
    ccc_basemodel_path_node.text = str(Path(base_model_dir) / 'BaseFullbody_6DOF.osim')
    male_marker_set_path_node.text = str(Path(base_model_dir) / 'markers_Male_VLStudy.xml')
    female_marker_set_path_node.text = str(Path(base_model_dir) / 'markers_Female_VLStudy.xml')
    scale_setup_path_node.text = str(Path(base_setup_dir) / 'scaleTool_Setup_KBedit.xml')

    #male_marker_set_path_node.text = rf'{base_model_dir}\markers_Male_VLStudy.xml'
    #female_marker_set_path_node.text = rf'{base_model_dir}\markers_Female_VLStudy.xml'
    #scale_setup_path_node.text = rf'{base_setup_dir}\scaleTool_Setup_KBedit.xml'

    #base_setup = f'{patient_directory_path}/model_creation_base_setup.xml'
    base_setup = str(Path(patient_directory_path) / 'model_creation_base_setup.xml')

    # Save the XML to a file
    with open(base_setup, 'wb') as file:
        file.write(etree.tostring(root, pretty_print=True))
    
    return base_setup

    

def create_patient_setup(patient_id, data_path):

    root = etree.Element('root')
    patient_directory_path = Path(data_path)/"derivatives"/patient_id
    patient_models_path = Path(data_path)/"models"/patient_id
    patient_results_path = Path(data_path)/"results"/patient_id

    root.append(etree.Comment('Patient directory (folder)'))
    patient_directory_path_node = etree.SubElement(root, 'patient_directory_path')

    patient_info_node = etree.SubElement(root, 'patient_info')
    patient_info_node.append(etree.Comment('Patient ID'))
    patient_id_node = etree.SubElement(patient_info_node, 'patient_ID')

    model_creation_patient_node = etree.SubElement(root, 'model_creation')

    model_creation_patient_node.append(etree.Comment('Info file path (.mat)'))
    info_file_path_node = etree.SubElement(model_creation_patient_node, 'info_file_path')
    model_creation_patient_node.append(etree.Comment('Calibration trial path (.trc)'))
    calibration_trial_path_node = etree.SubElement(model_creation_patient_node, 'calibration_trial_path')

    output_node = etree.SubElement(root, 'output')

    output_node.append(etree.Comment('Model output directory (folder)'))
    output_model_path_node = etree.SubElement(output_node, 'output_model_path')
    output_node.append(etree.Comment('Fully scaled model output path(.osim)'))
    output_scaled_model_path_node = etree.SubElement(output_node, 'scaled_model_path')

    output_node.append(etree.Comment('Setup output directory (folder)'))
    output_setup_path_node = etree.SubElement(output_node, 'output_setups_path')
    output_node.append(etree.Comment('Spine loading output directory (folder)'))
    output_spine_loading_path_node = etree.SubElement(output_node, 'output_spine_loading_path')

    patient_directory_path_node.text = str(patient_directory_path)

    patient_id_node.text = str(patient_id)
    info_file_path_node.text = os.path.join(patient_directory_path,f'sub-{patient_id}_osim_info.json')
    calibration_trial_path_node.text = ''

    output_model_path_node.text = str(patient_models_path)
    output_scaled_model_path_node.text = os.path.join(patient_models_path, f"sub-{patient_id}_" + '_FullyScaled.osim')
    output_setup_path_node.text = os.path.join(patient_directory_path)
    output_spine_loading_path_node.text = os.path.join(patient_results_path)

    patient_setup = f'{patient_directory_path}/sub-{patient_id}_patient_setup.xml'
    # Save the XML to a file
    with open(patient_setup, 'wb') as file:
        file.write(etree.tostring(root, pretty_print=True))

    return patient_setup

    
