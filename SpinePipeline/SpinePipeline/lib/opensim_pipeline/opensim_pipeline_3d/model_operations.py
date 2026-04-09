import opensim as osim
import os
import re

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
    print(MarkerSetPath)
    Model = osim.Model(BaseModel)
    MarkerSet = osim.MarkerSet(MarkerSetPath)
    Model.set_MarkerSet(MarkerSet)

    newModel = os.path.join(output_model_path, Model.getName() + '.osim')
    Model.printToXML(newModel)
    return newModel

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