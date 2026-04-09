import tkinter as tk
from tkinter import filedialog, simpledialog
from lxml import etree
import glob
import os

def select_directory(entry):
    directory = filedialog.askdirectory()
    entry.delete(0, tk.END)
    entry.insert(0, directory)
    if entry == entries['work_directory']:
        full_pattern = os.path.join(directory, r'base\setup')
        files = glob.glob(full_pattern)
        if files:
            entries['output_path'].delete(0, tk.END)
            entries['output_path'].insert(0, files[0]) # Consider the first detected basemodel

def select_file(entry):
    filepath = filedialog.askopenfilename()
    entry.delete(0, tk.END)
    entry.insert(0, filepath)

def select_files(entry):
    filepath = filedialog.askopenfilename()
    entry.insert(tk.END, filepath+' ')
def select_files_clear(entry):
    entry.delete(0, tk.END)


variables = [
    ('Trial Name'               ,'trial_name'               , 'Entry' ,''),
    ('Analysis Basemodel Path'  ,'analysis_basemodel_path'  , 'File'  ,r'base\model\BaseFullbody_3DOF.osim'),
    ('External Force Path'      ,'external_force_path'      , 'File'  ,r'base\motion\Motion1181\NMB_ExternalForce1181.mot'),
    ('Motion Path'              ,'motion_path'              , 'File'  ,r'base\motion\Motion1181\NMB_Motion1181.mot'),
    ('External Force Setup Path','external_force_setup_path', 'File'  ,r'base\setup\extForces_Setup.xml'),
    ('JRA Setup Path'           ,'JRA_setup_path'           , 'File'  ,r'base\setup\jointReact_Setup.xml'),
    ('SO Setup Path'            ,'SO_setup_path'            , 'File'  ,r'base\setup\staticOpt_Setup.xml'),
    ('Actuator Path List'       ,'actuator_path_list'       , 'Files' ,r'base\setup\actuator\Actuators_Supine.xml'),
]
setup_variables = [ 'trial_name'               ,
                    'analysis_basemodel_path'  ,
                    'external_force_path'      ,
                    'motion_path'              ,
                    'external_force_setup_path',
                    'JRA_setup_path'           ,
                    'SO_setup_path'            ,
                    'actuator_path_list'       ]

trial_dict_list = []
entries = {}


def populate_display():
    for widget in display_frame.winfo_children():
        widget.destroy()

    trials = root_node.xpath('analysis_setup/analysis_trial')
    for trial in trials:
        frame = tk.Frame(display_frame)
        frame.pack(fill="x", pady=5)
        
        trial_name = trial.xpath('trial_name')[0].text
        tk.Label(frame, text=f"Trial Name: {trial_name}").pack(side="left")
        
        tk.Button(frame, text="Edit", command=lambda t=trial: edit_trial_node(t)).pack(side="right", padx=5)
        tk.Button(frame, text="Delete", command=lambda t=trial: delete_trial_node(t)).pack(side="right")

def submit_trial_path(r):
    # Create the root element
    actuator_path_list = entries['actuator_path_list'       ].get().split(' ')
    actuator_path_list = [s for s in actuator_path_list if s != '']
    add_trial(  analysis_setup_node,
                entries['trial_name'               ].get(),
                entries['analysis_basemodel_path'  ].get(),
                entries['external_force_path'      ].get(),
                entries['motion_path'              ].get(),
                entries['external_force_setup_path'].get(),
                entries['JRA_setup_path'           ].get(),
                entries['SO_setup_path'            ].get(),
                actuator_path_list)
    populate_display()
    r.destroy()


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

def auto_detect_path(directory):
    # Modify this pattern if necessary
    for display,variable, vtype,pattern in variables:
        if (vtype in ('Directory','File')) and (pattern != '') :
            full_pattern = os.path.join(directory, pattern)
            files = glob.glob(full_pattern)
            if files:
                entries[variable].delete(0, tk.END)
                entries[variable].insert(0, files[0]) # Consider the first detected basemodel
        elif (vtype in ('Files')) and (pattern != ''):
            entries[variable].delete(0, tk.END)
            file_list = pattern.split(' ')
            file_list = [s for s in file_list if s != '']
            for file in file_list:
                full_pattern = os.path.join(directory, file)
                files = glob.glob(full_pattern)
                if files:
                    entries[variable].insert(tk.END, files[0]+' ') # Consider the first detected basemodel


def load_trial_path(trial_node):
    # Modify this pattern if necessary
    trial_dict = {}
    trial_dict['trial_name'] = trial_node.xpath('.//trial_name')[0].text
    trial_dict['analysis_basemodel_path'] = trial_node.xpath('.//analysis_basemodel_path')[0].text
    trial_dict['external_force_path'] = trial_node.xpath('.//external_force_path')[0].text
    trial_dict['motion_path'] = trial_node.xpath('.//motion_path')[0].text
    trial_dict['external_force_setup_path'] = trial_node.xpath('.//external_force_setup_path')[0].text
    trial_dict['JRA_setup_path'] = trial_node.xpath('.//JRA_setup_path')[0].text
    trial_dict['SO_setup_path'] = trial_node.xpath('.//SO_setup_path')[0].text
    actuator_list_str = ''
    for actuator_node in trial_node.xpath('.//actuator_path'):
        actuator_list_str += actuator_node.text + ' '    
    trial_dict['actuator_path_list'] = actuator_list_str

    for display,variable, vtype,pattern in variables:
        entries[variable].delete(0, tk.END)
        entries[variable].insert(0, trial_dict[variable])

def add_trial_node():
    win = tk.Toplevel()
    win.title('Path and Value Selector')
    for display, variable, vtype,pattern in variables:
        entries[variable] = add_input_node(win,display,vtype,pattern)

    work_directory = entries['work_directory'].get()
    if work_directory != '':
        auto_detect_path(work_directory)

    btn_submit = tk.Button(win, text='Submit', command=lambda r=win: submit_trial_path(r))
    btn_submit.pack(pady=20)
    

def edit_trial_node(trial_node):
    add_trial_node()
    load_trial_path(trial_node)
    root_node.xpath('analysis_setup')[0].remove(trial_node)
    

def delete_trial_node(trial_node):
    root_node.xpath('analysis_setup')[0].remove(trial_node)
    populate_display()

def add_trial(analysis_setup_node,trial_name,analysis_basemodel_path,external_force_path,motion_path,external_force_setup_path,JRA_setup_path, SO_setup_path, actuator_path_list):
    trial_node = etree.SubElement(analysis_setup_node, 'analysis_trial')
    
    trial_node.append(etree.Comment('Trial Name'))
    trial_name_node = etree.SubElement(trial_node, 'trial_name')
    trial_name_node.text = trial_name

    trial_node.append(etree.Comment('Static Optimization & Joint Reaction Analysis basemodel(.osim)'))
    analysis_basemodel_path_node = etree.SubElement(trial_node, 'analysis_basemodel_path')
    analysis_basemodel_path_node.text = analysis_basemodel_path

    trial_node.append(etree.Comment('External Force (.mot/.sto)'))
    external_force_path_node = etree.SubElement(trial_node, 'external_force_path')
    external_force_path_node.text = external_force_path
    
    trial_node.append(etree.Comment('Motion Data (.mot/.sto)'))
    motion_path_node = etree.SubElement(trial_node, 'motion_path')
    motion_path_node.text = motion_path


    trial_node.append(etree.Comment('Setup Files'))
    trial_setup_node = etree.SubElement(trial_node, 'trial_setup')

    trial_setup_node.append(etree.Comment('Static Optimization Setup (.xml)'))
    external_force_setup_path_node = etree.SubElement(trial_setup_node, 'external_force_setup_path')
    external_force_setup_path_node.text = external_force_setup_path

    trial_setup_node.append(etree.Comment('Static Optimization Setup (.xml)'))
    SO_setup_path_node = etree.SubElement(trial_setup_node, 'SO_setup_path')
    SO_setup_path_node.text = SO_setup_path

    trial_setup_node.append(etree.Comment('Joint Reaction Analysis Setup (.xml)'))
    JRA_setup_path_node = etree.SubElement(trial_setup_node, 'JRA_setup_path')
    JRA_setup_path_node.text = JRA_setup_path

    trial_setup_node.append(etree.Comment('Actuator setup file path (.xml)'))
    actuator_path_list_node = etree.SubElement(trial_setup_node, 'actuator_path_list')
    for actuator_path in actuator_path_list:
        actuator_path_node = etree.SubElement(actuator_path_list_node, 'actuator_path')
        actuator_path_node.text = actuator_path

def save_setup_file():
    output_file_name = os.path.join(entries['output_path'].get(),'analysis_setup.xml')
    with open(output_file_name, 'wb') as file:
        file.write(etree.tostring(root_node, pretty_print=True))
        print(f'Printed to {output_file_name}')
        tk.messagebox.showinfo('Success',f'Printed to {output_file_name}')



root = tk.Tk()
root.title('Step2 - Analysis Setup File Generator')

root_node = etree.Element('root')
analysis_setup_node = etree.SubElement(root_node, 'analysis_setup')

label1 = tk.Label(root, text='Global Settings',font='Arial 14 bold')
label1.pack(pady=10)
entries['work_directory'] = add_input_node(root,'Work Directory','Directory','')

label2 = tk.Label(root, text='Trials',font='Arial 14 bold')
label2.pack(pady=10)

display_frame = tk.Frame(root)
display_frame.pack(pady=20)
populate_display()

add_frame = tk.Frame(root)
add_frame.pack(pady=20)
tk.Label(add_frame, text="Add New Analysis Trial").pack()
tk.Button(add_frame, text="Add", command=add_trial_node).pack()


label3 = tk.Label(root, text='Output Directory',font='Arial 14 bold')
label3.pack(pady=10)

entries['output_path'] = add_input_node(root,'Output Directory','Directory',r'base\setup')

tk.Button(root, text="Save Setup File", command=save_setup_file).pack(pady=20)

root.mainloop()
