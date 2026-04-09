# %%
import opensim as osim
import numpy as np
from lxml import etree
import csv
import os
from multiprocessing import Pool
import argparse

# %%

def get_analysis_setup_info(analysis_setup_path):
    """
    Parses an XML file to extract analysis setup information for SO & JRA trials.

    :param analysis_setup_path: Path to the ana;ysis setup XML file.
    :type analysis_setup_path: str

    :return: A list of dictionaries, where each dictionary contains setup information for a trial.
    :rtype: list of dict

    Each dictionary in the returned list contains the following keys:
    - 'trial_name': Name of the trial.
    - 'analysis_basemodel_path': Path to the baseline OpenSim model file for the trial.
    - 'external_force_path': Path to the external force file for the trial.
    - 'motion_path': Path to the motion file for the trial.
    - 'external_force_setup_path': Path to the external force setup file for the trial.
    - 'JRA_setup_path': Path to the Joint Reaction Analysis setup file for the trial.
    - 'SO_setup_path': Path to the Static Optimization setup file for the trial.
    - 'actuator_path_list': List of paths to actuator files for the trial.
    """
    tree = etree.parse(analysis_setup_path)
    trial_list = []
    trial_node_list = tree.xpath('.//analysis_trial')
    for trial_node in trial_node_list:
        trial = {}
        trial['trial_name'] = trial_node.xpath('.//trial_name')[0].text
        trial['analysis_basemodel_path'] = trial_node.xpath('.//analysis_basemodel_path')[0].text
        trial['external_force_path'] = trial_node.xpath('.//external_force_path')[0].text
        trial['motion_path'] = trial_node.xpath('.//motion_path')[0].text
        trial['external_force_setup_path'] = trial_node.xpath('.//external_force_setup_path')[0].text
        trial['JRA_setup_path'] = trial_node.xpath('.//JRA_setup_path')[0].text
        trial['SO_setup_path'] = trial_node.xpath('.//SO_setup_path')[0].text
        trial['actuator_path_list'] = [actuator_node.text for actuator_node in trial_node.xpath('.//actuator_path')]
        trial_list.append(trial)
    
    return trial_list

def create_folder(folder_path_list):
    """
    Creates folders for the provided list of paths if they don't exist.

    :param folder_path_list: List of folder paths to be created.
    :type folder_path_list: list of str
    """
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
    patient_setup_info['output_spine_loading_path'] = tree.xpath('.//output_spine_loading_path')[0].text

    return patient_setup_info

# %% [markdown]
# # ExtForce_modGRFile

# %%
def ExtForce_modGRFile(SetupFileGeneric, GRFfilename,output_setups_path):
    """
    Modifies a generic External Force setup file to assign the appropriate GRFfilename.mot file for a trial.

    :param SetupFileGeneric: Path to the generic External Force setup file.
    :type SetupFileGeneric: str

    :param GRFfilename: Name of the GRF (Ground Reaction Force) file for the trial.
    :type GRFfilename: str

    :param output_setups_path: Path to the directory where the modified setup file will be saved.
    :type output_setups_path: str

    :return: Path to the modified External Force setup file.
    :rtype: str

    """

# takes generic External Force file (where I already assigned correct plates to correct bodies and assigns approriate GRFfilename.mot file for trial
# unsure how to do via API, and not totally necessary
    tree = etree.parse(SetupFileGeneric)
    root = tree.getroot()
    for i in root.iter('data_source_name'):
        i.text = GRFfilename
    for i in root.iter('datafile'):
        i.text = GRFfilename
    ExternalForce_File_name = os.path.basename(GRFfilename).split('.')[0] + '_EFsetup.xml'
    ExternalForce_File = os.path.join(output_setups_path,ExternalForce_File_name) 
    tree.write(ExternalForce_File,pretty_print=True,xml_declaration=True,encoding='utf-8')
    return ExternalForce_File

# %% [markdown]
# # Static Optimization

# %%
def SOsubfunc(SO_XML, OSmodel):
    """
    Executes the Static Optimization (SOpt) analysis using the provided setup XML.

    :param SO_XML: Path to the Static Optimization setup XML file.
    :type SO_XML: str

    :param OSmodel: Path to the OpenSim model file.
    :type OSmodel: str
    """
    model = osim.Model(OSmodel)
    model.initSystem()
    analyzeTool = osim.AnalyzeTool(SO_XML)
    print(SO_XML)
    analyzeTool.run()

def set_analysis_setup_basemodel_path(trial_name,analysis_setup_path,analysis_basemodel_path,output_setups_path):
    """
    Modifies the analysis setup file to set the analysis base model path.

    :param trial_name: Name of the trial for which the base model path is being set.
    :type trial_name: str

    :param analysis_setup_path: Path to the original analysis setup file.
    :type analysis_setup_path: str

    :param analysis_basemodel_path: Path to the base model file for the trial.
    :type analysis_basemodel_path: str

    :param output_setups_path: Path to the directory where the modified setup file will be saved.
    :type output_setups_path: str

    :return: Path to the modified analysis setup file.
    :rtype: str

    """
    setup_name = os.path.basename(analysis_setup_path).split('.')[0]
    tree = etree.parse(analysis_setup_path)
    root = tree.getroot()

    root.xpath('//model_file')[0].text = analysis_basemodel_path
    new_setup_file_path = os.path.join(output_setups_path,setup_name + '_' + trial_name + '.xml')
    with open(new_setup_file_path, 'wb') as file:
        file.write(etree.tostring(root, pretty_print=True))
        print(f'{patient_ID} Printed to {new_setup_file_path}')

    return new_setup_file_path
    
# %%
def SOpt_Analysis(trial_name,SOpt_setup,analysis_basemodel_path, scaled_model_path, IKmotion, external_force_path, actuator_path_list, Times,result_path,output_setups_path):
    """
    Performs Static Optimization (SOpt) analysis on a given trial.

    :param trial_name: Name of the trial for which the SOpt analysis is being performed.
    :type trial_name: str

    :param SOpt_setup: Path to the original SOpt setup file.
    :type SOpt_setup: str

    :param analysis_basemodel_path: Path to the analysis base model file for the trial.
    :type analysis_basemodel_path: str

    :param scaled_model_path: Path to the scaled model file.
    :type scaled_model_path: str

    :param IKmotion: Path to the Inverse Kinematics motion file.
    :type IKmotion: str

    :param external_force_path: Path to the external force file.
    :type external_force_path: str

    :param actuator_path_list: List of paths to actuator files.
    :type actuator_path_list: list

    :param Times: List containing the start and end times for the analysis. If None, the times are derived from the IK motion file.
    :type Times: list or None

    :param result_path: Path to the directory where the analysis results will be saved.
    :type result_path: str

    :param output_setups_path: Path to the directory where the modified setup files will be saved.
    :type output_setups_path: str
    """
    motion_name = os.path.basename(IKmotion).split('.')[0]
    
    model = osim.Model(scaled_model_path)
    model.initSystem()

    new_SOpt_setup = set_analysis_setup_basemodel_path(trial_name,SOpt_setup,analysis_basemodel_path,output_setups_path)
    statop = osim.AnalyzeTool(new_SOpt_setup) #this is a generic project specific Setup File contains SOpt finding specifics and intervals (can add to this if you want)
    statop.setName(motion_name) ##change Tool name names files with this
    x=statop.getPropertyByIndex(0)
    osim.PropertyHelper.setValueString(scaled_model_path, x)
        
    statop.setModel(model) #set model
    statop.setCoordinatesFileName(IKmotion) #set IK file    
    #SO.setStepInterval(####)  %set step interval (how many frames to skip) put this in the setup

    #set Reserve Actuator (if you want) 
    if actuator_path_list != None:
        RA = osim.ArrayStr()
        if type(actuator_path_list) == list:
            for path in actuator_path_list:
                RA.append(path)
        else: #instance where only 1 path and not listed in a cell array
            RA.append(actuator_path_list)
        statop.setForceSetFiles(RA)

    #set External Force file (if you want)
    if external_force_path != None:
        ExtLoads = osim.ExternalLoads(external_force_path,True)
        ExtLoads.setDataFileName(external_force_path)
        statop.setExternalLoadsFileName(external_force_path)

        
    statop.setResultsDir(result_path)  #path saving things at

    analysis = statop.getAnalysisSet().get(0)
    SO = osim.StaticOptimization.safeDownCast(analysis)
    SO.setModel(model)

    #set times to analyze        
    if Times == None:

        motCoordsData = osim.Storage(IKmotion)
        initial_time = motCoordsData.getFirstTime()
        final_time = motCoordsData.getLastTime()
        Times = [initial_time, final_time]

    statop.setInitialTime(Times[0])  # worth adding 'Times'?
    statop.setFinalTime(Times[1])
    SO.setStartTime(Times[0])
    SO.setEndTime(Times[1])

    SO_XML = os.path.join(output_setups_path,'SO_Setup_'+motion_name+'.xml') #saves setupfile
    print('**** Running SOpt on ' +motion_name +' ****')
    statop.printToXML(SO_XML)
    SOsubfunc(SO_XML, scaled_model_path)  #needs this to run propertly (trust me)

# %% [markdown]
# # Joint Reaction Analysis

# %%
def JRAsubfunction(JRA_XML):
    """
    Executes the Joint Reaction Analysis (JRA) using the provided XML setup.

    :param JRA_XML: Path to the JRA XML setup file.
    :type JRA_XML: str
    """
    print('**** Running JRA ****')
    JRArun = osim.AnalyzeTool(JRA_XML)
    JRArun.run()

# %%
def JRA_Analysis(trial_name,JRA_setup,analysis_basemodel_path, scaled_model_path, IKmotion, external_force_path, actuator_path_list, SO_forces_path, Times,result_path,output_setups_path):
    """
    Executes the Joint Reaction Analysis (JRA) using the provided setup and model.

    :param trial_name: Name of the trial.
    :type trial_name: str

    :param JRA_setup: Path to the JRA setup file.
    :type JRA_setup: str

    :param analysis_basemodel_path: Path to the analysis base model.
    :type analysis_basemodel_path: str

    :param scaled_model_path: Path to the scaled OpenSim model file.
    :type scaled_model_path: str

    :param IKmotion: Path to the Inverse Kinematics motion file.
    :type IKmotion: str

    :param external_force_path: Path to the external force file.
    :type external_force_path: str

    :param actuator_path_list: List of paths to actuator files.
    :type actuator_path_list: list

    :param SO_forces_path: Path to the Static Optimization forces file.
    :type SO_forces_path: str

    :param Times: List containing the initial and final times for analysis.
    :type Times: list

    :param result_path: Path to the directory where the results will be saved.
    :type result_path: str

    :param output_setups_path: Path to the directory where the setup files will be saved.
    :type output_setups_path: str
    """
    motion_name = os.path.basename(IKmotion).split('.')[0]
    model = osim.Model(scaled_model_path)
    model.initSystem()


    new_JRA_setup = set_analysis_setup_basemodel_path(trial_name,JRA_setup,analysis_basemodel_path,output_setups_path)
    jointReact = osim.AnalyzeTool(new_JRA_setup) #this is a generic project specific Setup File
    jointReact.setName(motion_name)  #Change name so files named correctly
    x=jointReact.getPropertyByIndex(0)
    osim.PropertyHelper.setValueString(scaled_model_path, x)

    jointReact.setModel(model)
    jointReact.setCoordinatesFileName(IKmotion)
    jointReact.setModelFilename(scaled_model_path)

    #set Reserve Actuator (if you want) 
    if actuator_path_list != None:
        RA = osim.ArrayStr()
        if type(actuator_path_list) == list:
            for path in actuator_path_list:
                RA.append(path)
        else: #instance where only 1 path and not listed in a cell array
            RA.append(actuator_path_list)
        jointReact.setForceSetFiles(RA) 

    #set External Force file (if you want)    
    if external_force_path != None:
        jointReact.setExternalLoadsFileName(external_force_path)
    
    #set times to analyze     
    if Times == None:
        motCoordsData = osim.Storage(IKmotion)
        initial_time = motCoordsData.getFirstTime()
        final_time = motCoordsData.getLastTime()
        Times = [initial_time, final_time]
    
    jointReact.setInitialTime(Times[0]) #worth adding?
    jointReact.setFinalTime(Times[1])    

    for a in range(jointReact.getAnalysisSet().getSize()):  #prob a lot better way to do, but this works for now                    
        analysis = jointReact.getAnalysisSet().get(a)
        if  analysis.getConcreteClassName() == 'ForceReporter':
            SetUp = osim.ForceReporter.safeDownCast(analysis)
        else:
            SetUp = osim.JointReaction.safeDownCast(analysis)                           
            SetUp.setForcesFileName(SO_forces_path)
        SetUp.setModel(model)
        SetUp.setStartTime(Times[0])
        SetUp.setEndTime(Times[1])    

    jointReact.setResultsDir(result_path)
    JRA_XML = os.path.join(output_setups_path, 'JRA_Setup_' +  motion_name + '.xml')
    jointReact.printToXML(JRA_XML)             

    JRAsubfunction(JRA_XML)

def read_motionFile(fname):
    """
    Purpose:  This function reads a file in the format of a SIMM motion file
              and returns a data structure
    Input:    fname is the name of the ascii datafile to be read 
              ('character array') 
    Output:   q returns a dictionary with the following format:
                q['labels'] 	= numpy array of column labels
                q['data'] 		= numpy array of data
                q['nr'] 		= number of matrix rows
                q['nc'] 		= number of matrix columns
    """
    q = {'nr': 0, 'nc': 0}
    
    with open(fname, 'r') as f:
        lines = f.readlines()

    i = 0
    while 'endheader' not in lines[i].lower():
        if 'datacolumns' in lines[i].lower():
            q['nc'] = int(lines[i].split()[1])
        elif 'datarows' in lines[i].lower():
            q['nr'] = int(lines[i].split()[1])
        elif 'ncolumns' in lines[i].lower():
            q['nc'] = int(lines[i].split('=')[1])
        elif 'nrows' in lines[i].lower():
            q['nr'] = int(lines[i].split('=')[1])
        i += 1

    q['labels'] = np.array(lines[i+1].split())
    data = []
    for line in lines[i+2:i+2+q['nr']]:
        data.append(list(map(float, line.split())))
    q['data'] = np.array(data)
    return q

def Get_VertLoad_FullBody(result_path,motion_name):
    """
    Calculate the vertebral loads (compression and shear forces) for the full body from the Joint Reaction Analysis results.

    :param result_path: Path to the directory containing the analysis results.
    :type result_path: str
    :param motion_name: Name of the motion file without the file extension.
    :type motion_name: str

    :return: 
        - VertComp (numpy.ndarray): Vertebral compression forces.
        - VertAPShear (numpy.ndarray): Anterior-posterior shear forces.
        - VertMLShear (numpy.ndarray): Medial-lateral shear forces.
        - HeadersF (list): List of vertebral segment names.

    """
    child_HeadersF  = ['L5_S1_IVDjnt_on_lumbar5_in_lumbar5', 'L4_L5_IVDjnt_on_lumbar4_in_lumbar4', 'L3_L4_IVDjnt_on_lumbar3_in_lumbar3', 'L2_L3_IVDjnt_on_lumbar2_in_lumbar2', 'L1_L2_IVDjnt_on_lumbar1_in_lumbar1',  'T12_L1_IVDjnt_on_thoracic12_in_thoracic12',  'T11_T12_IVDjnt_on_thoracic11_in_thoracic11', 'T10_T11_IVDjnt_on_thoracic10_in_thoracic10', 'T9_T10_IVDjnt_on_thoracic9_in_thoracic9', 'T8_T9_IVDjnt_on_thoracic8_in_thoracic8', 'T7_T8_IVDjnt_on_thoracic7_in_thoracic7', 'T6_T7_IVDjnt_on_thoracic6_in_thoracic6', 'T5_T6_IVDjnt_on_thoracic5_in_thoracic5', 'T4_T5_IVDjnt_on_thoracic4_in_thoracic4', 'T3_T4_IVDjnt_on_thoracic3_in_thoracic3', 'T2_T3_IVDjnt_on_thoracic2_in_thoracic2', 'T1_T2_IVDjnt_on_thoracic1_in_thoracic1']
    parent_HeadersF = ['L4_L5_IVDjnt_on_lumbar5_in_lumbar5', 'L3_L4_IVDjnt_on_lumbar4_in_lumbar4', 'L2_L3_IVDjnt_on_lumbar3_in_lumbar3', 'L1_L2_IVDjnt_on_lumbar2_in_lumbar2', 'T12_L1_IVDjnt_on_lumbar1_in_lumbar1', 'T11_T12_IVDjnt_on_thoracic12_in_thoracic12', 'T10_T11_IVDjnt_on_thoracic11_in_thoracic11', 'T9_T10_IVDjnt_on_thoracic10_in_thoracic10',  'T8_T9_IVDjnt_on_thoracic9_in_thoracic9',  'T7_T8_IVDjnt_on_thoracic8_in_thoracic8', 'T6_T7_IVDjnt_on_thoracic7_in_thoracic7', 'T5_T6_IVDjnt_on_thoracic6_in_thoracic6', 'T4_T5_IVDjnt_on_thoracic5_in_thoracic5', 'T3_T4_IVDjnt_on_thoracic4_in_thoracic4', 'T2_T3_IVDjnt_on_thoracic3_in_thoracic3', 'T1_T2_IVDjnt_on_thoracic2_in_thoracic2', 'T1_head_neck_on_thoracic1_in_thoracic1']
    HeadersF = ['Lumbar5', 'Lumbar4', 'Lumbar3', 'Lumbar2', 'Lumbar1', 'Thoracic12', 'Thoracic11', 'Thoracic10', 'Thoracic9', 'Thoracic8', 'Thoracic7', 'Thoracic6', 'Thoracic5', 'Thoracic4', 'Thoracic3', 'Thoracic2', 'Thoracic1']
    
    childReact = read_motionFile(os.path.join(result_path,motion_name) + '_JointReaction_child_ReactionLoads.sto')
    parentReact = read_motionFile(os.path.join(result_path,motion_name) + '_JointReaction_parent_ReactionLoads.sto')

    child_HeadersFnums = np.zeros(len(child_HeadersF)).astype(int)
    parent_HeadersFnums = np.zeros(len(parent_HeadersF)).astype(int)

    for h in range(len(child_HeadersFnums)):
        childReact_label = child_HeadersF[h] + '_fx'
        child_HeadersFnums[h] = np.where(childReact['labels']==childReact_label)[0][0]

        parentReact_label = parent_HeadersF[h] + '_fx'
        parent_HeadersFnums[h] = np.where(parentReact['labels']==parentReact_label)[0][0]

    # Compression  
    child_Comp = childReact['data'][:, child_HeadersFnums+1]
    parent_Comp = parentReact['data'][:, parent_HeadersFnums+1]
    VertComp = (child_Comp - parent_Comp) / 2

    # AP Shear
    child_APShear = childReact['data'][:, child_HeadersFnums]
    parent_APShear = parentReact['data'][:, parent_HeadersFnums]
    VertAPShear = (parent_APShear - child_APShear) / 2

    # Medial-lateral Shear
    child_MLShear = childReact['data'][:, child_HeadersFnums+2]
    parent_MLShear = parentReact['data'][:, parent_HeadersFnums+2]
    VertMLShear = (parent_MLShear - child_MLShear) / 2

    return VertComp, VertAPShear, VertMLShear, HeadersF


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('base_setup',type=str,help='Analysis base setup file path')
    parser.add_argument('patient_setup',type=str,help='Patient setup file path')
    args = parser.parse_args()

    analysis_setup_path = args.base_setup
    patient_setup_path = args.patient_setup

    trial_list = get_analysis_setup_info(analysis_setup_path)

    patient_analysis_setup = get_patient_setup_info(patient_setup_path)
    patient_directory_path = patient_analysis_setup['patient_directory_path']
    patient_ID = patient_analysis_setup['patient_ID']
    output_setups_path = patient_analysis_setup['output_setups_path']
    output_spine_loading_path = patient_analysis_setup['output_spine_loading_path']
    scaled_model_path = patient_analysis_setup['scaled_model_path']

    print(patient_ID)

    #Loop trough trials in patient setup file
    for trial_no in range(len(trial_list)):
        trial_setup = trial_list[trial_no]
        trial_name = trial_setup['trial_name']
        analysis_basemodel_path = trial_setup['analysis_basemodel_path']
        motion_path = trial_setup['motion_path']
        external_force_path = trial_setup['external_force_path']
        external_force_setup_path = trial_setup['external_force_setup_path']
        SO_setup_path = trial_setup['SO_setup_path']
        JRA_setup_path = trial_setup['JRA_setup_path']
        actuator_path_list = trial_setup['actuator_path_list']
        # motion_path = motiondir + 'NMB_Motion' + str(j) + '.mot'# motions from WriteMotData_NMB.m or WriteMotData_PushDoor_KB.m
        # external_force_path = extforcedir + 'NMB_ExternalForce' +str(j) + '.mot' # WriteMotData_NMB.m or WriteMotData_PushDoor_KB.m
        # result_path = resultpath + str(ids[i]) + '/' + str(j) + '_Jan2023/'
        # motion_name = 'NMB_Motion' + str(j)
        motion_name = os.path.basename(motion_path).split('.')[0]
        create_folder([output_setups_path,output_spine_loading_path])
        result_path = os.path.join(output_spine_loading_path,trial_name)
        if not os.path.exists(result_path):
            os.makedirs(result_path)
        
        #run SO
        new_extForces=ExtForce_modGRFile(external_force_setup_path,external_force_path,output_setups_path)
        SOpt_Analysis(
                    trial_name,
                    SO_setup_path,
                    analysis_basemodel_path,
                    scaled_model_path,
                    motion_path,
                    new_extForces,
                    actuator_path_list,
                    (0,0),
                    result_path,
                    output_setups_path)

        #run JRA
        SO_forces_path = os.path.join(result_path, motion_name + '_StaticOptimization_force.sto')
        JRA_Analysis(
                    trial_name,
                    JRA_setup_path,
                    analysis_basemodel_path,
                    scaled_model_path, 
                    motion_path, 
                    new_extForces, 
                    actuator_path_list, 
                    SO_forces_path,
                    (0,0),
                    result_path,
                    output_setups_path)

        #calculate vertebra loading
        VertComp, VertAPShear, VertMLShear, HeadersF = Get_VertLoad_FullBody(result_path,motion_name)
        filename = os.path.join(result_path , motion_name + '_VertebralLoad.csv')
        VComp = 'Compressive Load'
        APShear = 'AP Shear'
        MLShear = 'ML Shear'

        #save file
        with open(filename, 'w', newline='') as file:
            writer = csv.writer(file)
            writer.writerow([VComp, APShear, MLShear])  # writing headers
            writer.writerows(zip(VertComp.flatten(), VertAPShear.flatten(), VertMLShear.flatten()))  # writing data
