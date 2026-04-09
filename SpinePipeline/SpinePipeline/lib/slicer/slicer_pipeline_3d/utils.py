import re
import slicer
from visualization import display_point

def get_file_name_ext(file_name_with_ext):
    """
    Extracts the file name and extension from a given string.

    The function takes into account extensions like '.ext' and '.ext1.ext2'
    and returns the file name and extension separately.

    If no extension is found, the returned extension will be an empty string.

    :param file_name_with_ext: The full filename string including extension.
    :type file_name_with_ext: str

    :return: A tuple containing the base filename without extension and the extension.
    :rtype: tuple(str, str)

    :Example:

    >>> get_file_name_ext("sample.txt")
    ('sample', 'txt')

    >>> get_file_name_ext("archive.tar.gz")
    ('archive', 'tar.gz')

    :Note: This function is used to get Slicer node name
    """
    ext_pattern = r'\.([a-zA-Z0-9]+(\.[a-zA-Z0-9]+)?)$'  # extension pattern. catch ext like .ext or .ext1.ext2
    # replace the extension with ''
    filename = re.sub(ext_pattern, '', file_name_with_ext)
    ext_search = re.search(ext_pattern, file_name_with_ext)
    if ext_search:
        ext = re.search(ext_pattern, file_name_with_ext).group(1)
    else:
        ext = ''
    return filename, ext

def set_segments_name_by_map(segmentation_node, segment_name_map):
    """
    Set the segment name in the segmentation node accodring to the segment_name_map. Segments not in the map will be ignored.

    :param segmentation_node: segmentation node
    :type segmentation_node: vtkMRMLSegmentationNode
    
    :param segment_name_map: dictionary that map the original segment names to new names. dict{original name: new name}
    :type segmentation_node: dict{str:str}
    
    :return: None

    :Example:

    >>> segmentation_node = slicer.util.getFirstNodeByClassByName('vtkMRMLSegmentationNode',segmentation_name)
    >>> name_map = {'OriginalName1': 'NewName1', 'OriginalName2': 'NewName2'}
    >>> set_segments_name_by_map(segmentation_node, name_map)
    """
    segmentation = segmentation_node.GetSegmentation()
    for i in range(segmentation.GetNumberOfSegments()):  # iterate through each segment
        segment = segmentation.GetNthSegment(i)
        segment_origin_name = segment.GetName()
        if segment_origin_name in segment_name_map:
            segment.SetName(segment_name_map[segment_origin_name])
    return

def get_existing_segment_list(segmentation_node, name_list_whole):
    """
    Find all existing segment names in a given name list.

    :param segmentation_node: segmentation node
    :type segmentation_node: vtkMRMLSegmentationNode
    
    :param whole_name_list: list of interested names
    :type whole_name_list: list[str]
    
    :return: A list contains all the existing segments. In the order of the whole_name_list.
    :rtype: list[str]

    :Example:

    >>> segmentation_node = slicer.util.getFirstNodeByClassByName('vtkMRMLSegmentationNode',segmentation_name)
    >>> get_segment_arrays_dict(segmentation_node,volume_node)
    
    """
    segmentation = segmentation_node.GetSegmentation()
    existing_name_list = []
    print(segmentation.GetNumberOfSegments())
    for i in range(segmentation.GetNumberOfSegments()):  # iterate through each segment
        segment = segmentation.GetNthSegment(i)
        existing_name_list.append(segment.GetName())
    name_list = []
    for name in name_list_whole:
        if name in existing_name_list:
            name_list.append(name)

    return name_list

def get_existing_list(name_list, vertebra_properties):
    """
    Find all existing segment names in a given name list.

    :param segmentation_node: segmentation node
    :type segmentation_node: vtkMRMLSegmentationNode
    
    :param whole_name_list: list of interested names
    :type whole_name_list: list[str]
    
    :return: A list contains all the existing segments. In the order of the whole_name_list.
    :rtype: list[str]

    :Example:

    >>> segmentation_node = slicer.util.getFirstNodeByClassByName('vtkMRMLSegmentationNode',segmentation_name)
    >>> get_segment_arrays_dict(segmentation_node,volume_node)
    
    """
    result = []
    for name in name_list:
        if name in vertebra_properties.keys():
            result.append(name)

    return result

def get_segment_arrays_dict(segmentation_node, volume_node):
    """
    Return a dictionary of all segments' 3D array masks in the segmentation_node.

    :param segmentation_node: segmentation node
    :type segmentation_node: vtkMRMLSegmentationNode
    
    :param volume_node: volume node for the CT image
    :type segmentation_node: vtkMRMLScalarVolumeNode
    
    :return: A dictionary contains all the (segment_name,segment_3D_array) pairs
    :rtype: dict{ str : np.array }

    :Example:
        
    >>> volume_node = slicer.util.getFirstNodeByClassByName('vtkMRMLScalarVolumeNode',volume_name)
    >>> segmentation_node = slicer.util.getFirstNodeByClassByName('vtkMRMLSegmentationNode',segmentation_name)
    >>> get_segment_arrays_dict(segmentation_node,volume_node)
    """
    segmentation = segmentation_node.GetSegmentation()
    segment_arrays_dict = {}
    for i in range(segmentation.GetNumberOfSegments()):  # iterate through each segment
        segment = segmentation.GetNthSegment(i)
        segment_ID = segmentation.GetNthSegmentID(i)
        segment_origin_name = segment.GetName()
        segment_arrays_dict[segment_origin_name] = slicer.util.arrayFromSegmentBinaryLabelmap(
            segmentation_node, segment_ID, volume_node)
    return segment_arrays_dict


def get_segment_centroids_dict(segmentation_node, display=False, markup_node_name='F'):
    """
    Return a dictionary containing centroids of all segments within a given segmentation_node.

    This function retrieves the centroid of each segment within a provided `segmentation_node`.
    If the `display` parameter is set to True, it will also display these centroids in the scene.

    :param segmentation_node: segmentation node
    :type segmentation_node: vtkMRMLSegmentationNode
    :param display: whether display the centroid in the scene, default False
    :type display: bool
    :param markup_node_name: If `display` is True, this defines the name of the markup node for displaying centroids.
                             Default is 'F'.
    :type markup_node_name: str
    :return: A dictionary contains all the (segment_name,segment_centroid_coordinate) pairs
    :rtype: dict{ str : tuple }

    :Example:

    # Assume an initialized vtkMRMLSegmentationNode instance
    >>> segmentation = slicer.util.getFirstNodeByClassByName('vtkMRMLSegmentationNode',segmentation_name)
    >>> centroids = get_segment_centroids_dict(segmentation, display=True, markup_node_name='Centroids')

    """

    segmentation = segmentation_node.GetSegmentation()
    segment_centroids_dict = {}

    if display:
        markup_list = slicer.mrmlScene.AddNewNodeByClass(
            "vtkMRMLMarkupsFiducialNode")  # if display, add a new markup list
        # set the name of the markup list
        markup_list.SetName(markup_node_name)

    for i in range(segmentation.GetNumberOfSegments()):  # iterate through each segment
        segment = segmentation.GetNthSegment(i)
        segment_ID = segmentation.GetNthSegmentID(i)
        segment_name = segment.GetName()
        x, y, z = segmentation_node.GetSegmentCenter(segment_ID)
        segment_centroids_dict[segment.GetName()] = (x, y, z)

        if display:
            display_point(markup_list, (x, y, z), 'ctr-' + segment_name)

    return segment_centroids_dict

