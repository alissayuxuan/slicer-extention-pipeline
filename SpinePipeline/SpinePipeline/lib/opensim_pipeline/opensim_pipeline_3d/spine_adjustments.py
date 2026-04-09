import json
import numpy as np
import os
import opensim as osim

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
    newY = np.arcsin(R[2,0])
    newX = np.arctan2(-R[2,1] / np.cos(newY), R[2,2] / np.cos(newY))
    newZ = np.arctan2(-R[1,0] / np.cos(newY), R[0,0] / np.cos(newY))
    XYZ = np.array([newX, newY, newZ])
    return XYZ

def Spine_Curvature_Adj(BaseModel, StrSubj, Sex, Height, mass, JointDist_CT, JointAngle_CT, output_model_path, GenericHeight):
    """
    Adjusts the spine curvature based on the given parameters and saves the adjusted model.

    :param BaseModel: Path to the model file.
    :param StrSubj: Subject identifier (patient ID).
    :param Sex: Gender of the subject. 'M' for male and 'F' for female.
    :param Height: Height of the subject in centimeters.
    :param mass: Mass of the subject in kilograms.
    :param JointDist_CT: Distances between inter-vertebra joints from CT.
    :param JointAngle_CT: Angles of the inter-vertebra joints from CT.
    :param output_model_path: Path to the directory where the adjusted model will be saved.
    :param GenericHeight: Generic height value used for scaling.
    :return: Path to the saved adjusted model.
    """
    print('Adjusting Spine Curvature')

    k = 1
    Ht = Height / 100  # Convert height from cm to m
    BodyHt = Ht

    vertebrae_names = [
        "L5", "L4", "L3", "L2", "L1", 
        "T12", "T11", "T10", "T9", "T8", 
        "T7", "T6", "T5", "T4", "T3", 
        "T2", "T1"
    ]

    # Load baseline model
    model = osim.Model(BaseModel)
    myJoints = model.getJointSet()

    joint_info_file = [
        "L5S1", "L4L5", "L3L4", "L2L3", "L1L2", "T12L1", "T11T12", "T10T11",
        "T9T10", "T8T9", "T7T8", "T6T7", "T5T6", "T4T5", "T3T4", "T2T3",
        "T1T2", "C7T1"
    ]

    JointNames = [
        'L5_S1_IVDjnt', 'L4_L5_IVDjnt', 'L3_L4_IVDjnt', 'L2_L3_IVDjnt', 'L1_L2_IVDjnt',
        'T12_L1_IVDjnt', 'T11_T12_IVDjnt', 'T10_T11_IVDjnt', 'T9_T10_IVDjnt',
        'T8_T9_IVDjnt', 'T7_T8_IVDjnt', 'T6_T7_IVDjnt', 'T5_T6_IVDjnt', 'T4_T5_IVDjnt',
        'T3_T4_IVDjnt', 'T2_T3_IVDjnt', 'T1_T2_IVDjnt', 'T1_head_neck'
    ]

    Ori_R = np.zeros((len(JointNames), 3))

    # Get joint orientations from base model
    for i in range(len(JointNames)):
        tempOriR = myJoints.get(JointNames[i]).get_frames(0).get_orientation()
        Ori_R[i, :] = [osim.ArrayDouble.getValuesFromVec3(tempOriR).get(j) for j in range(3)]

    # Set new orientations from CT data
    for i in range(len(JointNames) - 1):
        NewOriR = osim.ArrayDouble.createVec3(
            JointAngle_CT[joint_info_file[i]][0],
            JointAngle_CT[joint_info_file[i]][1],
            JointAngle_CT[joint_info_file[i]][2]
        )
        myJoints.get(JointNames[i]).get_frames(0).set_orientation(NewOriR)

    # Calculate orientation change from basemodel for correction of additional bodies
    JointChange = np.zeros((12, 3))
    for i in range(5, len(JointAngle_CT) - 1):
        temp = [
            np.sum([JointAngle_CT[joint_name][0] for joint_name in joint_info_file[:i + 1]]) - np.sum(Ori_R[:i + 1, 0]),
            np.sum([JointAngle_CT[joint_name][1] for joint_name in joint_info_file[:i + 1]]) - np.sum(Ori_R[:i + 1, 1]),
            np.sum([JointAngle_CT[joint_name][2] for joint_name in joint_info_file[:i + 1]]) - np.sum(Ori_R[:i + 1, 2])
        ]
        JointChange[i - 5, :] = temp

    JointNames3 = [
        'T12_r12R_CVjnt', 'T11_r11R_CVjnt', 'T10_r10R_CVjnt', 'T9_r9R_CVjnt',
        'T8_r8R_CVjnt', 'T7_r7R_CVjnt', 'T6_r6R_CVjnt', 'T5_r5R_CVjnt',
        'T4_r4R_CVjnt', 'T3_r3R_CVjnt', 'T2_r2R_CVjnt', 'T1_r1R_CVjnt',
        'T12_r12L_CVjnt', 'T11_r11L_CVjnt', 'T10_r10L_CVjnt', 'T9_r9L_CVjnt',
        'T8_r8L_CVjnt', 'T7_r7L_CVjnt', 'T6_r6L_CVjnt', 'T5_r5L_CVjnt',
        'T4_r4L_CVjnt', 'T3_r3L_CVjnt', 'T2_r2L_CVjnt', 'T1_r1L_CVjnt'
    ]


    Ori_R3 = np.zeros((len(JointNames3), 3))
    for i in range(len(JointNames3)):
        tempOriR = myJoints.get(JointNames3[i]).get_frames(0).get_orientation()
        Ori_R3[i, :] = [osim.ArrayDouble.getValuesFromVec3(tempOriR).get(j) for j in range(3)]

    Correction = np.tile(-JointChange, (2, 1))

    for i in range(len(JointNames3)):
        gf = 0
        OldValue = myJoints.get(JointNames3[i]).get_frames(gf).get_orientation()
        NewValueNum = [osim.ArrayDouble.getValuesFromVec3(OldValue).get(j) for j in range(3)]
        Rnv = XYZ2R(NewValueNum)
        Rc = XYZ2R(Correction[i, :])
        NewValueNum = R2XYZ(Rnv @ Rc)
        NewValue = osim.ArrayDouble.createVec3(*NewValueNum)
        myJoints.get(JointNames3[i]).get_frames(gf).set_orientation(NewValue)

    CorrHeadNeck = [
        np.sum(Ori_R[:17, i]) - np.sum([JointAngle_CT[joint_name][i] for joint_name in joint_info_file[:17]])
        for i in range(3)
    ]
    print(CorrHeadNeck)

    CorrSternum = [
        np.sum(Ori_R[10:17, i]) - np.sum([JointAngle_CT[joint_name][i] for joint_name in joint_info_file[10:17]])
        for i in range(3)
    ]
    CorrShoulder = np.array(CorrHeadNeck) - np.array(CorrSternum)

    Correction = [CorrHeadNeck, CorrSternum, CorrShoulder, CorrShoulder]
    JointNames2 = ['T1_head_neck', 'r1R_sterR_jnt', 'shoulder_R', 'shoulder_L']

    for i in range(1):  # only head/neck updated here
        OldValue = myJoints.get(JointNames2[i]).get_frames(0).get_orientation()
        NewValueNum = np.array([osim.ArrayDouble.getValuesFromVec3(OldValue).get(j) for j in range(3)])
        NewValueNum += Correction[i]
        NewValue = osim.ArrayDouble.createVec3(*NewValueNum)
        myJoints.get(JointNames2[i]).get_frames(0).set_orientation(NewValue)

    # Hide muscles for review
    nMuscles = model.getMuscles().getSize()
    for i in range(nMuscles):
        mus = model.getMuscles().get(i)
        mus.getGeometryPath().upd_Appearance().set_visible(False)

    model.setName(StrSubj + '_SpineAdjust')
    New_modelpath = os.path.join(output_model_path, model.getName() + '.osim')
    model.printToXML(New_modelpath)

    return New_modelpath


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
    
    vertebrae_names = [
    "L5", "L4", "L3", "L2", "L1", 
    "T12", "T11", "T10", "T9", "T8", 
    "T7", "T6", "T5", "T4", "T3", 
    "T2", "T1"]
    # Parse the JSON structure for joint distances
    JointDist_Orig = json.loads(JointDist_Orig)

    JointDistArray= np.zeros((len(JointDist_Orig),3))
    for i, vertebra_name in enumerate(vertebrae_names):
        dist_components = JointDist_Orig[vertebra_name]  # e.g., {'AP': value, 'SI': value, 'ML': value}
        JointDistArray[i, :] = [
            dist_components['AP'] / 1000 if dist_components['AP'] != 9999 else 9999,
            dist_components['SI'] / 1000 if dist_components['SI'] != 9999 else 9999,
            dist_components['ML'] / 1000 if dist_components['ML'] != 9999 else 9999
        ]

    # since the direction is already set by the angle of the previous vertebrae we only need the distance 
    for level in JointDistArray:
        if level[1] == 9999:
            continue
        level[0] = 9999
        level[1] = np.linalg.norm(level)
        level[2] = 9999

    ## Load the baseline model and initialize
    model = osim.Model(BaseModel)

    # ##
    ## Get baseline model joint information
    myJoints = model.getJointSet()        
    # joints we want to adjust
    JointNames = ['L5_S1_IVDjnt','L4_L5_IVDjnt','L3_L4_IVDjnt','L2_L3_IVDjnt','L1_L2_IVDjnt','T12_L1_IVDjnt','T11_T12_IVDjnt','T10_T11_IVDjnt','T9_T10_IVDjnt','T8_T9_IVDjnt','T7_T8_IVDjnt','T6_T7_IVDjnt','T5_T6_IVDjnt','T4_T5_IVDjnt','T3_T4_IVDjnt','T2_T3_IVDjnt','T1_T2_IVDjnt','T1_head_neck']
    Loc_R = np.zeros((len(JointNames),3))

    # ## Extract the joint locations from the base model
    # Pull all 18 IVJ from model, even though only 17 joint distances (and angles) 
    for i in range(len(JointNames)):  #  4:21 when numbered #L5/S1 to T1_head_neck (T1/C7 equivalent) IVJ
        tempLocR = myJoints.get(JointNames[i]).get_frames(0).get_translation()
        Loc_R[i,:]= [osim.ArrayDouble.getValuesFromVec3(tempLocR).get(j) for j in range(3)] #Joint location in parent body

    # ##
    Model_Scaled_Heights = Loc_R[1:,:].copy()  #2nd column is y-axis/direction height/distance

    #calculates the ratio the joint has in the base model
    Matching_JD = np.zeros_like(Model_Scaled_Heights) #preallocate array
    Matching_JD[JointDistArray<5] = Model_Scaled_Heights[JointDistArray<5]  #good joint distances
    Total_Scaled_Matching = np.sum(Matching_JD,axis=0)  #how 'tall' the good joint distances are in model
    Ratio_Matching = Matching_JD/Total_Scaled_Matching  #how much of the spine distance is known relative to total height 

    #calculates how the ratio has changed
    JD_0s = JointDistArray.copy()
    JD_0s[JointDistArray>=5] = 0  #get rid of 9.9999
    Total_JD_Found = np.sum(JointDistArray[JointDistArray<5], axis=0) #how 'tall' the good joint distances were calculated to be
    Ratio_JD_Found = JD_0s / Total_JD_Found #ratio of what known to known height
    RofRatios = Ratio_JD_Found/Ratio_Matching  #ratio of ratios from what found to what I assumed

    # ##
    ### use ratio of what was found to what was assumed prior to find new distances      
    Model_Scaled_Heights[JointDistArray<5] = Model_Scaled_Heights[JointDistArray<5] * RofRatios[JointDistArray<5]


    #calculate the ratio between scaled distance in model to the measured value from CT assumes atleast one measurement
    vertical_dist = Model_Scaled_Heights[:,1]
    indices = np.where(vertical_dist<5)
    index = indices[0][0]
    scaled_d_to_measured = Model_Scaled_Heights[index][1] /JointDistArray[index][1]
    new_scaled_location = Loc_R.copy()
    # Replace NaN in Model_Scaled_Heights with corresponding values of measured distance scaled to model
    new_scaled_location[1:, :] = np.where(np.isnan(Model_Scaled_Heights), JointDistArray*scaled_d_to_measured, Model_Scaled_Heights)

    # ##
    '''difference'''
    # ##      set new joint distances in model 
    for i in range(len(JointNames)):   # 4:20 #L5/S1 to T1_T2
        NewLoc_R = osim.ArrayDouble.createVec3(*new_scaled_location[i]); #Update i-# of joints, 18 
        myJoints.get(JointNames[i]).get_frames(0).set_translation(NewLoc_R)

    rIVJ_Use = new_scaled_location[:,:]/Loc_R[:,:]  

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
        setSF = osim.ArrayDouble.createVec3(scaleFacts[0],scaleFacts[1]*rIVJ_Use[v+1,1],scaleFacts[2])
        cBody.get_attached_geometry(0).set_scale_factors(setSF)
        
    # CoM y
        bCoM = np.array([cBody.getMassCenter().get(j) for j in range(3)])
        setCOM = osim.ArrayDouble.createVec3(bCoM[0]*rIVJ_Use[v+1,0],bCoM[1]*rIVJ_Use[v+1,1],bCoM[2]*rIVJ_Use[v+1,2])
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

def getJointAngles_Osim(VertebralAxes_CT, jnts='All'):
    """
    Calculate the Euler angles (joint orientations) between adjacent vertebrae
    based on CT-derived vertebral axes.

    Parameters:
        VertebralAxes_CT (str or dict): JSON string or dict with vertebral axis unit vectors ('AP', 'SI', 'ML').
        jnts (str or list): List of joints to process. Default is 'All' (L5S1 to C7T1).

    Returns:
        dict: Dictionary of joint names mapped to [X, Y, Z] Euler angles (in radians),
              or [9999, 9999, 9999] if data is missing or invalid.
    """
    # Parse JSON string if necessary
    if isinstance(VertebralAxes_CT, str):
        VertebralAxes_CT = json.loads(VertebralAxes_CT)

    # Vertebral order and joint definitions
    vert_list = [
        "S1", "L5", "L4", "L3", "L2", "L1",
        "T12", "T11", "T10", "T9", "T8", "T7",
        "T6", "T5", "T4", "T3", "T2", "T1", "C7"
    ]

    jnt_vertebra = ["L5S1", "L4L5", "L3L4", "L2L3", "L1L2"]
    jnt_thoracic = ["T12L1", "T11T12", "T10T11", "T9T10", "T8T9", "T7T8", "T6T7", "T5T6", "T4T5", "T3T4", "T2T3", "T1T2", "C7T1"]

    jnt_list = jnt_vertebra + jnt_thoracic if jnts == 'All' else jnts

    JtAngles = {}

    for joint in jnt_list:
        idx = jnt_list.index(joint)
        parent = vert_list[idx]
        child = vert_list[idx + 1]

        if child not in VertebralAxes_CT or parent not in VertebralAxes_CT:
            if parent == "S1":
                x_child = np.array(VertebralAxes_CT[child]['AP'])
                y_child = np.array(VertebralAxes_CT[child]['SI'])
                z_child = np.array(VertebralAxes_CT[child]['ML'])

                x_parent = np.array([0, -1, 0]) 
                y_parent = np.array([0, 0, -1])
                z_parent = np.array([-1, 0, 0])
            else:
                JtAngles[joint] = np.array([9999, 9999, 9999])
                continue

        else:
            # Extract axis vectors
            x_child = np.array(VertebralAxes_CT[child]['AP'])
            y_child = np.array(VertebralAxes_CT[child]['SI'])
            z_child = np.array(VertebralAxes_CT[child]['ML'])

            x_parent = np.array(VertebralAxes_CT[parent]['AP'])
            y_parent = np.array(VertebralAxes_CT[parent]['SI'])
            z_parent = np.array(VertebralAxes_CT[parent]['ML'])

        # Build transformation matrices
        T_parent = np.column_stack([x_parent, y_parent, z_parent])
        T_child = np.column_stack([x_child, y_child, z_child])

        # Sanity checks
        if (
            abs(np.linalg.det(T_parent)) > 1.1 or
            abs(np.linalg.det(T_child)) > 1.1 or
            np.any(T_parent == 9999) or
            np.any(T_child == 9999)
        ):
            JtAngles[joint] = np.array([9999, 9999, 9999])
            continue

        # Calculate relative rotation matrix
        R = T_child.T @ T_parent

        # Convert rotation matrix to Euler angles (ZYX sequence)
        newY = np.arcsin(R[2, 0])
        newX = np.arctan2(-R[2, 1] / np.cos(newY), R[2, 2] / np.cos(newY))
        newZ = np.arctan2(-R[1, 0] / np.cos(newY), R[0, 0] / np.cos(newY))

        orientation_offset_rad = np.array([newX, newY, newZ])
        JtAngles[joint] = orientation_offset_rad

    return JtAngles
