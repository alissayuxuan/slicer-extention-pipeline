# %%
import numpy as np
import os
import re
import opensim as osim
import scipy.io as sio
from scipy.interpolate import interp1d
import shutil
import argparse
from lxml import etree

# %%
np.seterr(divide='ignore', invalid='ignore')


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

# %% [markdown]
# # Add_Marker

# %%
def Add_Marker(BaseModel,MarkerSetPath,output_model_path):
    """
    Adds markers to a given OpenSim model using.

    :param BaseModel: Path to the OpenSim model to which markers will be added.
    :type BaseModel: str

    :param MarkerSetPath: Path to the marker set file that contains the markers to be added.
    :type MarkerSetPath: str

    :param output_model_path: Directory path where the new model with added markers will be saved.
    :type output_model_path: str

    :return: Path to the new model with added markers.
    :rtype: str
    """
    Model = osim.Model(BaseModel)
    MarkerSet = osim.MarkerSet(MarkerSetPath)
    Model.set_MarkerSet(MarkerSet)

    newModel = os.path.join(output_model_path, Model.getName() + '.osim')
    Model.printToXML(newModel)
    return newModel

# %% [markdown]
# # Spine_Curvature_Adj

# %%
def XYZ2R(XYZ):
    """
    Converts Euler angles (XYZ rotation sequence) to a rotation matrix.

    :param XYZ: List or array containing three Euler angles [X, Y, Z].
    :type XYZ: list or np.ndarray

    :return: 3x3 rotation matrix corresponding to the provided Euler angles.
    :rtype: np.ndarray
    """
    X = XYZ[0]
    Y = XYZ[1]
    Z = XYZ[2]
    
    R = np.array([[np.cos(Y)*np.cos(Z) , np.cos(Z)*np.sin(Y)*np.sin(X)+np.sin(Z)*np.cos(X) , -np.cos(Z)*np.sin(Y)*np.cos(X)+np.sin(Z)*np.sin(X)],
                  [-np.sin(Z)*np.cos(Y), -np.sin(Z)*np.sin(Y)*np.sin(X)+np.cos(Z)*np.cos(X), np.sin(Z)*np.sin(Y)*np.cos(X)+np.cos(Z)*np.sin(X) ],
                  [np.sin(Y)           , -np.cos(Y)*np.sin(X)                              , np.cos(Y)*np.cos(X)                               ]])
    return R

def R2XYZ(R):
    """
    Converts a rotation matrix to Euler angles (XYZ rotation sequence).

    :param R: 3x3 rotation matrix.
    :type R: np.ndarray

    :return: List or array containing three Euler angles [X, Y, Z].
    :rtype: np.ndarray
    """
    newY = np.pi - np.arcsin(R[2,0])
    newX = np.arctan2(-R[2,1] / np.cos(newY), R[2,2] / np.cos(newY))
    newZ = np.arctan2(-R[1,0] / np.cos(newY), R[0,0] / np.cos(newY))
    XYZ = np.array([newX, newY, newZ])
    return XYZ


# %%
def Spine_Curvature_Adj(BaseModel, StrSubj, Sex, Height, mass, JointDist_Orig, JointAngle_Orig, output_model_path,GenericHeight):
    """
    Adjusts the spine curvature based on the given parameters and saves the adjusted model.

    :param BaseModel: Path to the model file.
    :type BaseModel: str

    :param StrSubj: Subject identifier (patient ID).
    :type StrSubj: str
 
    :param Sex: Gender of the subject. 'M' for male and 'F' for female.
    :type Sex: str

    :param Height: Height of the subject in centimeters.
    :type Height: float

    :param mass: Mass of the subject in kilograms.
    :type mass: float

    :param JointDist_Orig: Original distances between inter-vertebra joints.
    :type JointDist_Orig: np.ndarray

    :param JointAngle_Orig: Original angles of the inter-vertebra joints.
    :type JointAngle_Orig: np.ndarray

    :param output_model_path: Path to the directory where the adjusted model will be saved.
    :type output_model_path: str

    :param GenericHeight: Generic height value used for scaling.
    :type GenericHeight: float

    :return: Path to the saved adjusted model.
    :rtype: str
    """
    print('Adjusting Spine Curvature')

    k=1;  #use 'k' for sessions for some studies
    ## Get relevant subject-specific data             
    Ht = Height/100; # Change height from cm to m
    #subjectSex = char(ModelSex);
    BodyHt = Ht #*UppBodyHtFraction;
    lengthScaleFactor = BodyHt/GenericHeight

    # ##
    ## For CT data, we go from T1/2 - T2/T3 to L3/4 - L4/L5 angles
    # Joint Angles and Distances from subject's info file, derived from marker data in order from C7/T1 to T1/T2 down through L5/S1 to L4/L5 (before being flipped)
    JointDist = JointDist_Orig.copy()
    
    JointAngle = JointAngle_Orig.copy()
    JointAngle = np.flipud(JointAngle) # Start with L5/S1 first, 
    
    JointDist = np.flipud(JointDist)
        
    JointAngle[JointAngle==-9999] = 9999       

    # ##
    # Load the baseline model and initialize
    model = osim.Model(BaseModel)

    # ##
    ## Get baseline model joint information
    myJoints = model.getJointSet()
    # joints we want to adjust
    JointNames = ['L5_S1_IVDjnt','L4_L5_IVDjnt','L3_L4_IVDjnt','L2_L3_IVDjnt','L1_L2_IVDjnt','T12_L1_IVDjnt','T11_T12_IVDjnt','T10_T11_IVDjnt','T9_T10_IVDjnt','T8_T9_IVDjnt','T7_T8_IVDjnt','T6_T7_IVDjnt','T5_T6_IVDjnt','T4_T5_IVDjnt','T3_T4_IVDjnt','T2_T3_IVDjnt','T1_T2_IVDjnt','T1_head_neck']
    Loc_R = np.zeros((len(JointNames),3))
    Ori_R = Loc_R.copy() 

    # ##
    # Pull all 18 IVJ from model, even though only 17 joint distances (and angles) 
    for i in range(len(JointNames)):  #  4:21 when numbered #L5/S1 to T1_head_neck (T1/C7 equivalent) IVJ
        tempLocR = myJoints.get(JointNames[i]).get_frames(0).get_translation()
        tempOriR = myJoints.get(JointNames[i]).get_frames(0).get_orientation()
        Loc_R[i,:]= [osim.ArrayDouble.getValuesFromVec3(tempLocR).get(j) for j in range(3)] #Joint location in parent body
        Ori_R[i,:]= [osim.ArrayDouble.getValuesFromVec3(tempOriR).get(j) for j in range(3)] #Joint orientation in parent body

    # ##
    ## Get new joint inputs for model
    # For distances, start with L4/L5 IVJ from model, since its parent is L5
    
    Loc_R_ratios = lengthScaleFactor * np.ones((17,k))
    Loc_R2 = Loc_R[1:,1:2]
    Loc_R_ratios[JointDist!=9999] = (JointDist[JointDist!=9999]/1000) / Loc_R2[JointDist!=9999]  #put in m and normalize to basemodel
    

    # ##
    # Get baseline model joint angles, starting at L5/S1 (to actually rotate L5)
    JointAngleRel = np.full((len(Ori_R)-1,k), np.nan)

    # ##
    # For first joint angle (angle of L5 from sacrum), the relative motion is from the sacrum, so no modification to the angle is needed.
    if JointAngle[0,k-1] == 9999: #if the first measured joint angle is missing, 
        #keep the orientation in parent from baseline model for that joint
        JointAngleRel[0,k-1] = Ori_R[0,2]*180/np.pi #put in degrees
    else:
        # Keep first joint angle relative to ground (no subtraction)
        JointAngleRel[0,k-1] = JointAngle[0,k-1] #already in degrees

    # For remaining joint angles, get angle relative to previous vertebra.
    for i in range(1,17): #if any other joint angle measurements are missing, use 
        #orientation in parent from baseline model for that joint 
        if JointAngle[i,k-1] == 9999 or JointAngle[i-1,k-1] == 9999:
            JointAngleRel[i,k-1] = Ori_R[i,2]*180/np.pi #in degrees
        else:
            # Get the angle relative to IVJ below. For example, get relative change in angle of L3/L4 joint by subtracting that angle for the L4/L5 angle.
            JointAngleRel[i,k-1] = JointAngle[i,k-1]-JointAngle[i-1,k-1] #in degrees

    # ##
    JointAngleRel = JointAngleRel*np.pi/180 #convert to radians

    # ##
    # Set joint orientations in model   
    for i in range(len(JointNames)-1):  # 4:20 #L5/S1 to T1_T2
        NewOriR = osim.ArrayDouble.createVec3(0,0,JointAngleRel[i,k-1]) #Update i-# of joints, 17 
        myJoints.get(JointNames[i]).get_frames(0).set_orientation(NewOriR)

    # ##
    JointChange = np.zeros((12,3))  
    for i in range(5,len(JointAngleRel)):
        JointChange[i-5,:]= [np.sum(Ori_R[:i+1,0]),np.sum(Ori_R[:i+1,1]),np.sum(JointAngleRel[:i+1])-np.sum(Ori_R[:i+1,2])]       


    # ##
    ##   adjust ribs
    '''difference'''
    JointNames3 = ['T12_r12R_CVjnt','T11_r11R_CVjnt','T10_r10R_CVjnt','T9_r9R_CVjnt','T8_r8R_CVjnt','T7_r7R_CVjnt','T6_r6R_CVjnt','T5_r5R_CVjnt','T4_r4R_CVjnt','T3_r3R_CVjnt','T2_r2R_CVjnt','T1_r1R_CVjnt','T12_r12L_CVjnt','T11_r11L_CVjnt','T10_r10L_CVjnt','T9_r9L_CVjnt','T8_r8L_CVjnt','T7_r7L_CVjnt','T6_r6L_CVjnt','T5_r5L_CVjnt','T4_r4L_CVjnt','T3_r3L_CVjnt','T2_r2L_CVjnt','T1_r1L_CVjnt']
    Ori_R3 = np.zeros((len(JointNames3),3))
    for i in range(len(JointNames3)):  #  4:21 when numbered #L5/S1 to T1_head_neck (T1/C7 equivalent) IVJ
        tempOriR = myJoints.get(JointNames3[i]).get_frames(0).get_orientation()
        Ori_R3[i,:]= [osim.ArrayDouble.getValuesFromVec3(tempOriR).get(j) for j in range(3)] #Joint orientation in parent body


    # # ##
    Correction = np.tile(-JointChange, (2, 1))
    for i in range(len(JointNames3)):    #[21:44] #ribs
        gf=0
        OldValue = myJoints.get(JointNames3[i]).get_frames(gf).get_orientation()
        NewValueNum = [osim.ArrayDouble.getValuesFromVec3(OldValue).get(j) for j in range(3)]
        Rnv = XYZ2R(NewValueNum)  #probably over complicating, but works and takes into account any non-orthongonal corrections
        Rc  = XYZ2R(Correction[i,:])
        NewValueNum = R2XYZ(Rnv@Rc)
        NewValue = osim.ArrayDouble.createVec3(*NewValueNum)
        myJoints.get(JointNames3[i]).get_frames(gf).set_orientation(NewValue)
        
    # ##
    ## correct head sternum and shoulders
    CorrHeadNeck = np.sum(Ori_R[:17, 2]) - np.sum(JointAngleRel[:, k-1]) # Move head/neck back to upright position
    CorrSternum = np.sum(Ori_R[10:17, 2]) - np.sum(JointAngleRel[10:17, k-1]) #Move sternum to reflect new curvature; fixed from T7/T8 to T1/T2 (previously 8:11)
    CorrShoulder = CorrHeadNeck - CorrSternum # Correct arms to hange by sides (not held out in front).   

    #Correction = [CorrHeadNeck; CorrSternum; CorrShoulder; CorrShoulder];
    Correction = np.array([CorrHeadNeck, CorrHeadNeck, 0, 0])  #this seems to work better (jjb: 5/6/21)
    JointNames2 = ['T1_head_neck', 'r1R_sterR_jnt', 'shoulder_R', 'shoulder_L']

    '''difference'''
    for i in range(1): #size(JointNames2,1)    #[20 45 48 54] #head and neck, sternum, right shoulder, left shoulder
        OldValue = myJoints.get(JointNames2[i]).get_frames(0).get_orientation()
        #JointNames2{i} = char(myJoints.get(i).getName); #Array of Joint names

        NewValueNum = np.array([osim.ArrayDouble.getValuesFromVec3(OldValue).get(j) for j in range(3)])
        NewValueNum[2] += Correction[i]

        NewValue = osim.ArrayDouble.createVec3(*NewValueNum)
        myJoints.get(JointNames2[i]).get_frames(0).set_orientation(NewValue)
        


    # ##
    ## hide muscles for reviewing!
    nMuscles = model.getMuscles().getSize()
    for i in range(nMuscles):
        mus = model.getMuscles().get(i)
        mus.getGeometryPath().upd_Appearance().set_visible(False)

    # ##
    model.setName(StrSubj + '_SpineAdjust')
    New_modelpath = os.path.join(output_model_path ,model.getName() + '.osim')
    model.printToXML(New_modelpath)

    return New_modelpath

# %% [markdown]
# # Un_LockCoordinates_OS4

# %%
def Un_LockCoordinates_OS4(modelfile, U_LCoors, un_or_lock, Newmodelname):
    """
    Locks or unlocks specific joints in the given model file.

    :param modelfile: Path to the model file.
    :type modelfile: str

    :param U_LCoors: List of joints to be locked or unlocked.
    :type U_LCoors: list

    :param un_or_lock: Action to be performed on the joints Can be 'lock' or 'unlock'.
    :type un_or_lock: str

    :param Newmodelname: Name for the new model file after locking/unlocking. If 'Same', keeps the original name.
    :type Newmodelname: str

    :return: Path to the saved model with locked/unlocked coordinates.
    :rtype: str
    """
    print(un_or_lock+'ing select joints')
    ## check if want to lock or unlock joints
    if un_or_lock == 'lock':
        UNorLock = True
    elif un_or_lock =='unlock' :
        UNorLock = False
    else:
        print('Incorrect Input... making unlock')
        UNorLock = False


    ## naming stuff
    CurrentDirectory = os.path.dirname(modelfile)
    name = os.path.basename(modelfile).split('.')[0]
    ext = os.path.basename(modelfile).split('.')[1]


    if CurrentDirectory == '':  #check if path part of modelfile
        CurrentDirectory = os.getcwd().replace('//','/')

    if Newmodelname == '':  #renaming things
        Newmodelname = name + '_' + un_or_lock
    elif Newmodelname== 'Same': #keep name the same
        Newmodelname = name


    Model_Unlocked = os.path.join(CurrentDirectory, Newmodelname + '.'+ext)


    OSmodel = osim.Model(modelfile)
    
    Coordinates = OSmodel.getCoordinateSet()

    #Coordinates.printToXML(CurrentDirectory + '/' + 'CoordinateSet.XML')

    for i in range(len(U_LCoors)):
        Coordinates.get(U_LCoors[i,0]).setDefaultLocked(UNorLock)


    # saving things    
    OSmodel.setName(Newmodelname)
    OSmodel.printToXML(Model_Unlocked)
    return Model_Unlocked


# %% [markdown]
# # Spine_JtDist_Adj

# %%
def Spine_JtDist_Adj(BaseModel, StrSubj, Sex, Height, mass, JointDist_Orig, output_model_path):
    """
    Adjusts the spine joint distances in the given model based on the provided joint distances.

    :param BaseModel: Path to the baseline model file.
    :type BaseModel: str

    :param StrSubj: Subject identifier (patient ID).
    :type StrSubj: str

    :param Sex: Gender of the subject. 'M' for Male or 'F' for Female).
    :type Sex: str

    :param Height: Height of the subject in centimeters.
    :type Height: float

    :param mass: Mass of the subject in kilograms.
    :type mass: float

    :param JointDist_Orig: Original joint distances from the subject's info file.
    :type JointDist_Orig: np.ndarray

    :param output_model_path: Path to the directory where the adjusted model will be saved.
    :type output_model_path: str

    :return: Path to the saved model with adjusted spine joint distances.
    :rtype: str
    """
    ## For CT data, we go from T1/2 - T2/T3 to L3/4 - L4/L5 angles
    # Joint Distances from subject's info file, derived from marker data in order from C7/T1 to T1/T2 down through L5/S1 to L4/L5 (before being flipped)
    JointDist = JointDist_Orig.copy()
    JointDist = np.flipud(JointDist)/1000 #put in mm

    # ##
    ## Load the baseline model and initialize
    model = osim.Model(BaseModel)

    # ##
    ## Get baseline model joint information
    myJoints = model.getJointSet()        
    # joints we want to adjust
    JointNames = ['L5_S1_IVDjnt','L4_L5_IVDjnt','L3_L4_IVDjnt','L2_L3_IVDjnt','L1_L2_IVDjnt','T12_L1_IVDjnt','T11_T12_IVDjnt','T10_T11_IVDjnt','T9_T10_IVDjnt','T8_T9_IVDjnt','T7_T8_IVDjnt','T6_T7_IVDjnt','T5_T6_IVDjnt','T4_T5_IVDjnt','T3_T4_IVDjnt','T2_T3_IVDjnt','T1_T2_IVDjnt','T1_head_neck']
    Loc_R = np.zeros((len(JointNames),3))

    # ##
    # Pull all 18 IVJ from model, even though only 17 joint distances (and angles) 
    for i in range(len(JointNames)):  #  4:21 when numbered #L5/S1 to T1_head_neck (T1/C7 equivalent) IVJ
        tempLocR = myJoints.get(JointNames[i]).get_frames(0).get_translation()
        Loc_R[i,:]= [osim.ArrayDouble.getValuesFromVec3(tempLocR).get(j) for j in range(3)] #Joint location in parent body

    # ##
    Model_Scaled_Heights = Loc_R[1:,1:2].copy()  #2nd column is y-axis/direction height/distance

    Matching_JD = np.zeros_like(Model_Scaled_Heights) #preallocate array
    Matching_JD[JointDist<5] = Model_Scaled_Heights[JointDist<5]  #good joint distances
    Total_Scaled_Matching = np.sum(Matching_JD)  #how 'tall' the good joint distances are in model
    Total_Scaled_NOTmatching = np.sum(Model_Scaled_Heights[JointDist>=5]) #how 'tall' the unmeasured joint distances are in model #if don't add 9.999 above add here to account for L5/S1                 
    Total_SpineY =  np.sum(Model_Scaled_Heights)  #how tall total model spine is
    Ratio_Matching = Matching_JD/Total_Scaled_Matching  #how much of the spine distance is known relative to total height

    JD_0s = JointDist.copy()
    JD_0s[JointDist>=5] = 0  #get rid of 9.9999
    Total_JD_Found = np.sum(JointDist[JointDist<5]) #how 'tall' the good joint distances were calculated to be
    Ratio_JD_Found = JD_0s / Total_JD_Found #ratio of what known to known height
    RofRatios = Ratio_JD_Found/Ratio_Matching  #ratio of ratios from what found to what I assumed

    # ##
    ### use ratio of what was found to what was assumed prior to find new distances      
    Model_Scaled_Heights[JointDist<5] = Model_Scaled_Heights[JointDist<5] * RofRatios[JointDist<5]

    Use_JD3 = Loc_R.copy()
    Use_JD3[1:,1:2] = Model_Scaled_Heights

    # ##
    '''difference'''
    # ##      set new joint distances in model 
    for i in range(len(JointNames)):   # 4:20 #L5/S1 to T1_T2
        NewLoc_R = osim.ArrayDouble.createVec3(*Use_JD3[i]); #Update i-# of joints, 18 
        myJoints.get(JointNames[i]).get_frames(0).set_translation(NewLoc_R)

    rIVJ_Use = Use_JD3[:,1:2]/Loc_R[:,1:2]  

    # ##
    ## scale image, CoM y location for each vertebrae 
    vBodies = ['lumbar5', 'lumbar4', 'lumbar3', 'lumbar2', 'lumbar1', 'thoracic12', 'thoracic11', 'thoracic10', 'thoracic9','thoracic8', 'thoracic7','thoracic6', 'thoracic5', 'thoracic4','thoracic3', 'thoracic2', 'thoracic1' ]


    # ##
    '''difference'''
    for v in range(len(vBodies)):
        Body = vBodies[v]
        cBody= model.getBodySet().get(Body)  
        
    # image
        scaleFacts = np.array([cBody.get_attached_geometry(0).get_scale_factors(0).get(j) for j in range(3)])
        setSF = osim.ArrayDouble.createVec3(scaleFacts[0],scaleFacts[1]*rIVJ_Use[v+1,0],scaleFacts[2])
        cBody.get_attached_geometry(0).set_scale_factors(setSF)
        
    # CoM y
        bCoM = np.array([cBody.getMassCenter().get(j) for j in range(3)])
        setCOM = osim.ArrayDouble.createVec3(bCoM[0],bCoM[1]*rIVJ_Use[v+1,0],bCoM[2])
        cBody.setMassCenter(setCOM)    

    # ##
    ## hide muscles for reviewing! (only need to really problem solve)

    nMuscles = model.getMuscles().getSize()
    for i in range(nMuscles):
        mus = model.getMuscles().get(i)
        mus.getGeometryPath().upd_Appearance().set_visible(False)

    # ##
    ## Scale model and write to a new .osim file:
    model.setName(StrSubj + '_SpineDistAdjust')
    New_modelpath = os.path.join(output_model_path , model.getName() + '.osim')
    model.printToXML(New_modelpath) ### stop here and run like I used too!
    return New_modelpath

# %% [markdown]
# # ScaleOpenSim

# %%
def ScaleOpenSim_sub(Ssetup):
    """
    Scales the OpenSim model based on the provided setup file.
    The Opensim API must read the scaletool from the root of work director, or may cause some error. Don't know why.

    :param Ssetup: Path to the scaling setup file.
    :type Ssetup: str

    :return: Name of the scaled model.
    :rtype: str
    """
  ### seems to work better with this sub function as opens (rather than keeps open) setup file and works best without the path extension so renaming stuff and deleting is best
    sname = os.path.basename(Ssetup).split('.')[0]
    print('Performing Scaling with:   '+ sname +'\n')
    STool2 = osim.ScaleTool(sname + '.xml')
    STool2.run()  #need seperate function, puts in HearGrant righ tnow!
    Scalemodelname = STool2.getName()
    return Scalemodelname

# %%
def ScaleOpenSim(OSmodel, SetupFileGeneric, TRCfile, smass, Newmodelname,output_setups_path,output_model_path):
    """
    Scales the OpenSim model based on marker data.

    :param OSmodel: Path to the OpenSim model file.
    :type OSmodel: str

    :param SetupFileGeneric: Path to the generic setup file for scaling.
    :type SetupFileGeneric: str

    :param TRCfile: Path to the TRC marker data file.
    :type TRCfile: str

    :param smass: Subject mass.
    :type smass: float

    :param Newmodelname: Name for the new scaled model.
    :type Newmodelname: str

    :param output_setups_path: Path to the directory where the setup files will be saved.
    :type output_setups_path: str

    :param output_model_path: Path to the directory where the scaled model will be saved.
    :type output_model_path: str

    :return: Tuple containing the path to the scaled model and the path to the setup file.
    :rtype: tuple(str, str)
    """
    STool = osim.ScaleTool(SetupFileGeneric)


    # Load the model and initialize
    # model = Model(OSmodel);
    # myState = model.initSystem();
    #     
    # Get initial and intial time, left like this in case I edit/want to adjust times, but really only using 'else' part right now
    markerData = osim.MarkerData(TRCfile)

    if 'Times' not in locals() or not Times:
        initial_time = markerData.getStartFrameTime()
        final_time = markerData.getLastFrameTime()
    else:
        initial_time = Times[0]
        final_time = Times[1]



    TRCpath = os.path.dirname(TRCfile)
    TRCname = os.path.basename(TRCfile).split('.')[0]


    STool.setName(Newmodelname)

    STool.setSubjectMass(smass)

    Tarray = osim.ArrayDouble()  #initialize array
    Tarray.set(0, initial_time)
    Tarray.set(1, final_time)


    ### ModelScaler stuff
    STool.getModelScaler().setTimeRange(Tarray)

    STool.getModelScaler().setMarkerFileName(TRCfile)

    STool.getModelScaler().setApply(True)
    fName = Newmodelname + '.osim'
    STool.getModelScaler().setOutputModelFileName(fName) #1 of 2, scaling
    #STool.getModelScaler().setOutputScaleFileName( fullfile(TRCpath, Newmodelname, '_ScaleFactors', 'sto'));


    ### ModelPlacer stuff
    STool.getMarkerPlacer().setOutputModelFileName(fName) #2 of 2, markers
    # STool.getMarkerPlacer().setOutputMarkerFileName( fullfile(TRCpath, [TRCname '_MarkerFile' '.xml']) );
    # STool.getMarkerPlacer().setOutputMotionFileName( fullfile(TRCpath, [TRCname '_ScaleMotion' '.mot']) );
    STool.getMarkerPlacer().setMarkerFileName(TRCfile) #Strange behavior: Opensim API regards this filename as relative path to the parent folder of work folder.
    STool.getMarkerPlacer().setTimeRange(Tarray)


    ### ModelMaker stuff
    STool.getGenericModelMaker().setModelFileName(OSmodel)

    ### Set output names
    #Ssetup = os.path.join(output_setups_path,'Scale_setup_' +Newmodelname + '.xml')
    Ssetup = os.path.join(os.getcwd(),'Scale_setup_' +Newmodelname + '.xml') # !! Important: This setup must be save in the os.getcwd(), or will cause error
    STool.printToXML(Ssetup)  #temperarily write setupfile
            
    Scalemodelname = ScaleOpenSim_sub(Ssetup)  #sub function

    # Construct the source and destination file paths
    source1 = os.path.join(os.getcwd(),Newmodelname +'.osim')

    shutil.copy2(source1, os.path.join(output_model_path ,Newmodelname +'.osim'))
    os.remove(source1)

    # Copy the second file
    shutil.copy2(Ssetup, os.path.join(output_setups_path,'Scale_setup_' + Newmodelname + '.xml'))
    os.remove(Ssetup)


    Scalemodelname = os.path.join(output_model_path,Newmodelname +'.osim')

    return Scalemodelname, Ssetup

# %% [markdown]
# # Scale_Height

# %%
def Scale_Hight(BaseModel, StrSubj, Sex, Height, mass, ScaleSetupFile,output_model_path,output_setups_path,GenericHt):
    """
    Scales the model based on height if no marker data is provided.

    :param BaseModel: Path to the base OpenSim model file.
    :type BaseModel: str

    :param StrSubj: Subject identifier (patient ID).
    :type StrSubj: str

    :param Sex: Sex of the subject.
    :type Sex: str

    :param Height: Height of the subject in centimeters.
    :type Height: float

    :param mass: Mass of the subject.
    :type mass: float

    :param ScaleSetupFile: Path to the scaling setup file.
    :type ScaleSetupFile: str

    :param output_model_path: Path to the directory where the scaled model will be saved.
    :type output_model_path: str

    :param output_setups_path: Path to the directory where the setup files will be saved.
    :type output_setups_path: str

    :param GenericHt: Generic height value for scaling.
    :type GenericHt: float

    :return: Path to the new scaled model.
    :rtype: str
    """

    Ht = Height/100 #Change height from cm to m
    Wt = mass
    k=0
    BodyHt = Ht #*UppBodyHtFraction
    lengthScaleFactor = BodyHt/GenericHt
    BodyWt = Wt #*(35.878661544 / 61)



    #for the measured intervertebral joint distances, get ratio 
    #of measured distance to baseline model distance to create scale factors
    # Loc_R_ratios = np.full(shape=(17,1),fill_value = lengthScaleFactor)

    scTool = osim.ScaleTool(ScaleSetupFile)
    ## Set joint distances in model
    scaler = scTool.getModelScaler()
        # Add in marker data
    #scaler.setMarkerFileName('Trial01.trc');

    scales = scaler.getScaleSet()
    numScales = scales.getSize() #number of bodies to scale

    
    for s in range(numScales): # get all body scale factors
        scales.get(s).setScaleFactors(osim.ArrayDouble.createVec3(lengthScaleFactor, lengthScaleFactor, lengthScaleFactor))

    
    # for s in range(13,30): # L5 to T1 scale factors derived from  measurements, this is not updated to 4:20, because it's specific to the setup file order
    #     scales.get(s).setScaleFactors(osim.ArrayDouble.createVec3(lengthScaleFactor,lengthScaleFactor,lengthScaleFactor)); # updated s-3

    
    ## Scale model and write to a new .osim file:
    model = osim.Model(BaseModel)
    New_modelpath = os.path.join(output_model_path , StrSubj + '_Scaled_Height.osim')
    scaler.setOutputModelFileName(New_modelpath) #Set the name of the new model
    scaler.processModel(model,output_model_path, BodyWt) #processes scaling and writes to a new file.
    scaler.printToXML(os.path.join(output_setups_path ,StrSubj + '_Scale_Setup.xml'))

    return New_modelpath


# %% [markdown]
# # AddDOF_OS4

# %%
def AddDOF_OS4(UnconstrainedModel, ModelCCC): 
    """
    Adds Degrees of Freedom (DoF) to an OpenSim model based on a provided model with constraints (CCCs).

    :param UnconstrainedModel: Path to the base OpenSim model without constraints.
    :type UnconstrainedModel: str

    :param ModelCCC: Path to the OpenSim model with constraints (CCCs).
    :type ModelCCC: str

    :return: Path to the new model with added DoF.
    :rtype: str
    """

    print('Making model with CCCs')

    ## load CCC #DoF model
    OrigConsModel = osim.Model(ModelCCC)
    state = OrigConsModel.initSystem() #initialize the model; get model state, but really do not need left of equal sign stuff

    # get and copy CCC
    Constraints = OrigConsModel.getConstraintSet()
    ConsClone = Constraints.clone()


    # Assuming ModelCCC is a string variable

    # Find the index of the 'DOF' substring
    dof_spot = ModelCCC.find('DOF')

    # If 'DOF' substring is found
    if dof_spot != -1:

        pattern = r'_([0-9]*)DOF'
        re_result = re.search(pattern,ModelCCC)
        
        if re_result != None: 
            DoF = int(re_result.group(1))
        else:
            DoF = 51
    else:
        DoF = 51

    # dof now holds the extracted substring or 51 if 'DOF' was not found.




    ## Load Scaled Model without constraints and then add the constraints
    NewConsModel = osim.Model(UnconstrainedModel)
    state = NewConsModel.initSystem()
    # add CCC from other model
    Constraints2 = NewConsModel.updConstraintSet()  #'upd' new for OS4, used to be 'get', but that doesn't 'tell' the model to update things according to a june 11, 2020 forum post (by Emily Dooley) 
    Constraints2.assign(ConsClone)


    ## save & name new model and clean up stuff  
    
    SubjectDirectory = os.path.dirname(UnconstrainedModel)
    name = os.path.basename(UnconstrainedModel).split('.')[0]

    NewName = name + '_' +str(DoF) + 'DOF'
    #NewName = ['BaseFullbody_' num2str(DoF) 'DOF'];
    NewConsModel.setName(NewName)
    newCCCModel = os.path.join(SubjectDirectory , NewName + '.osim')
    NewConsModel.printToXML(newCCCModel)

    return newCCCModel

# %% [markdown]
# # ScaleMuscleMarkerModel

def interp1(x,Y,xi):
    """
    Performs 1D linear interpolation on given data.

    :param x: The x-coordinates of the data points.
    :type x: numpy.ndarray of shape (n, 1)

    :param Y: The y-coordinates of the data points for each column.
    :type Y: numpy.ndarray of shape (n, m)

    :param xi: The x-coordinates at which to evaluate the interpolated values.
    :type xi: numpy.ndarray of shape (n, 1)

    :return: Interpolated values at xi for each column of Y.
    :rtype: numpy.ndarray of shape (n, m)
    """
    result = []
    # x: (n*1) Y:(n*m) xi:(n*1)
    for i in range(Y.shape[1]):
        f = interp1d(x[:,0], Y[:,i], kind='linear')
        result.append(f(xi[:,0]))
    return np.array(result).T
# %%
def Evaluate_Muscle_AllLevels_v3_EOTM(modelpath):
    '''
    This function processes and evaluates muscle data on all vertebra levels from a given model path. It computes metrics related to muscle groups, such as their cross-sectional areas (CSAs), moment arms in the X and Z directions, and other related metrics.

    :param modelpath: The path to the model containing information about muscle groups.
    :type modelpath: str

    :returns: A tuple containing dictionaries with results for group CSAs, moment arms in the X and Z directions, and other metrics. The tuple also includes additional information like `VertCentY`, `VertCent`, and `JointCent`.
    :rtype: tuple
    '''
    # ##
    myModel = osim.Model(modelpath) #load the model
    state = myModel.initSystem() #initialize the model; get model state
    myModel.equilibrateMuscles(state)  # Make sure the muscles states are in equilibrium

    # ##
    #get Body information|
    myBodies = myModel.getBodySet()
    numBodies = myBodies.getSize()
    BodyNames = [] #initialize cell array for bodies
    for i in range(numBodies):
        BodyNames.append(myBodies.get(i).getName()) #Array of Body names


    # ##
    # Get Joint information
    myJoints = myModel.getJointSet()
    numJoints = myJoints.getSize()
    JointNames = []
    JtPosGlobStruct = {}
    for i in range(numJoints):
        
        ## 4.0 New update
    #     Parent{i} = char(myJoints.get(i-1).getParentName); #Identify parent body
    #     Child{i} = char(myJoints.get(i-1).getBody); #Identify child body
        JointNames.append(myJoints.get(i).getName()) #Array of Joint names
        
    #     temp = ArrayDouble.createVec3([0,0,0]);
    #     globalPos = ArrayDouble.createVec3([0.0,0.0,0.0]);
        tempJtPos = myJoints.get(i).get_frames(0).getPositionInGround(state)
    #     Loc_R(i,:)= str2num(char(ArrayDouble.getValuesFromVec3(temp))); #Joint location in parent body
    #     Loc_r(i,:)= str2num(char(ArrayDouble.getValuesFromVec3(myJoints.get(i-1).getLocationInChild()))); #Joint location in child body
        
    #     myModel.getSimbodyEngine().transformPosition(state, myBodies.get(Parent{i}),temp,myModel.getGroundBody, globalPos);

        JtPosGlobStruct[JointNames[i]] = np.array([osim.ArrayDouble.getValuesFromVec3(tempJtPos).get(j) for j in range(3)]) #Joint location in global frame

    # ##
    ## Get axial positions of vert bodies:

    count=0
    JntArray = np.zeros((17,2,3))
    VertCent = np.zeros((17,3))
    VertCentY = np.zeros((17,1))
    JointCent = np.zeros((18,3))
    JointCentY = np.zeros((18,1))

    # ##
    for i in range(20,3,-1):#CHANGED TO T1 to L5
        JntArray[count] = np.array([JtPosGlobStruct[JointNames[i]],JtPosGlobStruct[JointNames[i-1]]])
        VertCent[count] = JntArray[count,1,:] + (JntArray[count,0,:] - JntArray[count,1,:])/2
        VertCentY[count,0] = VertCent[count,1]
        JointCent[count] = JtPosGlobStruct[JointNames[i]]
        JointCentY[count,0] = JtPosGlobStruct[JointNames[i]][1] # Added
        count += 1

    JointCentY[17,0] = JtPosGlobStruct[JointNames[3]][1] #Include L5-Sac joint
    JointCent[17] = JtPosGlobStruct[JointNames[3]]

    VertHeights = JointCentY[0:17] - JointCentY[1:18] #vertebral level heights (between joints) in axial direction.

    # ##
    #Examine the muscle groups:
    struct_strings = ['VertCent','JointCent']
    num_samples = [17,18]

    GroupCSA_info = {}
    GroupMAX_info = {}
    GroupMAZ_info = {}
    FascicleCSA_info = {}
    FascicleMAX_info = {}
    FascicleMAZ_info = {}

    # ## [markdown]
    # ## loc for loop:

    # ##
    #for loc in range(1,2):
    loc = 0

    CSA_TL = {} 
    CSA_TM = {} 
    CSA_TH = {} 
    X_MA_TL = {} 
    X_MA_TM = {} 
    X_MA_TH = {} 
    Z_MA_TL = {} 
    Z_MA_TM = {} 
    Z_MA_TH = {} 

    GroupCSA_TL = []
    GroupCSA_TM = []
    GroupCSA_TH = []

    # Use correct variable depending on sampling vertebrae or joints
    if loc == 0:
        CentPosY = VertCentY
        CentPos = VertCent
    else:
        CentPosY = JointCentY
        CentPos = JointCent
        # clear CSA_TL CSA_TM CSA_TH X_MA_TL X_MA_TM X_MA_TH Z_MA_TL Z_MA_TM Z_MA_TH ...
        #     GroupCSA_TL GroupCSA_TM GroupCSA_TH Group_X_MA_TL Group_X_MA_TM Group_X_MA_TH ...
        #     Group_Z_MA_TL Group_Z_MA_TM Group_Z_MA_TH

    # ## [markdown]
    # ### g for loop:

    # ##
    MuscleGroupNamesArray = []
    for g in range(11):
        # g = 0


        # ##
        MuscleGroup = myModel.getForceSet().getGroup(g)
        MuscleGroupName = MuscleGroup.getName()
        MuscleGroupNamesArray.append(MuscleGroupName)
        FascicleNames = MuscleGroup.getMembers()
        FascicleNum = FascicleNames.getSize()

        # ##
        CSA_TL[MuscleGroupName] = []
        CSA_TM[MuscleGroupName] = []
        CSA_TH[MuscleGroupName] = []

        X_MA_TL[MuscleGroupName] = []
        X_MA_TM[MuscleGroupName] = []
        X_MA_TH[MuscleGroupName] = []

        Z_MA_TL[MuscleGroupName] = []
        Z_MA_TM[MuscleGroupName] = []
        Z_MA_TH[MuscleGroupName] = []

        # ## [markdown]
        # #### m for loop:

        # ##
        MuscleList = []
        #for m = 1:FascicleNum #go through fascicles
        for m in range(FascicleNum):
            # m=1

            # ##
            #Process each fascicle
            CurrentFasName = FascicleNames.get(m).getName()
            aMuscle = myModel.getMuscles().get(CurrentFasName) #The muscle fascicle
            MuscleList.append(aMuscle.getName()) #record muscle name
            faslength = aMuscle.getLength(state) #Get fascicle length
            TendonLength = aMuscle.getTendonLength(state) #Get fascicle tendon length
            Strength = aMuscle.getMaxIsometricForce() #Get max muscle strength
            Pennation = aMuscle.getPennationAngle(state) #Get current pennation angle

            # ##
            #Get the current muscle path from Geometry Path (includes wrapping and via points)
            aMuscleGeometry = aMuscle.getGeometryPath()
            aCurrentPath = aMuscleGeometry.getCurrentPath(state)
            NumCurrentPath = aCurrentPath.getSize() # Number of path points

            # ##
            # Get global position of each path point
            PtGlobal = np.zeros((NumCurrentPath,3))
            for i in range(NumCurrentPath):
                PtBody = aCurrentPath.getitem(i).getBody().getName() #Body the point is in
                globalPos = osim.ArrayDouble.createVec3(0.0,0.0,0.0)
                myModel.getSimbodyEngine().transformPosition(state, myBodies.get(PtBody),aCurrentPath.getitem(i).getLocation(state),myModel.getGround(), globalPos)
                PtGlobal[i,:] = np.array([osim.ArrayDouble.getValuesFromVec3(globalPos).get(j) for j in range(3)])

            # ##
            # Check order of muscle points; want them to go from low to high
            if PtGlobal[0,1] > PtGlobal[-1,1]: # Pt 1 is higher than Pt N
                PtGlobal = PtGlobal[::-1] #Flip PtGlobal over

            Pt1Global = PtGlobal[0] #first path point
            PtNGlobal = PtGlobal[-1] #last path point

            # ##

            ## Determine if musculotendon unit is present at each vertebral level
            Pt1_y = Pt1Global[1] #axial position of endpoint 1
            PtN_y = PtNGlobal[1] #axial position of endpoint 2
            Pt_lower = Pt1_y
            Pt_higher = PtN_y

            MTUPresent = (CentPosY >= Pt_lower) & (CentPosY <= Pt_higher)

            # ##
            ## Determine if muscle portion of MTU is present at each vertebral level, assuming tendon is lower end of
            #musculotendon unit:

            # Get path lengths between each path point 
            PathLengths = (np.sum((PtGlobal[1:NumCurrentPath]-PtGlobal[0:NumCurrentPath-1])**2,1))**(1/2)

            #Find point where each musculotendon unit switches from tendon to
            #muscle:
            TendonRemainder = TendonLength #Initialize how much tendon length there is.
            for j in range(NumCurrentPath-1):
                if TendonRemainder < PathLengths[j]: # the tendon ends in this section of the musculotendon unit
                    Pt1 = PtGlobal[j]
                    Pt2 = PtGlobal[j+1]
                    diff = Pt2 - Pt1
                    sectionlength = np.linalg.norm(diff) #(np.sum(diff**2))**(1/2) length between 2 adjacent path points
                    MTjunction = PtGlobal[j] + TendonRemainder/sectionlength*diff #location of switch from tendon to muscle in musculotendon unit
                    #Set the Muscle Section points
                    MuscleSection = np.vstack([MTjunction,PtGlobal[j+1:]])
                    break #once found, stop
                else: #the tendon hasn't ended yet
                    TendonRemainder = TendonRemainder - PathLengths[j]

            # ##
            #Determine if muscle portion of musculotendon unit is present at each vertebral level
            Pt1_y = MTjunction[1] #axial position of endpoint 1
            PtN_y = PtNGlobal[1] #axial position of endpoint 2

            MusclePts_y = MuscleSection[:,1]; #axial positions of muscle section endpoints.
            NumMuscleSections = len(MusclePts_y) - 1; # number of segments of muscle component

            # ##
            # Determine cross-sectional areas of fascicle
                    
            PCSA = Strength/100 # convert max isometric force to PCSA, using the MMS - orginal value of 100 N/cm2
            ACSA = PCSA*np.cos(Pennation) # calculate ACSA for fascicle

            #clear Pt New_xz FasMidVertPos MomArms
            MomArms = np.zeros((num_samples[loc],3))
            CSA_LT = np.zeros((num_samples[loc],1))

            # ## [markdown]
            # ##### j for loop for j = 1:num_samples(loc)

            for j in range(num_samples[loc]): #do for T1 to L5 if vert centroid, or NEW: t1-head to L5-s1
                #print('j = ',j)
                AboveUpper = MusclePts_y > JointCentY[j] #are muscle section endpoints above the upper joint.
                BelowUpper = MusclePts_y <= JointCentY[j] #are muscle section endpoints at or below the upper joint.
                AboveLower = MusclePts_y >= JointCentY[j+1]  # are muscle section endpoints at or above the lower joint.
                BelowLower = MusclePts_y < JointCentY[j+1]  # are muscle section endpoints below the lower joint.
                LengthInside = np.zeros((NumMuscleSections,1)) #array for lengths of muscle sections within vertebra
                #                 SectionVolumeInside = zeros(NumMuscleSections); #array for volume of muscle within vertebra
                SectionCentersInside = np.zeros((NumMuscleSections,3)); #array for centers of muscle sections within

                for k in range(NumMuscleSections): #check if muscle sections are partly or fully within VB level
                    # get original muscle section points
                    Pt1 = MuscleSection[k] #low
                    Pt2 = MuscleSection[k+1] #high
                    Pt = np.vstack([Pt2, Pt1])
                    
                    if Pt1[1] > Pt2[1]: # Pt 1 is higher than Pt 2, change order of Pt.
                        Pt = np.vstack([Pt1, Pt2])

                    if BelowLower[k] and AboveUpper[k+1]: #muscle section completely spans the vertebra
                        #print(1)
                        #Get global position where muscle section crosses joint positions
                        New_xz = interp1(Pt[:,1:2],np.hstack([Pt[:,0:1],Pt[:,2:3]]),JointCentY[j:j+2])
                        SectionPts = np.hstack([New_xz[:,0:1],JointCentY[j:j+2],New_xz[:,1:2]]) 

                    elif BelowLower[k] and AboveLower[k+1] and BelowUpper[k+1]: # upper part of section within the vertebra
                        #print(2)
                        #Get global position where muscle section crosses lower joint
                        New_xz = interp1(Pt[:,1:2],np.hstack([Pt[:,0:1],Pt[:,2:3]]),JointCentY[j+1:j+2])
                        SectionPts = np.vstack([Pt2,[New_xz[0,0],JointCentY[j+1,0],New_xz[0,1]]]); 
                            
                    elif  AboveLower[k] and BelowUpper[k+1]:  # entire section is within the vertebra
                        #print(3)
                        #Muscle section doesn't cross joint positions, so
                        #use whole thing.
                        SectionPts = Pt
                                        
                    elif AboveLower[k] and BelowUpper[k] and AboveUpper[k+1]: #lower part of section within the vertebra
                        #print(4)
                        #Get global position where muscle section crosses upper joint
                        New_xz = interp1(Pt[:,1:2],np.hstack([Pt[:,0:1],Pt[:,2:3]]),JointCentY[j:j+1])
                        SectionPts = np.vstack([[New_xz[0,0],JointCentY[j,0],New_xz[0,1]], Pt1 ])
                                            
                    else: #none of the section is within the vertebra
                        continue
                                #calculate length and center of this
                    #section
                    #print(' k= ',k)
                    # print(SectionPts)
                    diff = SectionPts[1,:] - SectionPts[0,:]
                    #print('diff=', diff)
                    LengthInside[k] = np.linalg.norm(diff) #(np.sum((diff)**2))**0.5 L2 norm #length of muscle section within the vertebra
                    SectionCentersInside[k,:] = np.sum(SectionPts,axis=0)/2 #global center of this muscle section within the vertebra 

                #calculate CSA and moment arm at this vertebral level
                SectionVolumeInside = LengthInside*ACSA; #volumes of muscle section(s) within the vertebra
                TotalVolumeInside = np.sum(SectionVolumeInside)
 #               print(' LengthInside = \n',LengthInside,'\n')
                #                 VertHeights(j)
                #                 CSA_LT
                CSA_LT[j] = TotalVolumeInside/VertHeights[j] #Average CSA estimated as volume / vertebral height.  
                if TotalVolumeInside > 0 :# only calculate moment arm if some muscle is present
                    TotalCentersInside = np.sum(SectionCentersInside * SectionVolumeInside,axis=0)/TotalVolumeInside #weighted center position of the muscles inside.
                    # print(SectionCentersInside)
                    # print(TotalVolumeInside)
                    # print(TotalCentersInside)
                    MomArms[j,:] = TotalCentersInside - CentPos[j,:]
                

            # ## [markdown]
            # ##### j for loop end

            # ##
            MusclePresent_LT = CSA_LT > 0
            CSA_LT = CSA_LT.T
            X_MA_LT = MomArms[:,0:1].T
            Z_MA_LT = MomArms[:,2:3].T

            # ##
            ## Determine if muscle portion of MTU is present at each vertebral level, assuming tendon is equally distributed at lower and upper ends of
            #musculotendon unit:
            TendonRemainder = TendonLength/2 #Initialize how much tendon length there is.
            for j in range(NumCurrentPath-1):
                if TendonRemainder < PathLengths[j]: # the tendon ends in this section of the musculotendon unit
                    Pt1 = PtGlobal[j,:]
                    Pt2 = PtGlobal[j+1,:]
                    diff = Pt2 - Pt1
                    sectionlength = np.linalg.norm(diff) #L2 norm
                    MTjunction_low = PtGlobal[j,:] + TendonRemainder/sectionlength*diff#location of switch from tendon to muscle in musculotendon unit
                    jlow = j+1 #index found for lower end of muscle section.
                    break #once found, stop
                else: #the tendon hasn't ended yet
                    TendonRemainder = TendonRemainder - PathLengths[j]

            # ##

            TendonRemainder = TendonLength/2; #Initialize how much tendon length there is.
            for j in range(NumCurrentPath-2,-1,-1):# NumCurrentPath-1:-1:1
                if TendonRemainder < PathLengths[j]: # the tendon ends in this section of the musculotendon unit
                    Pt1 = PtGlobal[j+1,:]
                    Pt2 = PtGlobal[j,:]
                    diff = Pt2-Pt1
                    sectionlength = np.linalg.norm(diff)
                    MTjunction_high = PtGlobal[j+1,:] + TendonRemainder/sectionlength*diff #location of switch from tendon to muscle in musculotendon unit
                    #Set the Muscle Section points
                    MuscleSection = np.vstack([MTjunction_low, PtGlobal[jlow:j+1,:],MTjunction_high])
                    break #once found, stop
                else: #the tendon hasn't ended yet
                    TendonRemainder = TendonRemainder - PathLengths[j]

            # ##
            MusclePts_y = MuscleSection[:,1:2] #axial positions of muscle section endpoints.
            NumMuscleSections = len(MusclePts_y) - 1 # number of segments of muscle component  

            PCSA = Strength/100 # convert max isometric force to PCSA, using the MMS - orginal value of 100 N/cm2
            ACSA = PCSA*np.cos(Pennation) # calculate ACSA for fascicle

            MomArms = np.zeros((num_samples[loc],3))
            CSA_MT = np.zeros((num_samples[loc],1))

            # ## [markdown]
            # ##### j for loop 2 

            # ##
            for j in range(num_samples[loc]): #do for T1 to L5 if vert centroid, or NEW: t1-head to L5-s1
                # print('j = ',j)
                AboveUpper = MusclePts_y > JointCentY[j] #are muscle section endpoints above the upper joint.
                BelowUpper = MusclePts_y <= JointCentY[j] #are muscle section endpoints at or below the upper joint.
                AboveLower = MusclePts_y >= JointCentY[j+1]  # are muscle section endpoints at or above the lower joint.
                BelowLower = MusclePts_y < JointCentY[j+1]  # are muscle section endpoints below the lower joint.
                LengthInside = np.zeros((NumMuscleSections,1)) #array for lengths of muscle sections within vertebra
                #                 SectionVolumeInside = zeros(NumMuscleSections); #array for volume of muscle within vertebra
                SectionCentersInside = np.zeros((NumMuscleSections,3)); #array for centers of muscle sections within

                for k in range(NumMuscleSections): #check if muscle sections are partly or fully within VB level
                    # get original muscle section points
                    Pt1 = MuscleSection[k] #low
                    Pt2 = MuscleSection[k+1] #high
                    Pt = np.vstack([Pt2, Pt1])
                    
                    if Pt1[1] > Pt2[1]: # Pt 1 is higher than Pt 2, change order of Pt.
                        Pt = np.vstack([Pt1, Pt2])

                    if BelowLower[k] and AboveUpper[k+1]: #muscle section completely spans the vertebra
                        # print(1)
                        #Get global position where muscle section crosses joint positions
                        New_xz = interp1(Pt[:,1:2],np.hstack([Pt[:,0:1],Pt[:,2:3]]),JointCentY[j:j+2])
                        SectionPts = np.hstack([New_xz[:,0:1],JointCentY[j:j+2],New_xz[:,1:2]]) 

                    elif BelowLower[k] and AboveLower[k+1] and BelowUpper[k+1]: # upper part of section within the vertebra
                        # print(2)
                        #Get global position where muscle section crosses lower joint
                        New_xz = interp1(Pt[:,1:2],np.hstack([Pt[:,0:1],Pt[:,2:3]]),JointCentY[j+1:j+2])
                        SectionPts = np.vstack([Pt2,[New_xz[0,0],JointCentY[j+1,0],New_xz[0,1]]]); 
                            
                    elif  AboveLower[k] and BelowUpper[k+1]:  # entire section is within the vertebra
                        # print(3)
                        #Muscle section doesn't cross joint positions, so
                        #use whole thing.
                        SectionPts = Pt
                                        
                    elif AboveLower[k] and BelowUpper[k] and AboveUpper[k+1]: #lower part of section within the vertebra
                        # print(4)
                        #Get global position where muscle section crosses upper joint
                        New_xz = interp1(Pt[:,1:2],np.hstack([Pt[:,0:1],Pt[:,2:3]]),JointCentY[j:j+1])
                        SectionPts = np.vstack([[New_xz[0,0],JointCentY[j,0],New_xz[0,1]], Pt1 ])
                                            
                    else: #none of the section is within the vertebra
                        continue
                                #calculate length and center of this
                    #section
                    # print(' k= ',k)
                    # print(SectionPts)
                    diff = SectionPts[1,:] - SectionPts[0,:]
                    # print('diff=', diff)
                    LengthInside[k] = np.linalg.norm(diff) #(np.sum((diff)**2))**0.5 L2 norm #length of muscle section within the vertebra
                    SectionCentersInside[k,:] = np.sum(SectionPts,axis=0)/2 #global center of this muscle section within the vertebra 

                #calculate CSA and moment arm at this vertebral level
                SectionVolumeInside = LengthInside*ACSA; #volumes of muscle section(s) within the vertebra
                TotalVolumeInside = np.sum(SectionVolumeInside)
                # print(' LengthInside = \n',LengthInside,'\n')
                #                 VertHeights(j)
                #                 CSA_LT
                CSA_MT[j] = TotalVolumeInside/VertHeights[j] #Average CSA estimated as volume / vertebral height.  
                if TotalVolumeInside > 0 :# only calculate moment arm if some muscle is present
                    TotalCentersInside = np.sum(SectionCentersInside * SectionVolumeInside,axis=0)/TotalVolumeInside #weighted center position of the muscles inside.
                    # print(SectionCentersInside)
                    # print(TotalVolumeInside)
                    # print(TotalCentersInside)
                    MomArms[j,:] = TotalCentersInside - CentPos[j,:]

            # ##
            # print('\n\n\nCSAMT\n\n\n',CSA_MT)
            # !! precision difference

            # ## [markdown]
            # ##### j for loop 2 end

            # ##
            MusclePresent_MT = CSA_MT > 0
            CSA_MT = CSA_MT.T
            X_MA_MT = MomArms[:,0:1].T
            Z_MA_MT = MomArms[:,2:3].T

            # ##
            ## Determine if muscle portion of MTU is present at each vertebral level, assuming tendon is at upper end of
            #musculotendon unit:
            TendonRemainder = TendonLength #Initialize how much tendon length there is.
            for j in range(NumCurrentPath-2,-1,-1): # NumCurrentPath-1:-1:1
                if TendonRemainder < PathLengths[j]: # the tendon ends in this section of the musculotendon unit
                    Pt1 = PtGlobal[j+1,:]
                    Pt2 = PtGlobal[j,:]
                    diff = Pt2-Pt1
                    sectionlength = np.linalg.norm(diff)
                    MTjunction = PtGlobal[j+1,:] + TendonRemainder/sectionlength*diff #location of switch from tendon to muscle in musculotendon unit
                    #Set the Muscle Section points
                    MuscleSection = np.vstack([PtGlobal[0:j+1,:],MTjunction])
                    break #once found, stop
                else: #the tendon hasn't ended yet
                    TendonRemainder = TendonRemainder - PathLengths[j]


            # ##
            ## Determine cross-sectional areas and angles of fascicle relative to axial direction (y)

            MusclePts_y = MuscleSection[:,1] #axial positions of muscle section endpoints.
            NumMuscleSections = len(MusclePts_y) - 1; # number of segments of muscle component  

            PCSA = Strength/100; # convert max isometric force to PCSA, using the MMS - orginal value of 100 N/cm2
            ACSA = PCSA*np.cos(Pennation); # calculate ACSA for fascicle

            MomArms = np.zeros((num_samples[loc],3))
            CSA_HT = np.zeros((num_samples[loc],1))

            # ## [markdown]
            # ##### j for loop 3

            # ##
            for j in range(num_samples[loc]): #do for T1 to L5 if vert centroid, or NEW: t1-head to L5-s1
                #print('j = ',j)
                AboveUpper = MusclePts_y > JointCentY[j] #are muscle section endpoints above the upper joint.
                BelowUpper = MusclePts_y <= JointCentY[j] #are muscle section endpoints at or below the upper joint.
                AboveLower = MusclePts_y >= JointCentY[j+1]  # are muscle section endpoints at or above the lower joint.
                BelowLower = MusclePts_y < JointCentY[j+1]  # are muscle section endpoints below the lower joint.
                LengthInside = np.zeros((NumMuscleSections,1)) #array for lengths of muscle sections within vertebra
                #                 SectionVolumeInside = zeros(NumMuscleSections); #array for volume of muscle within vertebra
                SectionCentersInside = np.zeros((NumMuscleSections,3)); #array for centers of muscle sections within

                for k in range(NumMuscleSections): #check if muscle sections are partly or fully within VB level
                    # get original muscle section points
                    Pt1 = MuscleSection[k] #low
                    Pt2 = MuscleSection[k+1] #high
                    Pt = np.vstack([Pt2, Pt1])
                    
                    if Pt1[1] > Pt2[1]: # Pt 1 is higher than Pt 2, change order of Pt.
                        Pt = np.vstack([Pt1, Pt2])

                    if BelowLower[k] and AboveUpper[k+1]: #muscle section completely spans the vertebra
                        #Get global position where muscle section crosses joint positions
                        New_xz = interp1(Pt[:,1:2],np.hstack([Pt[:,0:1],Pt[:,2:3]]),JointCentY[j:j+2])
                        SectionPts = np.hstack([New_xz[:,0:1],JointCentY[j:j+2],New_xz[:,1:2]]) 

                    elif BelowLower[k] and AboveLower[k+1] and BelowUpper[k+1]: # upper part of section within the vertebra
                        #Get global position where muscle section crosses lower joint
                        New_xz = interp1(Pt[:,1:2],np.hstack([Pt[:,0:1],Pt[:,2:3]]),JointCentY[j+1:j+2])
                        SectionPts = np.vstack([Pt2,[New_xz[0,0],JointCentY[j+1,0],New_xz[0,1]]]); 
                            
                    elif  AboveLower[k] and BelowUpper[k+1]:  # entire section is within the vertebra
                        #Muscle section doesn't cross joint positions, so
                        #use whole thing.
                        SectionPts = Pt
                                        
                    elif AboveLower[k] and BelowUpper[k] and AboveUpper[k+1]: #lower part of section within the vertebra
                        #Get global position where muscle section crosses upper joint
                        New_xz = interp1(Pt[:,1:2],np.hstack([Pt[:,0:1],Pt[:,2:3]]),JointCentY[j:j+1])
                        SectionPts = np.vstack([[New_xz[0,0],JointCentY[j,0],New_xz[0,1]], Pt1 ])
                                            
                    else: #none of the section is within the vertebra
                        continue
                                #calculate length and center of this
                    #section
                    #print(' k= ',k)
                    # print(SectionPts)
                    diff = SectionPts[1,:] - SectionPts[0,:]
                    #print('diff=', diff)
                    LengthInside[k] = np.linalg.norm(diff) #(np.sum((diff)**2))**0.5 L2 norm #length of muscle section within the vertebra
                    SectionCentersInside[k,:] = np.sum(SectionPts,axis=0)/2 #global center of this muscle section within the vertebra 

                #calculate CSA and moment arm at this vertebral level
                SectionVolumeInside = LengthInside*ACSA; #volumes of muscle section(s) within the vertebra
                TotalVolumeInside = np.sum(SectionVolumeInside)
                #print(' LengthInside = \n',LengthInside,'\n')
                #                 VertHeights(j)
                #                 CSA_LT
                CSA_HT[j] = TotalVolumeInside/VertHeights[j] #Average CSA estimated as volume / vertebral height.  
                if TotalVolumeInside > 0 :# only calculate moment arm if some muscle is present
                    TotalCentersInside = np.sum(SectionCentersInside * SectionVolumeInside,axis=0)/TotalVolumeInside #weighted center position of the muscles inside.
                    # print(SectionCentersInside)
                    # print(TotalVolumeInside)
                    # print(TotalCentersInside)
                    MomArms[j,:] = TotalCentersInside - CentPos[j,:]   

            # ## [markdown]
            # ##### j for loop 3 end

            MusclePresent_HT = CSA_HT > 0 
            CSA_HT = CSA_HT.T
            X_MA_HT = MomArms[:,0:1].T
            Z_MA_HT = MomArms[:,2:3].T

            # ##
            #MuscleParams.(MuscleGroupName)(m,:) = [Strength length TendonLength Pennation PCSA ACSA Angles 1*MTUPresent'];
            CSA_TL[MuscleGroupName].append(np.hstack([CSA_LT , 1*MusclePresent_LT.T]).squeeze()) 
            CSA_TM[MuscleGroupName].append(np.hstack([CSA_MT , 1*MusclePresent_MT.T]).squeeze())
            CSA_TH[MuscleGroupName].append(np.hstack([CSA_HT , 1*MusclePresent_HT.T]).squeeze())

            X_MA_TL[MuscleGroupName].append(np.hstack([X_MA_LT , 1*MusclePresent_LT.T]).squeeze())
            X_MA_TM[MuscleGroupName].append(np.hstack([X_MA_MT , 1*MusclePresent_MT.T]).squeeze())
            X_MA_TH[MuscleGroupName].append(np.hstack([X_MA_HT , 1*MusclePresent_HT.T]).squeeze())

            Z_MA_TL[MuscleGroupName].append(np.hstack([Z_MA_LT , 1*MusclePresent_LT.T]).squeeze())
            Z_MA_TM[MuscleGroupName].append(np.hstack([Z_MA_MT , 1*MusclePresent_MT.T]).squeeze())
            Z_MA_TH[MuscleGroupName].append(np.hstack([Z_MA_HT , 1*MusclePresent_HT.T]).squeeze())

            # ## [markdown]
            # #### m for loop end

        # ##
        CSA_TL[MuscleGroupName] = np.array(CSA_TL[MuscleGroupName])
        CSA_TM[MuscleGroupName] = np.array(CSA_TM[MuscleGroupName])
        CSA_TH[MuscleGroupName] = np.array(CSA_TH[MuscleGroupName])

        X_MA_TL[MuscleGroupName] = np.array(X_MA_TL[MuscleGroupName])
        X_MA_TM[MuscleGroupName] = np.array(X_MA_TM[MuscleGroupName])
        X_MA_TH[MuscleGroupName] = np.array(X_MA_TH[MuscleGroupName])

        Z_MA_TL[MuscleGroupName] = np.array(Z_MA_TL[MuscleGroupName])
        Z_MA_TM[MuscleGroupName] = np.array(Z_MA_TM[MuscleGroupName])
        Z_MA_TH[MuscleGroupName] = np.array(Z_MA_TH[MuscleGroupName])

        # ##
        #Sum the CSAs for each group:
        GroupCSA_TL.append(np.sum(CSA_TL[MuscleGroupName][:,:num_samples[loc]], axis = 0))
        GroupCSA_TM.append(np.sum(CSA_TM[MuscleGroupName][:,:num_samples[loc]], axis = 0))
        GroupCSA_TH.append(np.sum(CSA_TH[MuscleGroupName][:,:num_samples[loc]], axis = 0))

        # ## [markdown]
        # ### g for loop end

    GroupCSA_TL = np.array(GroupCSA_TL)
    GroupCSA_TM = np.array(GroupCSA_TM)
    GroupCSA_TH = np.array(GroupCSA_TH)
    # ##
    #Find muscle group center of area at each level
    Group_Z_MA_TL = np.zeros((11,num_samples[loc]))
    Group_Z_MA_TM = np.zeros((11,num_samples[loc]))
    Group_Z_MA_TH = np.zeros((11,num_samples[loc]))
    Group_X_MA_TL = np.zeros((11,num_samples[loc]))
    Group_X_MA_TM = np.zeros((11,num_samples[loc]))
    Group_X_MA_TH = np.zeros((11,num_samples[loc]))


    # ##
    for l in range(num_samples[loc]): #for each level updated to 14 (T4)
        for g in range(11):#for each muscle group
            NumerZ_TL=0
            NumerZ_TM=0
            NumerZ_TH=0
            NumerX_TL=0
            NumerX_TM=0
            NumerX_TH=0
            tempArea_TL = 0
            tempArea_TM = 0
            tempArea_TH = 0
            for m in range(Z_MA_TM[MuscleGroupNamesArray[g]].shape[0]): #go through the fascicles
                if Z_MA_TL[MuscleGroupNamesArray[g]][m,l] > 0:#right side muscle fascicle
                    NumerZ_TL = NumerZ_TL + Z_MA_TL[MuscleGroupNamesArray[g]][m,l]*CSA_TL[MuscleGroupNamesArray[g]][m,l]
                    NumerX_TL = NumerX_TL + X_MA_TL[MuscleGroupNamesArray[g]][m,l]*CSA_TL[MuscleGroupNamesArray[g]][m,l]
                    tempArea_TL = tempArea_TL + CSA_TL[MuscleGroupNamesArray[g]][m,l]
                
                if Z_MA_TM[MuscleGroupNamesArray[g]][m,l] > 0: #right side muscle fascicle
                    NumerZ_TM = NumerZ_TM + Z_MA_TM[MuscleGroupNamesArray[g]][m,l]*CSA_TM[MuscleGroupNamesArray[g]][m,l]
                    NumerX_TM = NumerX_TM + X_MA_TM[MuscleGroupNamesArray[g]][m,l]*CSA_TM[MuscleGroupNamesArray[g]][m,l]
                    tempArea_TM = tempArea_TM + CSA_TM[MuscleGroupNamesArray[g]][m,l]

                if Z_MA_TH[MuscleGroupNamesArray[g]][m,l] > 0: #right side muscle fascicle
                    NumerZ_TH = NumerZ_TH + Z_MA_TH[MuscleGroupNamesArray[g]][m,l]*CSA_TH[MuscleGroupNamesArray[g]][m,l]
                    NumerX_TH = NumerX_TH + X_MA_TH[MuscleGroupNamesArray[g]][m,l]*CSA_TH[MuscleGroupNamesArray[g]][m,l]
                    tempArea_TH = tempArea_TH + CSA_TH[MuscleGroupNamesArray[g]][m,l]

            Group_Z_MA_TL[g,l] = (NumerZ_TL/tempArea_TL)*100 if tempArea_TL != 0 else np.nan 
            Group_X_MA_TL[g,l] = (NumerX_TL/tempArea_TL)*100 if tempArea_TL != 0 else np.nan 
            Group_Z_MA_TM[g,l] = (NumerZ_TM/tempArea_TM)*100 if tempArea_TM != 0 else np.nan 
            Group_X_MA_TM[g,l] = (NumerX_TM/tempArea_TM)*100 if tempArea_TM != 0 else np.nan 
            Group_Z_MA_TH[g,l] = (NumerZ_TH/tempArea_TH)*100 if tempArea_TH != 0 else np.nan 
            Group_X_MA_TH[g,l] = (NumerX_TH/tempArea_TH)*100 if tempArea_TH != 0 else np.nan 



        GroupCSA_info[struct_strings[loc]] = np.zeros((11,GroupCSA_TL.shape[1]))
        GroupCSA_info[struct_strings[loc]][[1,7,8,9],:] =  GroupCSA_TL[[1,7,8,9],:]
        GroupCSA_info[struct_strings[loc]][[0,2,3,4,5],:] =  GroupCSA_TM[[0,2,3,4,5],:]
        GroupCSA_info[struct_strings[loc]][[6,10],:] =  GroupCSA_TH[[6,10],:]
        GroupCSA_info['TL'] = GroupCSA_TL
        GroupCSA_info['TM'] = GroupCSA_TM
        GroupCSA_info['TH'] = GroupCSA_TH

        GroupMAX_info[struct_strings[loc]] = np.zeros((11,Group_X_MA_TL.shape[1]))
        GroupMAX_info[struct_strings[loc]][[1,7,8,9],:] =  Group_X_MA_TL[[1,7,8,9],:]
        GroupMAX_info[struct_strings[loc]][[0,2,3,4,5],:] =  Group_X_MA_TM[[0,2,3,4,5],:]
        GroupMAX_info[struct_strings[loc]][[6,10],:] =  Group_X_MA_TH[[6,10],:]
        GroupMAX_info['TL'] = Group_X_MA_TL
        GroupMAX_info['TM'] = Group_X_MA_TM
        GroupMAX_info['TH'] = Group_X_MA_TH


        GroupMAZ_info[struct_strings[loc]] = np.zeros((11,Group_Z_MA_TL.shape[1]))
        GroupMAZ_info[struct_strings[loc]][[1,7,8,9],:] =  Group_Z_MA_TL[[1,7,8,9],:]
        GroupMAZ_info[struct_strings[loc]][[0,2,3,4,5],:] =  Group_Z_MA_TM[[0,2,3,4,5],:]
        GroupMAZ_info[struct_strings[loc]][[6,10],:] =  Group_Z_MA_TH[[6,10],:]
        GroupMAZ_info['TL'] = Group_Z_MA_TL
        GroupMAZ_info['TM'] = Group_Z_MA_TM
        GroupMAZ_info['TH'] = Group_Z_MA_TH


        FascicleCSA_info[struct_strings[loc]] = {}
        FascicleCSA_info[struct_strings[loc]]['Pectoralis'] = CSA_TM['Pectoralis']
        FascicleCSA_info[struct_strings[loc]]['Rectus_Abdominus'] = CSA_TL['Rectus_Abdominus']
        FascicleCSA_info[struct_strings[loc]]['Serratus_Anterior'] = CSA_TM['Serratus_Anterior']
        FascicleCSA_info[struct_strings[loc]]['Latissimus_Dorsi'] = CSA_TM['Latissimus_Dorsi']
        FascicleCSA_info[struct_strings[loc]]['Trapezius'] = CSA_TM['Trapezius']
        FascicleCSA_info[struct_strings[loc]]['External_Oblique'] = CSA_TM['External_Oblique']
        FascicleCSA_info[struct_strings[loc]]['Internal_Oblique'] = CSA_TH['Internal_Oblique']
        FascicleCSA_info[struct_strings[loc]]['SacroSpinalis'] = CSA_TL['SacroSpinalis']
        FascicleCSA_info[struct_strings[loc]]['TransversoSpinalis'] = CSA_TL['TransversoSpinalis']
        FascicleCSA_info[struct_strings[loc]]['Psoas_Major'] = CSA_TL['Psoas_Major']
        FascicleCSA_info[struct_strings[loc]]['Quadratus_Laborum'] = CSA_TH['Quadratus_Laborum']
        FascicleCSA_info['TL'] = CSA_TL
        FascicleCSA_info['TH'] = CSA_TH
        FascicleCSA_info['TM'] = CSA_TM

        FascicleMAX_info[struct_strings[loc]] = {}
        FascicleMAX_info[struct_strings[loc]]['Pectoralis'] = X_MA_TM['Pectoralis']
        FascicleMAX_info[struct_strings[loc]]['Rectus_Abdominus'] = X_MA_TL['Rectus_Abdominus']
        FascicleMAX_info[struct_strings[loc]]['Serratus_Anterior'] = X_MA_TM['Serratus_Anterior']
        FascicleMAX_info[struct_strings[loc]]['Latissimus_Dorsi'] = X_MA_TM['Latissimus_Dorsi']
        FascicleMAX_info[struct_strings[loc]]['Trapezius'] = X_MA_TM['Trapezius']
        FascicleMAX_info[struct_strings[loc]]['External_Oblique'] = X_MA_TM['External_Oblique']
        FascicleMAX_info[struct_strings[loc]]['Internal_Oblique'] = X_MA_TH['Internal_Oblique']
        FascicleMAX_info[struct_strings[loc]]['SacroSpinalis'] = X_MA_TL['SacroSpinalis']
        FascicleMAX_info[struct_strings[loc]]['TransversoSpinalis'] = X_MA_TL['TransversoSpinalis']
        FascicleMAX_info[struct_strings[loc]]['Psoas_Major'] = X_MA_TL['Psoas_Major']
        FascicleMAX_info[struct_strings[loc]]['Quadratus_Laborum'] = X_MA_TH['Quadratus_Laborum']
        FascicleMAX_info['TL'] = X_MA_TL
        FascicleMAX_info['TH'] = X_MA_TH
        FascicleMAX_info['TM'] = X_MA_TM

        FascicleMAZ_info[struct_strings[loc]] = {}
        FascicleMAZ_info[struct_strings[loc]]['Pectoralis'] = Z_MA_TM['Pectoralis']
        FascicleMAZ_info[struct_strings[loc]]['Rectus_Abdominus'] = Z_MA_TL['Rectus_Abdominus']
        FascicleMAZ_info[struct_strings[loc]]['Serratus_Anterior'] = Z_MA_TM['Serratus_Anterior']
        FascicleMAZ_info[struct_strings[loc]]['Latissimus_Dorsi'] = Z_MA_TM['Latissimus_Dorsi']
        FascicleMAZ_info[struct_strings[loc]]['Trapezius'] = Z_MA_TM['Trapezius']
        FascicleMAZ_info[struct_strings[loc]]['External_Oblique'] = Z_MA_TM['External_Oblique']
        FascicleMAZ_info[struct_strings[loc]]['Internal_Oblique'] = Z_MA_TH['Internal_Oblique']
        FascicleMAZ_info[struct_strings[loc]]['SacroSpinalis'] = Z_MA_TL['SacroSpinalis']
        FascicleMAZ_info[struct_strings[loc]]['TransversoSpinalis'] = Z_MA_TL['TransversoSpinalis']
        FascicleMAZ_info[struct_strings[loc]]['Psoas_Major'] = Z_MA_TL['Psoas_Major']
        FascicleMAZ_info[struct_strings[loc]]['Quadratus_Laborum'] = Z_MA_TH['Quadratus_Laborum']
        FascicleMAX_info['TL'] = Z_MA_TL
        FascicleMAX_info['TH'] = Z_MA_TH
        FascicleMAX_info['TM'] = Z_MA_TM

        # import json
        # # Custom JSON encoder
        # class NumpyEncoder(json.JSONEncoder):
        #     def default(self, obj):
        #         if isinstance(obj, np.ndarray):
        #             return obj.tolist()  # Convert ndarray to list
        #         return super(NumpyEncoder, self).default(obj)
        
        # output = [GroupCSA_info, GroupMAX_info, GroupMAZ_info,
        # FascicleCSA_info, FascicleMAX_info, FascicleMAZ_info,
        # VertCentY, VertCent, JointCent]
        # output_name = ['GroupCSA_info',' GroupMAX_info',' GroupMAZ_info',
        #             'FascicleCSA_info',' FascicleMAX_info',' FascicleMAZ_info',
        #             'VertCentY',' VertCent',' JointCent']
        # for v in range(len(output)):
        #     with open("./Scaled_Muscle/"+output_name[v]+".json", "w") as outfile:
        #         json.dump(output[v], outfile,cls=NumpyEncoder,sort_keys=True,indent=4)

    output = (GroupCSA_info, GroupMAX_info, GroupMAZ_info,
    FascicleCSA_info, FascicleMAX_info, FascicleMAZ_info,
    VertCentY, VertCent, JointCent)
    return output


# %%
def ScaleMuscleMarkerModel(BaseModel, SubjectID, muscledataCSA, muscledataMAX, muscledataMAZ,scaled_model_path):
    """
    Scales muscles of the model based on provided muscle CSA and moment arm data. Saves the scaled model to a specified path.

    The function scales the muscle marker model based on provided muscle data. It adjusts the cross-sectional area, 
    moment arms of the muscles on each vertebra level based on the input data. The function then saves the scaled model to the specified 
    path and returns the path to the newly scaled model.

    :param BaseModel: Path to the base model file.
    :type BaseModel: str

    :param SubjectID: Identifier for the subject.
    :type SubjectID: str

    :param muscledataCSA: Muscle cross-sectional area data.
    :type muscledataCSA: 2D ndarray

    :param muscledataMAX: Muscle MA_X data.
    :type muscledataMAX: 2D ndarray

    :param muscledataMAZ: Muscle MA_Z data.
    :type muscledataMAZ: 2D ndarray

    :param scaled_model_path: Path to save the scaled model.
    :type scaled_model_path: str

    :return: Path to the newly scaled model.
    :rtype: str
    """    
    muscleinput_CSA = muscledataCSA
    muscleinput_MAX = muscledataMAZ
    muscleinput_MAY = muscledataMAX
    outputfilepath = os.path.dirname(BaseModel)

    
    #Muscle params from regression
    CSA_AveMeasured = muscleinput_CSA*2
    MAX_AveMeasured = muscleinput_MAY
    MAZ_AveMeasured = muscleinput_MAX

    
    # for iter_num in range(1,2):
    iter_num = 1 #1 iteration of scaling for this function

    modelpath = BaseModel
    myModel = osim.Model(modelpath) #load the model
    print('model_path = ', modelpath)
    state = myModel.initSystem() #initialize the model; get model state
    myModel.equilibrateMuscles(state) # Make sure the muscles states are in equilibrium
    myBodies = myModel.getBodySet() #get body set

    
    # ## Evaluate Muscle All levels

    
    preCSA_info, preMAX_info, preMAZ_info,preFascicleCSA_info, preFascicleMAX_info, preFascicleMAZ_info,VertCentY, VertCent, JointCent = Evaluate_Muscle_AllLevels_v3_EOTM(modelpath);

    
    # ## for g loop

    
    for g in range(11):

    
    # ### if iter_num > 1    continue else
        if iter_num >1:
            continue
        else:

            MuscleNames = []

            
            MuscleGroup = myModel.getForceSet().getGroup(g)
            MuscleGroupName = myModel.getForceSet().getGroup(g).getName()
            FascicleNames = MuscleGroup.getMembers()
            NumFascicles = FascicleNames.getSize()
            MuscleNames.append(MuscleGroupName)

            
            #Measured - group params
            CSA_meas = CSA_AveMeasured[g,:17]  #group CSA at T1 through L5
            MAX_meas = MAX_AveMeasured[g,:17]  #group MA_X at T1 through L5
            MAZ_meas = MAZ_AveMeasured[g,:17]  #group MA_Z at T1 through L5

            #Size Scaled Model - group params
            CSA_L_0 = preCSA_info['VertCent'][g,:17]  #group CSA at T1 through L5
            MAX_L_0 = preMAX_info['VertCent'][g,:17] #group MA_X at T1 through L5
            MAZ_L_0 = preMAZ_info['VertCent'][g,:17]   #group MA_Z at T1 through L5

            #levels that are not measured or not present will be ignored
            Levels_present = np.where((CSA_meas > 0) & (CSA_meas < 9999) & (CSA_L_0 > 0))[0]

        
            # #### if isempty(Levels_present) == 1 continue
            if np.where(Levels_present)[0].size != 0:

                ## Adjust CSA of size scaled subject model
                #Size Scaled Model - fascicle
                CSA_f_0 =  preFascicleCSA_info['VertCent'][MuscleGroupName][:,0:17]  #fascicle CSA at T1 through L5
                MAX_f_0 =  preFascicleMAX_info['VertCent'][MuscleGroupName][:,0:17]  #fascicle MA_X at T1 through L5
                MAZ_f_0 =  preFascicleMAZ_info['VertCent'][MuscleGroupName][:,0:17]  #fascicle MA_Z at T1 through L5

                #Whether fascicle is present at a given level
                Muscle_Present = preFascicleCSA_info['VertCent'][MuscleGroupName][:,17:34] #updated from 13:24 CHECK THIS TO SEE IF NEEDS UPDATING

                
                Muscle_Present.shape

                
                np.seterr(divide='ignore',invalid='ignore')

                Ratio_L = CSA_meas / CSA_L_0 #Ratios of measured group CSA to model group CSA
                #CSA_L_0 may include 0
                # nan for 0/0 and inf for non-zero values divided by 0

                Diff_L_MAX = MAX_meas - MAX_L_0 #Differences of measured group MAX to model group MAX
                Diff_L_MAZ = MAZ_meas - MAZ_L_0 #Differences of measured group MAZ to model group MAZ

                #Model 2B (MomentOnly) Removed this Section

                CSA_f_1 = np.zeros((NumFascicles,max(12,Levels_present.max()+1))) #fascicle area at each level calculated from ratio at each level
                CSA_f_2 = np.zeros((NumFascicles,1)) #average fascicle area across levels (since each fascicle can only have one area)

                CSA_original_average = np.zeros((NumFascicles,1))
                CSA_ratio = np.zeros((NumFascicles,1))

                
                for f in range(NumFascicles): #for each fascicle in the group
                    
                    CSA_f_1[f,Levels_present] = CSA_f_0[f,Levels_present]*Ratio_L[Levels_present]#Calculate fascicle CSA at each level
                    L = np.sum(Muscle_Present[f,Levels_present]) #Number of levels where it's present
                    
                    if L>0:
                        CSA_f_2[f] = np.sum(CSA_f_1[f,Levels_present])/L #average across levels to get new CSA of the fascicle
                        CSA_original_average[f] = np.sum(CSA_f_0[f,Levels_present])/L #Average in original model
                        CSA_ratio[f] = CSA_f_2[f]/CSA_original_average[f]

                
                #For fascicles that were not present at the levels where CT
                #measurements were available, use the average ratio for the other
                #fascicles in the group
                CSA_ratio_nonzero = np.where(CSA_ratio > 0)[0]
                CSA_ratio_zero = np.where(CSA_ratio == 0)
                CSA_ratio_mean = np.mean(CSA_ratio[CSA_ratio_nonzero])
                CSA_ratio[CSA_ratio_zero] = CSA_ratio_mean

                
                #m=1;
                for m in range(NumFascicles): #for each fascicle in the group
                    CurrentFasName = FascicleNames.get(m).getName()
                    aMuscle = myModel.getMuscles().get(CurrentFasName)#The muscle fascicle
                    OriginalStrength = aMuscle.getMaxIsometricForce() #Get max muscle strength
                    NewStrength = OriginalStrength*CSA_ratio[m,0] #Calculate new strength
                    aMuscle.setMaxIsometricForce(NewStrength) #Set new strength
                    # print('FasName = ', CurrentFasName)
                    # print('CSA_ratio = ',CSA_ratio,'m = ',m)
                    # print('OriginalStrength = ',OriginalStrength,'NewStrength = ',NewStrength,'\n')

                    
                    # ##### if g == 2 || g==4 || g == 5 || g==7 || g == 8 || g == 9 || g == 10 || g == 11

                    
                    # if g in [1,3,4,6,7,8,9,10]:

            
                # ##### if iter_num <= 1
                if (iter_num <=1) and (g in [1,3,4,6,7,8,9,10]):
                    
                    count=0
                    temparray = []
                    f=0
                    OriginalLength = np.zeros((1,NumFascicles))

                    
                        # ###### for f = 1:NumFascicles
                    for f in range(NumFascicles):
                        
                        #Get the current muscle path from Geometry Path
                        CurrentFasName = FascicleNames.get(f).getName()
                        aMuscle = myModel.getMuscles().get(CurrentFasName) #the muscle fascicle
                        aMuscleGeometry = aMuscle.getGeometryPath()
                        aCurrentPath = aMuscleGeometry.getCurrentPath(state)
                        NumCurrentPath = aCurrentPath.getSize() #number of path points
                        OriginalLength[0,f] = aMuscle.getLength(state) #Get fascicle length
                        #Get global position of each path point
                        PtGlobal = np.zeros((NumCurrentPath,3))

                        
                        for i in range(NumCurrentPath):
                            PtBody = aCurrentPath.getitem(i).getBody().getName() #body the point is in
                            globalPos = osim.ArrayDouble.createVec3(0.0,0.0,0.0)
                            myModel.getSimbodyEngine().transformPosition(state, myBodies.get(PtBody),aCurrentPath.getitem(i).getLocation(state),myModel.getGround(), globalPos)
                            PtGlobal[i,:] = [osim.ArrayDouble.getValuesFromVec3(globalPos).get(j) for j in range(3)]#array of locations in global coordinates
                    

                        
                        #i=3;
                        for i in range(NumCurrentPath): #Go through all pathpoints in a fascicle
                            #print('i= ' ,i)
                            temp = (MAX_meas != 0) & (MAX_meas != 9999) & (~np.isnan(MAX_L_0)) #find levels with measured data
                            #                                 temp = ~isnan(MAX_L_0); #find levels with model estimates
                            indices = np.where(temp)[0] #find indices for levels with measured data
                            indexHigh = np.min(indices) #Highest level with measured data
                            indexLow = np.max(indices)  #Lowest level with measured data
                            
                            #Restrict movement of some
                            #fascicles at the endpoints. This may help keep the muscles from "blowing up"
                            if ((g == 4) or (g == 3)) and ((i == 0) or (i == (NumCurrentPath - 1))):
                                #print(1)
                                # do nothing for the endpoints of trapezius paths
                                #                     elseif (g == 1) && (i == 0)
                                #                         # do nothing for the humerus endpoint of pectoralis  paths
                                #                     elseif (g==3) && (i== NumCurrentPath - 1)
                                #                         # do nothing for the scapula endpoint of SA paths
                                pass
                            
                                #if pathpoint is between the levels for which we have measured data
                            elif (PtGlobal[i,1] > VertCentY[indexLow,0]) and (PtGlobal[i,1] < VertCentY[indexHigh,0]):
                                #print(2)
                                #find levels that pathpoint is between
                                bb = np.argmin(np.abs(VertCentY-PtGlobal[i,1])) #what vert level is it closest to
                                cc = np.min(np.abs(indices-bb))
                                dd = np.argmin(np.abs(indices-bb))  #what is the closest level with measured data
                                index1 = indices[dd] #what is the closest level with measured data
                                # print('bb = \n',bb)
                                # print('cc = \n',cc)
                                # print('dd = \n',dd)
                                if PtGlobal[i,1] > VertCentY[index1,0]:
                                    index2 = indices[dd-1]
                                else:
                                    index2 = indices[dd+1]
                                
                                #interpolate to find difference of model to measured MAX and
                                #MAZ at y-level of pathpoint
                                X = np.vstack([VertCent[index1,1] ,VertCent[index2,1]]) #y-position of vertebrae spanning pathpoint
                                Y1 = np.vstack([Diff_L_MAX[index1], Diff_L_MAX[index2]]) #MAX diff of vertebrae spanning pathpoint
                                Y2 = np.vstack([Diff_L_MAZ[index1], Diff_L_MAZ[index2]]) #MAZ diff of vertebrae spanning pathpoint
                                        
                                # print('X = \n',X)
                                # print('Y1 = \n',Y1)
                                # print('Y2 = \n',Y2)
                                # print('PtGlobal = \n',PtGlobal)

                                newDiff_L_MAX = interp1(X,Y1,PtGlobal[i:i+1,1:2]) #Interpolated MAX diff at level of pathpoint
                                newDiff_L_MAZ = interp1(X,Y2,PtGlobal[i:i+1,1:2]) #Interpolated MAZ diff at level of pathpoint
                                
                                New_X_pathpt = PtGlobal[i,0] + newDiff_L_MAX/100; #Get new X position of pathpoint
                                
                                Isleft = PtGlobal[:,2] < 0
                                Isleft2  = np.where(Isleft)[0]
                                
                                if Isleft2.size > 0: #if a left side fascicle
                                    New_Z_pathpt = PtGlobal[i,2]-newDiff_L_MAZ/100 #Get new Z position of pathpoint
                                else: #if a right side fascicle
                                    New_Z_pathpt = PtGlobal[i,2]+newDiff_L_MAZ/100 #Get new Z position of pathpoint
                                
                                #print([New_X_pathpt,PtGlobal[i,1],New_Z_pathpt,newDiff_L_MAX,newDiff_L_MAZ])
                                temparray.append(np.hstack([New_X_pathpt,PtGlobal[i:i+1,1:2],New_Z_pathpt,newDiff_L_MAX,newDiff_L_MAZ]).squeeze())
                                count += 1
                                
                                PtBody = aCurrentPath.getitem(i).getBody().getName() #Body the point is in
                                newglobalPos = osim.ArrayDouble.createVec3(New_X_pathpt[0,0],PtGlobal[i,1],New_Z_pathpt[0,0]) #X Y Z global position of pathpoint
                                newlocalPos = osim.ArrayDouble.createVec3(0.0,0.0,0.0)
                                myModel.getSimbodyEngine().transformPosition(state, myModel.getGround(), newglobalPos, myBodies.get(PtBody), newlocalPos)
                                p = osim.PathPoint.safeDownCast(aCurrentPath.getitem(i))
                                p.setLocation(newlocalPos)
                                # print('newlocalPos2 = ',newlocalPos)
                                #if pathpoint is higher or lower than the
                                #measured data range, use the nearest neighbor
                                #difference
                            elif PtGlobal[i,1] > VertCentY[indexHigh,0] or  PtGlobal[i,1] < VertCentY[indexLow,0]:
                                #print(3)
                                #take average of neigbors
                                #newDiff_L_MAX = (Diff_L_MAX(indices(1)) + Diff_L_MAX(indices(2)) + Diff_L_MAX(indices(3)))/3;
                                #newDiff_L_MAZ = (Diff_L_MAZ(indices(1)) + Diff_L_MAZ(indices(2)) + Diff_L_MAZ(indices(3)))/3;
                                
                                #use nearest neighbor
                                if PtGlobal[i,1] > VertCentY[indexHigh,0]:
                                    newDiff_L_MAX = Diff_L_MAX[indices[0]]
                                    newDiff_L_MAZ = Diff_L_MAZ[indices[0]]
                                else:
                                    newDiff_L_MAX = Diff_L_MAX[indices[-1]]
                                    newDiff_L_MAZ = Diff_L_MAZ[indices[-1]]
                                
                                #could also extrapolate, but unsure if this
                                #will be accurate;  nearest neighbor approach
                                #is most conservative
                                
                                New_X_pathpt = PtGlobal[i,0] + newDiff_L_MAX/100 #Get new X position of pathpoint
                                
                                Isleft = PtGlobal[:,2] < 0
                                Isleft2  = np.where(Isleft)[0]
                                
                                if Isleft2.size>0 :#if a left side fascicle
                                    New_Z_pathpt = PtGlobal[i,2]-newDiff_L_MAZ/100; #Get new Z position of pathpoint
                                else :#if a right side fascicle
                                    New_Z_pathpt = PtGlobal[i,2]+newDiff_L_MAZ/100; #Get new Z position of pathpoint
                                
                                PtBody = aCurrentPath.getitem(i).getBody().getName() #Body the point is in
                                newglobalPos = osim.ArrayDouble.createVec3(New_X_pathpt,PtGlobal[i,1],New_Z_pathpt) #X Y Z global position of pathpoint
                                newlocalPos = osim.ArrayDouble.createVec3(0.0,0.0,0.0)
                                myModel.getSimbodyEngine().transformPosition(state, myModel.getGround(), newglobalPos, myBodies.get(PtBody), newlocalPos)
                                p = osim.PathPoint.safeDownCast(aCurrentPath.getitem(i))
                                p.setLocation(newlocalPos)
                                # print('newlocalPos3 = ',newlocalPos)

                        


                        
                        # ###### for f = 1:NumFascicles end
                    
                    # print('OriginalLength = \n',OriginalLength)

                    
                    ## After moment arm adjustments, recalculate the muscle properties for any change in length...
                    state = myModel.initSystem() #initialize the model; get model state
                    myModel.equilibrateMuscles(state) # Make sure the muscles states are in equilibrium
                    for m in range(NumFascicles): #for each fascicle in the group
                        CurrentFasName = FascicleNames.get(m).getName()
                        aMuscle = myModel.getMuscles().get(CurrentFasName) #the muscle fascicle
                        NewLength = aMuscle.getLength(state) #Get fascicle length
                        ConstantTendon = aMuscle.getTendonSlackLength()
                        OptimalFiber = aMuscle.getOptimalFiberLength()
                        aMuscle.setOptimalFiberLength(OptimalFiber*NewLength/OriginalLength[0,m])# Optimal fiber length
                        aMuscle.setTendonSlackLength(ConstantTendon*NewLength/OriginalLength[0,m]) # Tendon slack length

                        # print('CurrentFasName = ',CurrentFasName)
                        # print('NewLength = ',NewLength)
                        # print('ConstantTendon = ',ConstantTendon)
                        # print('OptimalFiber = ',OptimalFiber)
                        # print('OptimalFiberLength = ',OptimalFiber*NewLength/OriginalLength[0,m])
                        # print('TendonSlackLength = ',ConstantTendon*NewLength/OriginalLength[0,m])
                        
                        # print('\n')


                    # ##### if iter_num <= 1 end

                # ##### if g == 2 || g==4 || g == 5 || g==7 || g == 8 || g == 9 || g == 10 || g == 11 end

            # #### if isempty(Levels_present) else end
        # ### if iter_num > 1 else end

    # ## for g loop end

    ## hide muscles for reviewing!
    nMuscles = myModel.getMuscles().getSize()
    for i in range(nMuscles):
        mus = myModel.getMuscles().get(i)
        mus.getGeometryPath().upd_Appearance().set_visible(True)
    
    Newmodelpath = scaled_model_path#os.path.join(outputfilepath , str(SubjectID) + '_FullyScaled.osim') # UPDATE name
    myModel.printToXML(Newmodelpath)

    # 
    # Newmodelpath = 'C:/Users/hhuang10/Documents/MATLAB/OpenSim4/result/13560/13560_FullyScaled_matlab2.osim'

    # 
    # postCSA_info, postMAX_info, postMAZ_info,postFascicleCSA_info, postFascicleMAX_info, postFascicleMAZ_info,VertCentY, VertCent,JointCent = Evaluate_Muscle_AllLevels_v3_EOTM(Newmodelpath)

    # output = (postCSA_info, postMAX_info, postMAZ_info,postFascicleCSA_info, postFascicleMAX_info, postFascicleMAZ_info,VertCentY, VertCent,JointCent, Newmodelpath)
    # return output
    return Newmodelpath

# %% [markdown]
# # ScaleMuscleProperties

# %%
def ScaleMuscleProperties(NewModel, BaseModel, AddName):
    """
    Scales the muscle properties of the model.

    The function scales the muscle properties of the new OpenSim model based on the properties of a baseline model.
    It adjusts the fiber length, tendon slack length, and optimal fiber length of the muscles in the new model 
    based on the ratios derived from the baseline model. The function then saves the scaled model with the updated 
    muscle properties to a specified path and returns the path to the newly scaled model.

    :param NewModel: Path to the new OpenSim model file.
    :type NewModel: str

    :param BaseModel: Path to the baseline OpenSim model file.
    :type BaseModel: str

    :param AddName: Additional name to append to the scaled model's filename.
    :type AddName: str

    :return: Path to the scaled model with updated muscle properties.
    :rtype: str
    """
    ## get baseline properties
    osimModel = osim.Model(BaseModel)

    state = osimModel.initSystem() #initialize the model; get model state

    osimModel.equilibrateMuscles(state) # Make sure the muscles states are in equilibrium     
    osimModel.realizePosition(state)  #some where where it said to do this?     

    muscles = osimModel.getMuscles() 
    nMuscles = muscles.getSize()  

    BaseMTA_TlenR = np.zeros(nMuscles)
    BaseMTA_FlenR = np.zeros(nMuscles)
    BaseMTA_TSlenR = np.zeros(nMuscles)
    BaseMTA_OFlenR = np.zeros(nMuscles)

    for i in range(nMuscles):
        mus = osimModel.getMuscles().get(i)
        mus = osim.Millard2012EquilibriumMuscle.safeDownCast(mus)
            
        BaseMTA_len   = mus.getLength(state)
        #BaseMTA_TlenR(i+1)  = mus.getTendonLength(state) / BaseMTA_len;
        BaseMTA_FlenR[i]  = mus.getFiberLength(state) / BaseMTA_len
        BaseMTA_TSlenR[i] = mus.getTendonSlackLength() / BaseMTA_len
        BaseMTA_OFlenR[i] = mus.getOptimalFiberLength() / BaseMTA_len

    ## get baseline properties
    osimModel = osim.Model(NewModel)

    state = osimModel.initSystem() #initialize the model; get model state

    osimModel.equilibrateMuscles(state) # Make sure the muscles states are in equilibrium     
    osimModel.realizePosition(state)  #some where where it said to do this?     

    muscles = osimModel.getMuscles() 
    nMuscles = muscles.getSize()  

    for i in range(nMuscles):
        mus = osimModel.getMuscles().get(i)
        mus = osim.Millard2012EquilibriumMuscle.safeDownCast(mus)
        
        NewMTA_len = mus.getLength(state)

            
        #Note: by changing Fiber length you change Tendon length            
        mus.setFiberLength(state,BaseMTA_FlenR[i] * NewMTA_len)
        mus.setTendonSlackLength(BaseMTA_TSlenR[i] * NewMTA_len)
        mus.setOptimalFiberLength(BaseMTA_OFlenR[i] * NewMTA_len)

    ## Write the model to a file
    path = os.path.dirname(NewModel)
    fname = os.path.basename(NewModel).split('.')[0]
    nName = fname + AddName
    osimModel.setName(nName) 
    ScaledModel = os.path.join(path , nName + '.osim') # UPDATE name       
    osimModel.printToXML(ScaledModel)

    return ScaledModel

# %% [markdown]
# # Change_MTA_Act

# %%
def Change_MTA_Act(modelfile, setMax):
    """
    Modifies the maximum control value of all muscles in the model.
    
    The function updates the maximum control value of all muscles in the provided OpenSim model to the specified value.
    After updating the muscle properties, the model is saved back to its original path.

    :param modelfile: Path to the OpenSim model file.
    :type modelfile: str

    :param setMax: The new maximum control value to set for all muscles.
    :type setMax: float or int

    """
# clear all;
# clc;
# StrSubj = 'AW019';
# patient_directory_path   = ['C:\Users\jbanks3\Desktop\DoD_Harvard\Data\' StrSubj '\']; 
# modelfile       = [patient_directory_path StrSubj '_FullyScaled_ExoFit_4DoF.osim'];   #'AW019_FullyScaled_ExoFit_4DoF'
# setMax = 5;
    print('** Changing MTA max control to ' + str(setMax) +' **')

    model = osim.Model(modelfile)
    model.initSystem()

    nMus =  model.getMuscles().getSize()
    for m in range(nMus):
        M = model.getMuscles().get(m)
        M.setMaxControl(setMax)

        
    model.initSystem()       
    Gmodelfile = modelfile#[patient_directory_path 'TempModel_test5.osim'];  #need new ones because parfor
    model.printToXML(Gmodelfile)


# %% [markdown]
# # ChangeBox_Inertia

# %%
def ChangeBox_Inertia(OSmodel, hand_r, hand_l, Addname):
    """
    Modifies the inertia properties of the Box_r and Box_l bodies.
    
    The function updates the inertia properties of the Box_r and Box_l bodies in the model based on the 
    provided hand_r and hand_l dictionaries. If a dictionary is empty, the mass of the corresponding body is set to 0 and 
    its visibility is turned off.

    :param OSmodel: Path to the OpenSim model file.
    :type OSmodel: str

    :param hand_r: Dictionary containing mass and inertia properties for the right hand (Box_r).
                   Expected keys: 'mass', 'inertiaX', 'inertiaY', 'inertiaZ'.
                   If the dictionary is empty, the mass is set to 0 and visibility is set to False.
    :type hand_r: dict

    :param hand_l: Dictionary containing mass and inertia properties for the left hand (Box_l).
                   Expected keys: 'mass', 'inertiaX', 'inertiaY', 'inertiaZ'.
                   If the dictionary is empty, the mass is set to 0 and visibility is set to False.
    :type hand_l: dict

    :param Addname: Additional name to append to the model's name. Preferably starts with '_'.
    :type Addname: str

    :return: Path to the modified OpenSim model.
    :rtype: str
    """
# want in format hand_r['mass'] = #; hand_r['inertiaX'] = # (Y & Z)
# Addname is better with '_' to start
# put [] in for when no mass in hand
# jjb 7/1/21

    model = osim.Model(OSmodel)
    model.initSystem()

    path = os.path.dirname(OSmodel)
    name = os.path.basename(OSmodel).split('.')[0]
### Inertia stuff    

    if len(hand_r) > 0:
        Box= model.getBodySet().get("Box_r");        
        Box.setMass(hand_r['mass'])
        newInert = osim.Inertia(hand_r['inertiaX'], hand_r['inertiaY'], hand_r['inertiaZ'], 0, 0, 0)
        Box.setInertia(newInert)     
        model.getBodySet().get("Box_r").get_attached_geometry(0).get_Appearance().set_visible(True)
    else:
        Box= model.getBodySet().get("Box_r")        
        Box.setMass(0)
        newInert = osim.Inertia(0, 0, 0, 0, 0, 0)
        Box.setInertia(newInert)   
        model.getBodySet().get("Box_r").get_attached_geometry(0).get_Appearance().set_visible(False)
 

    if len(hand_l) > 0:
        Box= model.getBodySet().get("Box_l")
        Box.setMass(hand_l['mass'])
        newInert = osim.Inertia(hand_l['inertiaX'], hand_l['inertiaY'], hand_l['inertiaZ'], 0, 0, 0)
        Box.setInertia(newInert)
        model.getBodySet().get("Box_l").get_attached_geometry(0).get_Appearance().set_visible(True)
    else:
        Box= model.getBodySet().get("Box_l")      
        Box.setMass(0)
        newInert = osim.Inertia(0, 0, 0, 0, 0, 0)
        Box.setInertia(newInert) 
        model.getBodySet().get("Box_l").get_attached_geometry(0).get_Appearance().set_visible(False)


#Cyl.getMass();
#Cyl.getInertia.get('Products'); #these are 0 0 0
#f = Cyl.getInertia.get('Moments');
# osimVec3ToArray(f);                #or use; eval(f.toString().substring(1));

    NewName = name + Addname
    model.setName(NewName)
    NewModel = os.path.join(path,NewName + '.osim')
    model.printToXML(NewModel)

    return NewModel

# %%


# %% [markdown]
# # for i = 1:size(Subjects,2) loop

# %%

if __name__ == '__main__':
    print('Running CT & Marker Pipeline...')
    # %%
    ## INPUTS

    parser = argparse.ArgumentParser()
    parser.add_argument('base_setup',type=str,help='Model creation base setup file path')
    parser.add_argument('patient_setup',type=str,help='Patient setup file path')
    args = parser.parse_args()

    Session = 1 #session number is always 1 for VLS

    base_setup_path = args.base_setup
    patient_setup_path = args.patient_setup

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
    info = sio.loadmat(info_file_path)
    JointAngles_CT = info['jointangles'].T
    JointDist_CT = info['jointdistances'].T 
    mass = np.float64(info['Weight'][0,0])  #it's mass not weight!!!!!!!
    Height = np.float64(info['Height'][0,0])
    muscledataCSA = info['muscledataCSA']
    muscledataMAX = info['muscledataMAX']
    muscledataMAZ = info['muscledataMAZ']

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
    ## Spine curvature (Algorhythm, Marker or CT specified)
    #BaseModel stuff is in the 'Create_...' function
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
        New_Model = Scale_Hight(New_Model,StrSubj, Sex, Height, mass,scale_setup_path,output_model_path,output_setups_path,GenericHt)
 

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
    ## Scales model by muscle images  (use last model before CCC's added)
    newMuscleModel  = ScaleMuscleMarkerModel(New_Model, StrSubj, muscledataCSA/100, muscledataMAX/10, muscledataMAZ/10,scaled_model_path)  #put in cm & cm2; MAX=A/P                
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

