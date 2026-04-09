import sys
import os
import json
import shutil
from pathlib import Path
import slicer

sys.path.insert(0, str(Path(__file__).parent))
from utils_main import get_files, convert_excel_to_json

def run(data_path, patient_id):
        
        data_path = Path(data_path)  
 
        derivatives_path = data_path / 'derivatives'
        patient_deriv_path = derivatives_path / patient_id
        #osim_file_path = patient_deriv_path/f"sub-{patient_id}_osim_info.json"


        ###############################################################################
        ######################## Preprocessing ########################################
        ###############################################################################

        # Find all matching files
        matching_files = [item for item in derivatives_path.iterdir() if item.is_file() and patient_id in item.name]
        
        # Move matching files (patient files) to patient-specific directory if not already done
        if matching_files:
            if not patient_deriv_path.exists():
                print(f"Creating {patient_deriv_path} and moving files...")
                patient_deriv_path.mkdir(parents=True, exist_ok=True)
                for item in matching_files:
                    shutil.move(str(item), str(patient_deriv_path / item.name))
        
        print("finished moving files")
        # Find or create relevant files to run Slicer Pipeline
        volume_filename, dir_raw, vb_segmentation_filename, muscle_segmentation_clean_filename, vertebra_properties_filename, osim_file = get_files(
            data_path, patient_id)
        
        print(f"########## Finished preprocessing for {patient_id} ##########")

        return volume_filename, dir_raw, vb_segmentation_filename, muscle_segmentation_clean_filename, vertebra_properties_filename, osim_file


if __name__ == "__main__":
    data_path, preproc_result_path, patient_id = sys.argv[1:4]

    volume_filename, dir_raw, vb_segmentation_filename, muscle_segmentation_clean_filename, vertebra_properties_filename, osim_file = run(data_path, patient_id)

    result = {
        "volume_filename": str(volume_filename) if volume_filename else None,
        "dir_raw": str(dir_raw) if dir_raw else None,
        "vb_segmentation_filename": str(vb_segmentation_filename) if vb_segmentation_filename else None,
        "muscle_segmentation_clean_filename": str(muscle_segmentation_clean_filename) if muscle_segmentation_clean_filename else None,
        "vertebra_properties_filename": str(vertebra_properties_filename) if vertebra_properties_filename else None,
        "osim_file": str(osim_file) if osim_file else None,
    }

    os.makedirs(os.path.dirname(preproc_result_path), exist_ok=True)
    
    with open(preproc_result_path, 'w') as f:
        json.dump(result, f, indent=4)

    print(f"Preprocessing results saved: {preproc_result_path}")