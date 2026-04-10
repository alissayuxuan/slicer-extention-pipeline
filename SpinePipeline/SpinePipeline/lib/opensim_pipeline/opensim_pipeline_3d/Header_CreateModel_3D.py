import json
import numpy as np
import os
import shutil
import argparse

from utils import get_base_setup_info, create_folder, get_patient_setup_info
from model_operations import Add_Marker, Un_LockCoordinates_OS4, AddDOF_OS4, Change_MTA_Act, ChangeBox_Inertia
from scaling_operations import Scale_Height, ScaleOpenSim
from spine_adjustments import Spine_Curvature_Adj, Spine_JtDist_Adj, getJointAngles_Osim
from muscle_adjustments import Evaluate_Muscle_AllLevels_v3_EOTM_Side, ScaleMuscleMarkerModel, ScaleMuscleProperties


np.seterr(divide='ignore', invalid='ignore')

if __name__ == '__main__':

    print('Running CT & Marker Pipeline...')
    # %%
    ## INPUTS

    
    parser = argparse.ArgumentParser()
    parser.add_argument('base_setup',type=str,help='Model creation base setup file path')
    parser.add_argument('patient_setup',type=str,help='Patient setup file path')
    args = parser.parse_args()
    print(args)

    Session = 1 #session number is always 1 for VLS


    base_setup_path = args.base_setup
    patient_setup_path = args.patient_setup

    #base_setup_path = "C:/Users/tlerchl/data/dataset-vfx_test/derivatives/S04/model_creation_base_setup.xml"
    #patient_setup_path = "C:/Users/tlerchl/data/dataset-vfx_test/derivatives/S04/sub-S04_patient_setup.xml"



    base_setup = get_base_setup_info(base_setup_path)

    male_basemodel_path = base_setup['male_basemodel_path']
    male_marker_set_path = base_setup['male_marker_set_path']
    male_basemodel_height = base_setup['male_basemodel_height']
    female_basemodel_path = base_setup['female_basemodel_path']
    female_marker_set_path = base_setup['female_marker_set_path']
    female_basemodel_height = base_setup['female_basemodel_height']
    ccc_basemodel_path = base_setup['ccc_basemodel_path']
    scale_setup_path = base_setup['scale_setup_path']

    patient_model_creation_setup = get_patient_setup_info(patient_setup_path)
    patient_directory_path = patient_model_creation_setup['patient_directory_path']
    patient_ID = patient_model_creation_setup['patient_ID']
    info_file_path = patient_model_creation_setup['info_file_path']
    calibration_trial_path = patient_model_creation_setup['calibration_trial_path']
    output_model_path = patient_model_creation_setup['output_model_path']
    output_setups_path = patient_model_creation_setup['output_setups_path']
    #output_spine_loading_path = patient_model_creation_setup['output_spine_loading_path']
    scaled_model_path = patient_model_creation_setup['scaled_model_path']

    create_folder([output_model_path,output_setups_path])
    StrSubj = patient_ID
    print(StrSubj)

    # %%
    ## Load subject info file from R drive (contains muscle and CT curvature data)
    with open(info_file_path, 'r') as file:
        info = json.load(file)
    #JointAngles_CT = info['vert_rotations']
    JointDist_CT = info["vert_translations"] 
    VertAxes_CT = info["vert_axes_in_world"]
    JointLocs_CT = info["IVJ_centers_in_world"]
    mass = np.float64(info['Weight'])  #it's mass not weight!!!!!!!
    Height = np.float64(info['Height'])

    muscledataCSA_L = info['muscleCSA_L']
    muscledataCSA_R = info['muscleCSA_R']
    muscledataMAX_L = info['muscleAP_L']
    muscledataMAX_R = info['muscleAP_R']
    muscledataMAZ_L = info['muscleML_L']
    muscledataMAZ_R = info['muscleML_R']

    # %%
    ## Check if use TRC 1 or 2; either Trial 1 or 2        
    TRCfile = calibration_trial_path
    if TRCfile != None :
        if not os.path.isfile(TRCfile):
            TRCfile = None
    if TRCfile == '':
        TRCfile = None

    if TRCfile:
        print('Marker data detected')
    else:
        print('No marker data detected')
    # %%
    ## Get Gender and BaseModel  
    # Select sex of base model
    Sex = info['Sex'][0]
    if Sex == 'M':
        # BaseModel = bModelDirectory + 'BaseModel_Male_no_marker.osim'
        BaseModel = male_basemodel_path
        MarkerSetPath = male_marker_set_path
        GenericHt = male_basemodel_height # use for UppBodyHtFraction;
    else:
        # BaseModel = bModelDirectory + 'BaseModel_Female_no_marker.osim' 
        BaseModel = female_basemodel_path
        MarkerSetPath = female_marker_set_path  
        GenericHt = female_basemodel_height


    # %%
    BaseModel = Add_Marker(BaseModel,MarkerSetPath,output_model_path)

    # %%
    ## Spine curvature (Algorithm, Marker or CT specified)
    #BaseModel stuff is in the 'Create_...' function
    JointAngles_CT = getJointAngles_Osim(VertAxes_CT)
    SpineAdj_Model = Spine_Curvature_Adj(BaseModel, StrSubj, Sex, Height, mass, JointDist_CT, JointAngles_CT, output_model_path,GenericHt)
    New_Model = SpineAdj_Model  #do this so steps can be skipped more easily

    # %%
    ## Lock select joints
    PelvisRots = ['pelvis_tilt','pelvis_list']
    Abs = ['Abs_FE','Abs_LB','Abs_AR']
    Spinejts_L4L5up = ['L4_L5_FE','L4_L5_LB','L4_L5_AR','L3_L4_FE','L3_L4_LB','L3_L4_AR','L2_L3_FE','L2_L3_LB','L2_L3_AR','L1_L2_FE','L1_L2_LB','L1_L2_AR','T12_L1_FE','T12_L1_LB','T12_L1_AR','T11_T12_FE','T11_T12_LB','T11_T12_AR','T10_T11_FE','T10_T11_LB','T10_T11_AR','T9_T10_FE','T9_T10_LB','T9_T10_AR','T8_T9_FE','T8_T9_LB','T8_T9_AR','T7_T8_FE','T7_T8_LB','T7_T8_AR','T6_T7_FE','T6_T7_LB','T6_T7_AR','T5_T6_FE','T5_T6_LB','T5_T6_AR','T4_T5_FE','T4_T5_LB','T4_T5_AR','T3_T4_FE','T3_T4_LB','T3_T4_AR','T2_T3_FE','T2_T3_LB','T2_T3_AR','T1_T2_FE','T1_T2_LB','T1_T2_AR']
    L5S1jt = ['L5_S1_FE','L5_S1_LB','L5_S1_AR']
    #Ribjts = ['T12_r12R_X','T12_r12R_Y','T12_r12R_Z','T11_r11R_X','T11_r11R_Y','T11_r11R_Z','T10_r10R_X','T10_r10R_Y','T10_r10R_Z','T9_r9R_X','T9_r9R_Y','T9_r9R_Z','T8_r8R_X','T8_r8R_Y','T8_r8R_Z','T7_r7R_X','T7_r7R_Y','T7_r7R_Z','T6_r6R_X','T6_r6R_Y','T6_r6R_Z','T5_r5R_X','T5_r5R_Y','T5_r5R_Z','T4_r4R_X','T4_r4R_Y','T4_r4R_Z','T3_r3R_X','T3_r3R_Y','T3_r3R_Z','T2_r2R_X','T2_r2R_Y','T2_r2R_Z','T1_r1R_X','T1_r1R_Y','T1_r1R_Z','T12_r12L_X','T12_r12L_Y','T12_r12L_Z','T11_r11L_X','T11_r11L_Y','T11_r11L_Z','T10_r10L_X','T10_r10L_Y','T10_r10L_Z','T9_r9L_X','T9_r9L_Y','T9_r9L_Z','T8_r8L_X','T8_r8L_Y','T8_r8L_Z','T7_r7L_X','T7_r7L_Y','T7_r7L_Z','T6_r6L_X','T6_r6L_Y','T6_r6L_Z','T5_r5L_X','T5_r5L_Y','T5_r5L_Z','T4_r4L_X','T4_r4L_Y','T4_r4L_Z','T3_r3L_X','T3_r3L_Y','T3_r3L_Z','T2_r2L_X','T2_r2L_Y','T2_r2L_Z','T1_r1L_X','T1_r1L_Y','T1_r1L_Z']
    RibXjts = ['T12_r12R_X','T11_r11R_X','T10_r10R_X','T9_r9R_X','T8_r8R_X','T7_r7R_X','T6_r6R_X','T5_r5R_X','T4_r4R_X','T3_r3R_X','T2_r2R_X','T1_r1R_X',  'T12_r12L_X','T11_r11L_X','T10_r10L_X','T9_r9L_X','T8_r8L_X','T7_r7L_X','T6_r6L_X','T5_r5L_X','T4_r4L_X','T3_r3L_X','T2_r2L_X','T1_r1L_X',]
    SternumRots = ['SternumRotZ','SternumRotX','SternumRotY']
    HeadNeck = ['T1_head_neck_LB',	'T1_head_neck_AR']

    AlwaysLock =    Abs + Spinejts_L4L5up + RibXjts + SternumRots
    AddLock =       PelvisRots + HeadNeck + L5S1jt  #leave [] if don't want any, rename line 60!!
    U_LCoors =      AlwaysLock + AddLock

    AlwaysLock = np.array(AlwaysLock).reshape((-1,1))
    AddLock = np.array(AddLock).reshape((-1,1))
    U_LCoors = np.array(U_LCoors).reshape((-1,1))

    un_or_lock = 'lock'

    # %%
    name = os.path.basename(New_Model).split('.')[0]
    Newmodelname = name + '_jt_' + un_or_lock
    Lock_Model = Un_LockCoordinates_OS4(New_Model, U_LCoors, un_or_lock, Newmodelname)
    New_Model = Lock_Model

    # %%
    ## IVJ distances from images 
    SpineAdj2_Model = Spine_JtDist_Adj(New_Model, StrSubj, Sex, Height, mass, JointDist_CT, output_model_path)
    New_Model = SpineAdj2_Model  #do this so steps can be skipped more easily  

    # %%
    ## Scales by TRC/marker 
    if TRCfile:
        SetupFileGeneric = scale_setup_path
        name = os.path.basename(New_Model).split('.')[0]
        Newmodelname = name + '_Scaled'

        Scale_Model, Ssetup = ScaleOpenSim(New_Model, SetupFileGeneric, TRCfile, mass, Newmodelname,output_setups_path,output_model_path)
        New_Model = Scale_Model
    else:
        New_Model = Scale_Height(New_Model,StrSubj, Sex, Height, mass,scale_setup_path,output_model_path,output_setups_path,GenericHt)
 

    # %%
    ## UNlock joints
    un_or_lock = 'unlock'
    U_LCoors =  Abs+Spinejts_L4L5up+ HeadNeck+ PelvisRots+ L5S1jt+ ['SternumRotZ']  #keep ribs & Sternum rot locked (perhaps modify baseline model to keep locked)
    U_LCoors = np.array(U_LCoors).reshape(-1,1)
    name = os.path.basename(New_Model).split('.')[0]
    Newmodelname = name + '_' + un_or_lock
    Scaled_UnLocked_Model = Un_LockCoordinates_OS4(New_Model, U_LCoors, un_or_lock, Newmodelname) 
    New_Model = Scaled_UnLocked_Model

    # %%

    ## Add CCC (keep model!)
    ModelCCC = ccc_basemodel_path
    newCCCModel = AddDOF_OS4(New_Model, ModelCCC) 

    shutil.copy2(newCCCModel, os.path.join(output_model_path,StrSubj+'_6CCC.osim'))
    # os.remove(newCCCModel)
    #need one here if >1 ccc being created

    # ModelCCC = bModelDirectory + 'BaseFullbody_3DOF.osim'
    # newCCCModel = AddDOF_OS4(New_Model, ModelCCC)
    # shutil.copy2(newCCCModel, patient_directory_path + StrSubj +'_3CCC.osim')  #rename for convenience

    # %%
    ## Scales model by muscle images  (use last model before CCC's added) scale csa by 100, max by 10, maz by 10

        # ## Evaluate Muscle All levels

    
    preCSA_info, preMAX_info, preMAZ_info,preFascicleCSA_info, preFascicleMAX_info, preFascicleMAZ_info,VertCentY, VertCent, JointCent = Evaluate_Muscle_AllLevels_v3_EOTM_Side(New_Model,'left')

    base_muscle_info = {
        "preCSA_info": preCSA_info,
        "preMAX_info": preMAX_info,
        "preMAZ_info": preMAZ_info,
        "preFascicleCSA_info": preFascicleCSA_info,
        "preFascicleMAX_info": preFascicleMAX_info,
        "preFascicleMAZ_info": preFascicleMAZ_info,
        "VertCentY": VertCentY,
        "VertCent": VertCent,
        "JointCent": JointCent
    }

    newMuscleModel_L  = ScaleMuscleMarkerModel(New_Model, StrSubj, muscledataCSA_L, muscledataMAX_L, muscledataMAZ_L,scaled_model_path,"left", base_muscle_info)  #put in cm & cm2; MAX=A/P                

    preCSA_info, preMAX_info, preMAZ_info,preFascicleCSA_info, preFascicleMAX_info, preFascicleMAZ_info,VertCentY, VertCent, JointCent = Evaluate_Muscle_AllLevels_v3_EOTM_Side(New_Model,'right')

    base_muscle_info = {
        "preCSA_info": preCSA_info,
        "preMAX_info": preMAX_info,
        "preMAZ_info": preMAZ_info,
        "preFascicleCSA_info": preFascicleCSA_info,
        "preFascicleMAX_info": preFascicleMAX_info,
        "preFascicleMAZ_info": preFascicleMAZ_info,
        "VertCentY": VertCentY,
        "VertCent": VertCent,
        "JointCent": JointCent    
    }
        
    newMuscleModel = ScaleMuscleMarkerModel(newMuscleModel_L, StrSubj, muscledataCSA_R, muscledataMAX_R, muscledataMAZ_R,scaled_model_path,"right",base_muscle_info)  #put in cm & cm2; MAX=A/P
    #newMuscleModel = ScaleMuscleMarkerModel(newMuscleModel, StrSubj, muscledataCSA_R, muscledataMAX_R, muscledataMAZ_R,scaled_model_path,"right")  #put in cm & cm2; MAX=A/P

    
    New_Model = newMuscleModel
    

    # %%
    ## adjust muscle length parameters based on baselines (needed as we change angles and distances outside of OpenSim Scaling)
        
    newMuscleLModel = ScaleMuscleProperties(New_Model, BaseModel, '_MuscleLengths')       
    New_Model = newMuscleLModel
    
    # %%
    ## change max muscle control (from 1 to 5)
    Change_MTA_Act(New_Model, 5)      #keeps same name 'New_Model'
    
    # %%
    ## unlock stuff for SOpt only (non CCC models)
    RibXjts = ['T12_r12R_X','T11_r11R_X','T10_r10R_X','T9_r9R_X','T8_r8R_X','T7_r7R_X','T6_r6R_X','T5_r5R_X','T4_r4R_X','T3_r3R_X','T2_r2R_X','T1_r1R_X',  'T12_r12L_X','T11_r11L_X','T10_r10L_X','T9_r9L_X','T8_r8L_X','T7_r7L_X','T6_r6L_X','T5_r5L_X','T4_r4L_X','T3_r3L_X','T2_r2L_X','T1_r1L_X']
    SternumRots = ['SternumRotZ','SternumRotX','SternumRotY']
    U_LCoors =  RibXjts + SternumRots   

    RibXjts = np.array(RibXjts).reshape((-1,1))
    SternumRots = np.array(SternumRots).reshape((-1,1))
    U_LCoors = np.array(U_LCoors).reshape((-1,1))

    un_or_lock = 'unlock'

    Newmodelname = 'Temp_unlocked2'
    Scaled_UnLocked_Model2 = Un_LockCoordinates_OS4(New_Model, U_LCoors, un_or_lock, Newmodelname)
    New_Model = Scaled_UnLocked_Model2

    # %%
    ## renaming model; keep this model (keep model!)
    FullyScaledmodel = os.path.join(output_model_path , StrSubj + '_51DoF.osim')
    shutil.copy2(New_Model, FullyScaledmodel) #rename for convenience 

    # %%
    if TRCfile:
        ## Add/Remove Box and 'window' lift Models
        #FullyScaledmodel =
        #'S:\Obl\AndersonLab\VertebralLoadingStudy\Matlab_Code\BaseModels\BaseModel_Male.osim'; mass = 74; #for testing stuff
        print('Making models with different Box properties')
        BoxX = 0.3;  #box seems to be .3 x .3 x .3 meters

        # no box
        hand_r = {}
        hand_l = hand_r.copy()
        NewModel = ChangeBox_Inertia(FullyScaledmodel, hand_r, hand_l, '_noBox')

        # both hands box
        hand_r['mass'] = 0.05 * mass; #10#bw box, split between hands
        hand_r['inertiaX'] = 1/12 * hand_r['mass'] * (2 * (BoxX)**2)
        hand_r['inertiaY'] = hand_r['inertiaX'] 
        hand_r['inertiaZ'] = hand_r['inertiaX']  #using rec Inertia = 1/12*m(a^2 + b^2); a=b; spliting between hands is taken care of with mass/2

        hand_l = hand_r  #in kg and kg*m^2
        NewModel = ChangeBox_Inertia(FullyScaledmodel, hand_r, hand_l, '_LRBox')  
        print('------------------------------------------------------------------------------------\n')

