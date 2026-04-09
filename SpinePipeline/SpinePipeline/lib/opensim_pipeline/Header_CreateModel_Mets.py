
# # INIT

# %%
import opensim as osim
import numpy as np
import scipy.io as sio
from scipy.interpolate import interp1d
import os
import math as m
import argparse
from lxml import etree


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
# # Create_Scale_Model_Size_Vicon_VLS

# %%
def Create_Scale_Model_Size_Vicon_VLS(patient_ID, Ht, Wt, JointDist_Orig, JointAngle_Orig,basemodel_path,GenericHt,scale_setup_path,output_model_path, output_setups_path):
    """
    Scales an OpenSim model based on the provided height, weight, joint distances, and joint angles. 

    The function scales the model based on the provided patient's height, weight, joint distances, and joint angles. 
    It adjusts joint orientations and distances in the model based on the provided data. The scaled model is then saved 
    to a specified directory with a new name.

    :param patient_ID: Identifier for the patient.
    :type patient_ID: str

    :param Ht: Height of the patient in centimeters.
    :type Ht: float

    :param Wt: Weight of the patient.
    :type Wt: float

    :param JointDist_Orig: Original joint distances derived from marker data.
    :type JointDist_Orig: list

    :param JointAngle_Orig: Original joint angles derived from marker data.
    :type JointAngle_Orig: list

    :param basemodel_path: Path to the baseline OpenSim model file.
    :type basemodel_path: str

    :param GenericHt: Generic height value used for scaling.
    :type GenericHt: float

    :param scale_setup_path: Path to the scaling setup file.
    :type scale_setup_path: str

    :param output_model_path: Path to the directory where the scaled model will be saved.
    :type output_model_path: str

    :param output_setups_path: Path to the directory where the setup files will be saved.
    :type output_setups_path: str

    :return: Path to the scaled OpenSim model.
    :rtype: str
    """
    k=0
    Ht = Ht/100 #Change height from cm to m
    Wt = float(Wt)
    
    # Joint Angles and Distances from subject, derived from marker data
    #  in order from C7/T1 to T1/T2 down through L5/S1 to L4/L5 (before
    #  being flipped)
    JointDist = JointDist_Orig[::-1] #flip the array
    JointAngle = JointAngle_Orig[::-1]

    
    JointAngle[JointAngle==-9999] = 9999


    scTool = osim.ScaleTool(scale_setup_path)
    ## Load the baseline model and initialize
    #modelpath = ['S:/Obl/Members/Joanna_James/IMUModel/' BaseModel];
    # modelpath = 'S:/Obl/AndersonLab/SpineMetsProject/SpineMetsModeling/ModelCreation/OpenSim4/' + BaseModel
    model = osim.Model(basemodel_path)
    state = model.initSystem()
    myJoints = model.getJointSet()

    
    # Pull all 18 IVJ from model, even though only 17 joint distances (and angles) 
    # Get baseline model joint information

    JointNames = []
    Loc_R = []
    Ori_R = []
    for i in range(3,21):  #  14:31(pre full body muscle update indexes) #L5/S1 to T1_head_neck (T1/C7 equivalent) IVJ
        #Parent{count} = char(myJoints.get(i-1).getParentName); #Identify parent body
        #Child{count} = char(myJoints.get(i-1).getBody); #Identify child body
        JointNames.append(myJoints.get(i).getName()) #Array of Joint names
        #disp(JointNames{count});
        tempLocR = myJoints.get(i).get_frames(0).get_translation()
        tempOriR = myJoints.get(i).get_frames(0).get_orientation()
        Loc_R.append([osim.ArrayDouble.getValuesFromVec3(tempLocR).get(j) for j in range(3)]) #Joint location in parent body
        Ori_R.append([osim.ArrayDouble.getValuesFromVec3(tempOriR).get(j) for j in range(3)]) #Joint orientation in parent body

    
    JointNames = np.array(JointNames).reshape((18,1))
    Loc_R = np.array(Loc_R)
    Ori_R = np.array(Ori_R)

    lengthScaleFactor = Ht/GenericHt
    #for the measured intervertebral joint distances, get ratio 
        #of measured distance to baseline model distance to create scale factors
    Loc_R_ratios = np.full(shape=(17,1),fill_value = lengthScaleFactor)

    
    # Get baseline model joint angles, starting at L5/S1 (to actually
    # rotate L5)
    JointAngleRel = (Ori_R[:17,2]*180/m.pi).reshape((17,1)) #in degrees
   
    # For first joint angle (angle of L5 from sacrum), the relative motion
    # is from the sacrum, so no modification to the angle is needed.
    if JointAngle[0,k] == 9999: #if the first measured joint angle is missing, 
        #keep the orientation in parent from baseline model for that joint
        JointAngleRel[0,k] = Ori_R[0,2]*180/m.pi #in degrees
    else:
        # Keep first joint angle relative to ground (no subtraction)
    #         JointAngleRel(1,k) = JointAngle(1,k)-9; #in degrees # 9 was the
    #         joint angle in the model for L4/L5 joint for Optasia scaling
        JointAngleRel[0,k] = JointAngle[0,k] #in degrees

    
    # For remaining joint angles, get angle relative to previous vertebra.
    for i in range(1,17): #if any other joint angle measurements are missing, use 
        #orientation in parent from baseline model for that joint 
        if JointAngle[i,k] == 9999 or JointAngle[i-1,k] == 9999:
            JointAngleRel[i,k] = Ori_R[i,2]*180/m.pi #in degrees
        else:
            # Get the angle relative to IVJ below. For example, get
            # relative change in angle of L3/L4 joint by subtracting that
            # angle for the L4/L5 angle.
            JointAngleRel[i,k] = JointAngle[i,k]-JointAngle[i-1,k] #in degrees


    
    JointAngleRel = JointAngleRel*m.pi/180 #convert to radians

    CorrHeadNeck = np.sum(Ori_R[0:17,2]) - np.sum(JointAngleRel[:,k])# Move head/neck back to upright position
    CorrSternum = np.sum(Ori_R[10:17,2]) - np.sum(JointAngleRel[10:17,0])#Move sternum to reflect new curvature; fixed from T7/T8 to T1/T2 (previously 8:11)
    CorrShoulder = CorrHeadNeck - CorrSternum # Correct arms to hange by sides (not held out in front).

    ## Set joint orientations in model
    for i in range(3,20):   # 14:30(preCTadjustmodel) #L5/S1 to T1_T2
        NewOriR = osim.ArrayDouble.createVec3(0,0,JointAngleRel[i-3,k]) #Update i-# for size of joints, original 6, 
        myJoints.get(i).get_frames(0).set_orientation(NewOriR)
        

    JointNames2 = []
    OldValueNum = []
    NewValueNum = []
    for i in [20,45,48,54]:          #[30 55 58 64] #head and neck, sternum, right shoulder, left shoulder
        if i == 20:
            Correction = CorrHeadNeck
        elif i ==45:
            Correction = CorrSternum
        else:
            Correction = CorrShoulder

        OldValue = myJoints.get(i).get_frames(0).get_orientation()

        JointNames2.append(myJoints.get(i).getName())#Array of Joint names
        OldValueNum.append([osim.ArrayDouble.getValuesFromVec3(OldValue).get(j) for j in range(3)])
        NewValueNum.append(OldValueNum[-1])
        NewValueNum[-1][2] += Correction
        NewValue = osim.ArrayDouble.createVec3(NewValueNum[-1][0],NewValueNum[-1][1],NewValueNum[-1][2])
        myJoints.get(i).get_frames(0).set_orientation(NewValue)

    ## Set joint distances in model
    scaler = scTool.getModelScaler()
        # Add in marker data
    #scaler.setMarkerFileName('Trial01.trc');

    scales = scaler.getScaleSet()
    numScales = scales.getSize() #number of bodies to scale

    
    for s in range(numScales): # get all body scale factors
        scales.get(s).setScaleFactors(osim.ArrayDouble.createVec3(lengthScaleFactor, lengthScaleFactor, lengthScaleFactor))

    
    for s in range(13,30): # L5 to T1 scale factors derived from  measurements, this is not updated to 4:20, because it's specific to the setup file order
        scales.get(s).setScaleFactors(osim.ArrayDouble.createVec3(lengthScaleFactor,Loc_R_ratios[s-13,k],lengthScaleFactor)); # updated s-3

    
    ## Scale model and write to a new .osim file:

    #copyfile(TRCfile, modelDir);
    scaled_modelpath = os.path.join(output_model_path, patient_ID+'_WHSMets.osim')
    scaler.setOutputModelFileName(scaled_modelpath) #Set the name of the new model
    scaler.processModel(model,output_model_path, Wt) #processes scaling and writes to a new file.
    scaler.printToXML(os.path.join(output_setups_path,'WHSMetsSetup.xml'))

    return scaled_modelpath


# %%
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

# %% [markdown]
# # Evaluate Muscle All levels

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

# %% [markdown]
# # ScaleMuscleMarkerModel

# %%
def ScaleMuscleMarkerModel(BaseModel, patient_ID, muscledataCSA, muscledataMAX, muscledataMAZ,output_model_path):
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

    :param output_model_path: Path to save the scaled model.
    :type output_model_path: str

    :return: Path to the newly scaled model.
    :rtype: str
    """    
    # %%
    muscleinput_CSA = muscledataCSA
    muscleinput_MAX = muscledataMAZ
    muscleinput_MAY = muscledataMAX

    # %%
    #Muscle params from regression
    CSA_AveMeasured = muscleinput_CSA*2
    MAX_AveMeasured = muscleinput_MAY
    MAZ_AveMeasured = muscleinput_MAX

    # %%
    # for iter_num in range(1,2):
    iter_num = 1 #1 iteration of scaling for this function

    modelpath = BaseModel
    myModel = osim.Model(modelpath) #load the model
    print('model_path = ', modelpath)
    state = myModel.initSystem() #initialize the model; get model state
    myModel.equilibrateMuscles(state) # Make sure the muscles states are in equilibrium
    myBodies = myModel.getBodySet() #get body set

    # %% [markdown]
    # ## Evaluate Muscle All levels

    # %%
    preCSA_info, preMAX_info, preMAZ_info,preFascicleCSA_info, preFascicleMAX_info, preFascicleMAZ_info,VertCentY, VertCent, JointCent = Evaluate_Muscle_AllLevels_v3_EOTM(modelpath);

    # %%
    # ## for g loop

    # %%
    for g in range(11):

    # %% [markdown]
    # ### if iter_num > 1    continue else
        if iter_num >1:
            continue
        else:

            MuscleNames = []

            # %%
            MuscleGroup = myModel.getForceSet().getGroup(g)
            MuscleGroupName = myModel.getForceSet().getGroup(g).getName()
            FascicleNames = MuscleGroup.getMembers()
            NumFascicles = FascicleNames.getSize()
            MuscleNames.append(MuscleGroupName)

            # %%
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

        # %% [markdown]
            # #### if isempty(Levels_present) == 1 continue
            if np.where(Levels_present)[0].size != 0:

                ## Adjust CSA of size scaled subject model
                #Size Scaled Model - fascicle
                CSA_f_0 =  preFascicleCSA_info['VertCent'][MuscleGroupName][:,0:17]  #fascicle CSA at T1 through L5
                MAX_f_0 =  preFascicleMAX_info['VertCent'][MuscleGroupName][:,0:17]  #fascicle MA_X at T1 through L5
                MAZ_f_0 =  preFascicleMAZ_info['VertCent'][MuscleGroupName][:,0:17]  #fascicle MA_Z at T1 through L5

                #Whether fascicle is present at a given level
                Muscle_Present = preFascicleCSA_info['VertCent'][MuscleGroupName][:,17:34] #updated from 13:24 CHECK THIS TO SEE IF NEEDS UPDATING

                # %%
                Muscle_Present.shape

                # %%
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

                # %%
                CSA_f_0

                # %%
                for f in range(NumFascicles): #for each fascicle in the group
                    
                    CSA_f_1[f,Levels_present] = CSA_f_0[f,Levels_present]*Ratio_L[Levels_present]#Calculate fascicle CSA at each level
                    L = np.sum(Muscle_Present[f,Levels_present]) #Number of levels where it's present
                    
                    if L>0:
                        CSA_f_2[f] = np.sum(CSA_f_1[f,Levels_present])/L #average across levels to get new CSA of the fascicle
                        CSA_original_average[f] = np.sum(CSA_f_0[f,Levels_present])/L #Average in original model
                        CSA_ratio[f] = CSA_f_2[f]/CSA_original_average[f]

                # %%
                #For fascicles that were not present at the levels where CT
                #measurements were available, use the average ratio for the other
                #fascicles in the group
                CSA_ratio_nonzero = np.where(CSA_ratio > 0)[0]
                CSA_ratio_zero = np.where(CSA_ratio == 0)
                CSA_ratio_mean = np.mean(CSA_ratio[CSA_ratio_nonzero])
                CSA_ratio[CSA_ratio_zero] = CSA_ratio_mean

                # %%
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

                    # %% [markdown]
                    # ##### if g == 2 || g==4 || g == 5 || g==7 || g == 8 || g == 9 || g == 10 || g == 11

                    # %%
                    # if g in [1,3,4,6,7,8,9,10]:

            # %% [markdown]
                # ##### if iter_num <= 1
                if (iter_num <=1) and (g in [1,3,4,6,7,8,9,10]):
                    # %%
                    count=0
                    temparray = []
                    f=0
                    OriginalLength = np.zeros((1,NumFascicles))

                    # %% [markdown]
                        # ###### for f = 1:NumFascicles
                    for f in range(NumFascicles):
                        # %%
                        #Get the current muscle path from Geometry Path
                        CurrentFasName = FascicleNames.get(f).getName()
                        aMuscle = myModel.getMuscles().get(CurrentFasName) #the muscle fascicle
                        aMuscleGeometry = aMuscle.getGeometryPath()
                        aCurrentPath = aMuscleGeometry.getCurrentPath(state)
                        NumCurrentPath = aCurrentPath.getSize() #number of path points
                        OriginalLength[0,f] = aMuscle.getLength(state) #Get fascicle length
                        #Get global position of each path point
                        PtGlobal = np.zeros((NumCurrentPath,3))

                        # %%
                        for i in range(NumCurrentPath):
                            PtBody = aCurrentPath.getitem(i).getBody().getName() #body the point is in
                            globalPos = osim.ArrayDouble.createVec3(0.0,0.0,0.0)
                            myModel.getSimbodyEngine().transformPosition(state, myBodies.get(PtBody),aCurrentPath.getitem(i).getLocation(state),myModel.getGround(), globalPos)
                            PtGlobal[i,:] = [osim.ArrayDouble.getValuesFromVec3(globalPos).get(j) for j in range(3)]#array of locations in global coordinates
                        
                        # %%
                        def interp1(x,Y,xi):
                            result = []
                            # x: (n*1) Y:(n*m) xi:(n*1)
                            for i in range(Y.shape[1]):
                                f = interp1d(x[:,0], Y[:,i], kind='linear')
                                result.append(f(xi[:,0]))
                            return np.array(result).T

                        # %%
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

                        # %% [markdown]
                        # ###### for f = 1:NumFascicles end

                    # %%
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


                    # %% [markdown]
                    # ##### if iter_num <= 1 end

                # %% [markdown]
                # ##### if g == 2 || g==4 || g == 5 || g==7 || g == 8 || g == 9 || g == 10 || g == 11 end

            # %% [markdown]
            # #### if isempty(Levels_present) else end

        # %% [markdown]
        # ### if iter_num > 1 else end

    # %% [markdown]
    # ## for g loop end

    # %% [markdown]
    # 


    # %%
    Newmodelpath = os.path.join(output_model_path,patient_ID +'_FullyScaled.osim')  # UPDATE name
    myModel.printToXML(Newmodelpath)


# %% [markdown]
# # Main Loop

## INPUTS
if __name__ == '__main__':
    print('Running CT no Marker Pipeline...')
    parser = argparse.ArgumentParser()
    parser.add_argument('base_setup',type=str,help='Model creation base setup file path')
    parser.add_argument('patient_setup',type=str,help='Patient setup file path')
    args = parser.parse_args()
    # Set the session that you are interested in
    Session = 1 #session number is always 1 for VLS

    base_setup_path = args.base_setup
    patient_setup_path = args.patient_setup

    base_setup = get_base_setup_info(base_setup_path)

    male_basemodel_path = base_setup['male_basemodel_path']
    male_basemodel_height = base_setup['male_basemodel_height']
    female_basemodel_path = base_setup['female_basemodel_path']
    female_basemodel_height = base_setup['female_basemodel_height']
    scale_setup_path = base_setup['scale_setup_path']

    patient_model_creation_setup = get_patient_setup_info(patient_setup_path)
    patient_directory_path = patient_model_creation_setup['patient_directory_path']
    patient_ID = patient_model_creation_setup['patient_ID']
    info_file_path = patient_model_creation_setup['info_file_path']

    output_model_path = patient_model_creation_setup['output_model_path']
    output_setups_path = patient_model_creation_setup['output_setups_path']

    create_folder([output_model_path,output_setups_path])

    ## Load subject info file from R drive (contains muscle and CT curvature data)
    # Skip for subjects 4,5,6
    info = sio.loadmat(info_file_path)
    Sex = info['Sex'][0]
    Height = info['Height'][0][0]
    Weight = info['Weight'][0][0]
    muscledataCSA = info['muscledataCSA']
    muscledataMAX = info['muscledataMAX']
    muscledataMAZ = info['muscledataMAZ']

    # Now we can use joint angles and distances pulled from the info files
    JointAngles_CT = info['jointangles'].T
    JointDist_CT = info['jointdistances'].T
    Sex = info['Sex']


    if Sex == 'M':
        # BaseModel = bModelDirectory + 'BaseModel_Male_no_marker.osim'
        basemodel_path = male_basemodel_path
        GenericHt = male_basemodel_height # use for UppBodyHtFraction;
    elif Sex == 'F':
        # BaseModel = bModelDirectory + 'BaseModel_Female_no_marker.osim' 
        basemodel_path = female_basemodel_path
        GenericHt = female_basemodel_height
    else:
        print('Sex Error. Make sure M for male and F for Female')

    HTWTSC_Modelpath = Create_Scale_Model_Size_Vicon_VLS(patient_ID, Height, Weight, JointDist_CT, JointAngles_CT,basemodel_path,GenericHt,scale_setup_path,output_model_path, output_setups_path)

    ScaleMuscleMarkerModel(HTWTSC_Modelpath, patient_ID, muscledataCSA/100, muscledataMAX/10, muscledataMAZ/10,output_model_path)
