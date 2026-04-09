import tkinter as tk
from tkinter import filedialog
import glob
import os
from lxml import etree

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


def on_radio_change():
    global variables
    if selected_var.get() == '0':
        variables = variables_no_marker
    elif selected_var.get() == '1':
        variables = variables_marker
    auto_detect_basemodel(entries['work_directory'].get())

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

def auto_detect_basemodel(directory):
    global variables
    # Modify this pattern if necessary
    for display,variable, vtype,pattern in variables:
        if (vtype in ('Directory','File')) and (pattern != '') :
            full_pattern = os.path.join(directory, pattern)
            files = glob.glob(full_pattern)
            if files:
                entries[variable].delete(0, tk.END)
                entries[variable].insert(0, files[0]) # Consider the first detected basemodel
    
    full_pattern = os.path.join(directory, r'base\setup')
    files = glob.glob(full_pattern)
    if files:
        entries['output_path'].delete(0, tk.END)
        entries['output_path'].insert(0, files[0]) # Consider the first detected basemodel


def print_setup():
    # Create the root element
    root = etree.Element('root')
    node_dict = {}
    # Add child elements
    node_dict['model_creation_base'] = etree.SubElement(root, 'model_creation_base')

    node_dict['basemodel'] = etree.SubElement(node_dict['model_creation_base'], 'base_model')

    node_dict['basemodel'].append(etree.Comment('Male basemodel path (.osim)'))
    node_dict['male_basemodel_path'] = etree.SubElement(node_dict['basemodel'], 'male_basemodel_path')
    node_dict['basemodel'].append(etree.Comment('Male basemodel generic height in m'))
    node_dict['male_basemodel_height'] = etree.SubElement(node_dict['basemodel'], 'male_basemodel_height')

    node_dict['basemodel'].append(etree.Comment('Female basemodel path (.osim)'))
    node_dict['female_basemodel_path'] = etree.SubElement(node_dict['basemodel'], 'female_basemodel_path')
    node_dict['basemodel'].append(etree.Comment('Female basemodel generic height in m'))
    node_dict['female_basemodel_height'] = etree.SubElement(node_dict['basemodel'], 'female_basemodel_height')

    node_dict['basemodel'].append(etree.Comment('CCC basemodel path (.osim)'))
    node_dict['ccc_basemodel_path'] = etree.SubElement(node_dict['basemodel'], 'ccc_basemodel_path')

    node_dict['marker_set'] = etree.SubElement(node_dict['model_creation_base'], 'marker_set')

    node_dict['marker_set'].append(etree.Comment('Male marker set file path (.xml)'))
    node_dict['male_marker_set_path'] = etree.SubElement(node_dict['marker_set'], 'male_marker_set_path')
    node_dict['marker_set'].append(etree.Comment('Female marker set path (.xml)'))
    node_dict['female_marker_set_path'] = etree.SubElement(node_dict['marker_set'], 'female_marker_set_path')


    node_dict['scale_setup'] = etree.SubElement(node_dict['model_creation_base'], 'scale_setup')

    node_dict['scale_setup'].append(etree.Comment('Scale tool setup file path (.xml) Use ScaleTool.xml if has motion data'))
    node_dict['scale_setup_path'] = etree.SubElement(node_dict['scale_setup'], 'scale_setup_path')

    global variables
    for display, variable, vtype,pattern in variables:
        node_dict[variable].text = entries[variable].get()

    output_file_name = os.path.join(entries['output_path'].get(),'model_creation_base_setup.xml')
    with open(output_file_name, 'wb') as file:
        file.write(etree.tostring(root, pretty_print=True))
        print(f'Printed to {output_file_name}')
        tk.messagebox.showinfo('Success',f'Printed to {output_file_name}')


entries = {}
variables_marker = [
    ('Male BaseModel Path'                      ,'male_basemodel_path'      , 'File'        ,r'base\model\BaseModel_Male_no_marker.osim'),
    ('Male BaseModel Height'                    ,'male_basemodel_height'    , 'Entry'       ,'1.75'),
    ('Female BaseModel Path'                    ,'female_basemodel_path'    , 'File'        ,r'base\model\BaseModel_Female_no_marker.osim'),
    ('Female BaseModel Height'                  ,'female_basemodel_height'  , 'Entry'       ,'1.63'),
    ('CCC BaseModel Path'                       ,'ccc_basemodel_path'       , 'File'        ,r'base\model\BaseFullbody_6DOF.osim'),
    ('Male Marker Set Path'                     ,'male_marker_set_path'     , 'File'        ,r'base\model\markers_Male_VLStudy.xml'),
    ('Female Marker Set Path'                   ,'female_marker_set_path'   , 'File'        ,r'base\model\markers_Female_VLStudy.xml'),
    ('Scale Setup Path'                         ,'scale_setup_path'         , 'File'        ,r'base\setup\ScaleTool.xml'),
]
variables_no_marker = [
    ('Male BaseModel Path'                      ,'male_basemodel_path'      , 'File'        ,r'base\model\MaleFullBodyModel_v2.0_OS4_no_marker.osim'),
    ('Male BaseModel Height'                    ,'male_basemodel_height'    , 'Entry'       ,'1.75'),
    ('Female BaseModel Path'                    ,'female_basemodel_path'    , 'File'        ,r'base\model\FemaleFullBodyModel_v2.0_OS4_no_marker.osim'),
    ('Female BaseModel Height'                  ,'female_basemodel_height'  , 'Entry'       ,'1.63'),
    ('CCC BaseModel Path'                       ,'ccc_basemodel_path'       , 'File'        ,r'base\model\BaseFullbody_6DOF.osim'),
    ('Male Marker Set Path'                     ,'male_marker_set_path'     , 'File'        ,r'base\model\markers_Male_VLStudy.xml'),
    ('Female Marker Set Path'                   ,'female_marker_set_path'   , 'File'        ,r'base\model\markers_Female_VLStudy.xml'),
    ('Scale Setup Path'                         ,'scale_setup_path'         , 'File'        ,r'base\setup\scaleTool_Setup_KBedit.xml'),
]
variables = variables_no_marker

root = tk.Tk()
root.title('Step1 - Model Creation Setup File Generator')

label1 = tk.Label(root, text='Global Settings',font='Arial 14 bold')
label1.pack(pady=10)


entries['work_directory'] = add_input_node(root,'Work Directory','Directory','') 


frame = tk.Frame(root, pady=5)
frame.pack(expand=True, anchor='center')
# Create two Radiobuttons
selected_var = tk.StringVar(value=0)
radio1 = tk.Radiobutton(frame, text='No Marker Data (Default)', variable=selected_var, value=0,command = on_radio_change)
radio2 = tk.Radiobutton(frame, text='Marker Data Available', variable=selected_var, value=1,command = on_radio_change)
radio1.grid(row=0,column=0, padx=10)
radio2.grid(row=0,column=1, padx=10)


label2 = tk.Label(root, text='Base Files',font='Arial 14 bold')
label2.pack(pady=10)

for display, variable, vtype,pattern in variables:
    entries[variable] = add_input_node(root,display,vtype,pattern)

label3 = tk.Label(root, text='Output Directory',font='Arial 14 bold')
label3.pack(pady=10)

entries['output_path'] = add_input_node(root,'Model Creation Setup Output', 'Directory' ,r'base\setup')

btn_submit = tk.Button(root, text='Save Setup File', command=print_setup)
btn_submit.pack(pady=20)

root.mainloop()
