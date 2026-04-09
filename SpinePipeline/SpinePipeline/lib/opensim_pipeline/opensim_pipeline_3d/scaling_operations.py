import os
import opensim as osim
import shutil

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

def Scale_Height(BaseModel, StrSubj, Sex, Height, mass, ScaleSetupFile,output_model_path,output_setups_path,GenericHt):
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
