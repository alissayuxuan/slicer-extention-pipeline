import tkinter as tk
from tkinter import filedialog
import glob
import os
import subprocess
from lxml import etree


def run_pipeline_all_patient():
    work_directory = entries['work_directory'].get()
    patient_data_directory = entries['patient_data_directory'].get()
    patient_data_output_directory = os.path.join(work_directory,entries['patient_data_output_directory'].get())
    model_creation_no = selected_var.get()
    try:
        for patient_ID in os.listdir(patient_data_directory):
            print(patient_ID)
            patient_directory_path = os.path.join(patient_data_output_directory,patient_ID)
            model_creation_setup_path = os.path.join(work_directory,r'base/setup/model_creation_base_setup.xml')
            analysis_setup_path = os.path.join(work_directory,r'base/setup/analysis_setup.xml')
            patient_setup_path = os.path.join(patient_directory_path,entries['output_setups_path'].get(),patient_ID+'_pipeline_setup.xml')

            run_pipeline(work_directory,model_creation_setup_path,analysis_setup_path,patient_setup_path,model_creation_no)
        tk.messagebox.showinfo('Success','Done.')
    except Exception as e:
        tk.messagebox.showinfo('Error',f'An error happened:\nPatient ID: {patient_ID}\n{e}.')

def run_pipeline(work_directory,model_creation_setup_path,analysis_setup_path,patient_setup_path,model_creation_no = '0'):
    if model_creation_no=='0':
        model_creation_script_path = os.path.join(work_directory,'Header_CreateModel_Marker_CT.py')
    elif model_creation_no=='1':
        model_creation_script_path = os.path.join(work_directory,'Header_CreateModel_Mets.py')
    print(work_directory)
    analysis_script_path = os.path.join(work_directory,'Header_RunActivities.py')
    model_creation_pipeline = ['python',model_creation_script_path,model_creation_setup_path,patient_setup_path]    
    analysis_pipeline = ['python',analysis_script_path,analysis_setup_path,patient_setup_path]
    
    print(model_creation_pipeline)
    result1 = subprocess.run(model_creation_pipeline,capture_output=True, text=True)
    print(analysis_pipeline)
    result2 = subprocess.run(analysis_pipeline,capture_output=True, text=True)
    
    if result1.stderr:
        raise ChildProcessError(f'Model Creation Error:\n{result1.stderr.strip()}')
    if result2.stderr:
        raise ChildProcessError(f'Analysis Error:\n{result2.stderr.strip()}')
    # print(result1.stdout.strip())
    # print(result2.stdout.strip())


def select_directory(entry):
    directory = filedialog.askdirectory()
    entry.delete(0, tk.END)
    entry.insert(0, directory)
    if entry == entries['work_directory']:
        auto_detect_basemodel(directory)

def select_file(entry):
    filepath = filedialog.askopenfilename()
    entry.delete(0, tk.END)
    entry.insert(0, filepath)

def select_files(entry):
    filepath = filedialog.askopenfilename()
    entry.insert(tk.END, filepath+' ')
def select_files_clear(entry):
    entry.delete(0, tk.END)


def create_folder(folder_path_list):
    for folder_path in folder_path_list:
        if not os.path.exists(folder_path):
            os.makedirs(folder_path)
            
def auto_detect_basemodel(directory):
    # Modify this pattern if necessary
    for display,variable, vtype,pattern in global_variables:
        if (vtype in ('Directory','File')) and (pattern != '') :
            full_pattern = os.path.join(directory, pattern)
            create_folder([full_pattern])
            files = glob.glob(full_pattern)
            if files:
                entries[variable].delete(0, tk.END)
                entries[variable].insert(0, files[0]) # Consider the first detected basemodel

def add_input_node(root,display,vtype,pattern):
    frame = tk.Frame(root, pady=5)
    frame.pack(fill=tk.X, padx=10)
    
    label = tk.Label(frame, text=display, width=25, anchor='w')
    label.pack(side=tk.LEFT)
    
    entry = tk.Entry(frame, width=50)
    entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
    
    if vtype == 'Directory' :
        btn = tk.Button(frame, text='Select', command=lambda e=entry: select_directory(e))
        btn.pack(side=tk.LEFT, padx=5)
    elif  vtype == 'File':
        btn = tk.Button(frame, text='Select', command=lambda e=entry: select_file(e))
        btn.pack(side=tk.LEFT, padx=5)
    elif vtype == 'Files':
        btn = tk.Button(frame, text='Select', command=lambda e=entry: select_files(e))
        btn.pack(side=tk.LEFT, padx=5)
        btn = tk.Button(frame, text='Clear', command=lambda e=entry: select_files_clear(e))
        btn.pack(side=tk.LEFT, padx=5)
    elif vtype == 'Entry':
        entry.delete(0, tk.END)
        entry.insert(0, pattern)
    return entry

def print_setup_all_patient():
    work_directory = entries['work_directory'].get()
    patient_data_directory = entries['patient_data_directory'].get()
    patient_data_output_directory = os.path.join(work_directory,entries['patient_data_output_directory'].get())
    
    patient_ID_display = ''
    for patient_ID in os.listdir(patient_data_directory):
        patient_directory_input_path = os.path.join(patient_data_directory,patient_ID)
        patient_directory_output_path = os.path.join(patient_data_output_directory,patient_ID)
        print_setup(patient_directory_input_path,patient_directory_output_path,patient_ID)
        patient_ID_display += patient_ID + '\n'
    tk.messagebox.showinfo('Success',f'Printed ID: \n{patient_ID_display}')

def print_setup(patient_directory_input_path,patient_directory_output_path,patient_ID):
    # Create the root element
    root_node = etree.Element('root')

    root_node.append(etree.Comment('Patient directory (folder)'))
    patient_directory_path_node = etree.SubElement(root_node, 'patient_directory_path')

    patient_info_node = etree.SubElement(root_node, 'patient_info')
    patient_info_node.append(etree.Comment('Patient ID'))
    patient_id_node = etree.SubElement(patient_info_node, 'patient_ID')

    model_creation_patient_node = etree.SubElement(root_node, 'model_creation')

    model_creation_patient_node.append(etree.Comment('Info file path (.mat)'))
    info_file_path_node = etree.SubElement(model_creation_patient_node, 'info_file_path')
    model_creation_patient_node.append(etree.Comment('Calibration trial path (.trc)'))
    calibration_trial_path_node = etree.SubElement(model_creation_patient_node, 'calibration_trial_path')

    output_node = etree.SubElement(root_node, 'output')

    output_node.append(etree.Comment('Model output directory (folder)'))
    output_model_path_node = etree.SubElement(output_node, 'output_model_path')
    output_node.append(etree.Comment('Fully scaled model output path(.osim)'))
    output_scaled_model_path_node = etree.SubElement(output_node, 'scaled_model_path')

    output_node.append(etree.Comment('Setup output directory (folder)'))
    output_setup_path_node = etree.SubElement(output_node, 'output_setups_path')
    output_node.append(etree.Comment('Spine loading output directory (folder)'))
    output_spine_loading_path_node = etree.SubElement(output_node, 'output_spine_loading_path')

    patient_id_node.text = str(patient_ID)
    info_file_path_node.text = os.path.join(patient_directory_input_path,entries['info_file_path'].get())

    calibration_trial_path_node.text = os.path.join(patient_directory_input_path,entries['calibration_trial_path'].get())

    output_model_path = os.path.join(patient_directory_output_path,entries['output_model_path'].get())
    output_scaled_model_path = os.path.join(patient_directory_output_path,entries['output_model_path'].get(), str(patient_ID) + '_FullyScaled.osim')
    output_setup_path = os.path.join(patient_directory_output_path,entries['output_setups_path'].get())
    output_spine_loading_path = os.path.join(patient_directory_output_path,entries['output_spine_loading_path'].get())
    output_model_path_node.text = output_model_path
    output_scaled_model_path_node.text = output_scaled_model_path
    output_setup_path_node.text = output_setup_path
    output_spine_loading_path_node.text = output_spine_loading_path
    
    create_folder([output_model_path,output_setup_path,output_spine_loading_path])

    patient_setup_file_path = os.path.join(patient_directory_output_path,entries['output_setups_path'].get(),patient_ID+'_pipeline_setup.xml')
    with open(patient_setup_file_path, 'wb') as file:
        file.write(etree.tostring(root_node, pretty_print=True))
        print(f'{patient_ID} Printed to {patient_setup_file_path}')

entries = {}
global_variables = [
    ('Work Directory'                           ,'work_directory'           , 'Directory'   ,''),
    ('Patient Data Directory'                   ,'patient_data_directory'   , 'Directory'   ,r'patient_data'),
    ('Patient Data Output Directory'            ,'patient_data_output_directory','Directory',r'result')
]
variables = [
    ('Info File Path'                           ,'info_file_path'           , 'Entry'       ,r'info.mat'),
    ('Calibration Trial Path'                   ,'calibration_trial_path'   , 'Entry'       ,r'Trial01.trc'),
    ('Model Output Path'                        ,'output_model_path'        , 'Entry'       ,r'models'),
    ('Fullyscaled Model Output Path'            ,'output_scaled_model_path' , 'Entry'       ,r'models'),
    ('Setup Output Path'                        ,'output_setups_path'       , 'Entry'       ,r'setup'),
    ('Spine Loading Output Path'                ,'output_spine_loading_path', 'Entry'       ,r'results')
]

root = tk.Tk()
root.title('Step 3 - Patient Setup Generator & Run Pipeline')

label1 = tk.Label(root, text='Patient Setup',font='Arial 14 bold')
label1.pack(pady=10)

label2 = tk.Label(root, text='Global Directory Setup')
label2.pack(pady=10)

for display, variable, vtype,pattern in global_variables:
    entries[variable] = add_input_node(root,display,vtype,pattern)

label3 = tk.Label(root, text='Patient Directory Setup (Relative Path to Patient\'s Directory)')
label3.pack(pady=10)

for display, variable, vtype,pattern in variables:
    entries[variable] = add_input_node(root,display,vtype,pattern)



btn_submit = tk.Button(root, text='Save Setup File', command=print_setup_all_patient)
btn_submit.pack(pady=20)

label4 = tk.Label(root, text='Run Pipeline',font='Arial 14 bold')
label4.pack(pady=15)


frame = tk.Frame(root, pady=5)
frame.pack(expand=True, anchor='center')
# Create two Radiobuttons
selected_var = tk.StringVar(value=0)
radio1 = tk.Radiobutton(frame, text='CT & Marker Pipeline (Default)', variable=selected_var, value=0)
radio2 = tk.Radiobutton(frame, text='CT no Marker Pipeline', variable=selected_var, value=1)
radio1.grid(row=0,column=0, padx=10)
radio2.grid(row=0,column=1, padx=10)

btn_run_pipeline = tk.Button(root, text='RUN', command=run_pipeline_all_patient)
btn_run_pipeline.pack(pady=20)

root.mainloop()
