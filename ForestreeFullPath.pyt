import arcpy
from ForestreeFullPath import forestree_crosswalk_fullpath

class Toolbox(object):
    def __init__(self):
        self.label = "Forestree Crosswalk FullPath"
        self.alias = "forestreefullpath"
        self.tools = [CrosswalkFullPath]

class CrosswalkFullPath(object):
    def __init__(self):
        self.label = "Create Forestree CSV with Full Paths"
        self.description = "Joins Forestree with Crosswalk and outputs FinalAsset paths (LowPoly/Realistic/Schematic + one FinalAsset column)."
        self.canRunInBackground = False

    def getParameterInfo(self):
        p1 = arcpy.Parameter(
            displayName="Forestree Excel File (sheet 'Forestree')",
            name="forestree_path",
            datatype="DEFile",
            parameterType="Required",
            direction="Input"
        )
        p2 = arcpy.Parameter(
            displayName="Crosswalk CSV File",
            name="crosswalk_path",
            datatype="DEFile",
            parameterType="Required",
            direction="Input"
        )
        p3 = arcpy.Parameter(
            displayName="Output CSV File",
            name="output_path",
            datatype="DEFile",
            parameterType="Required",
            direction="Output"
        )
        p4 = arcpy.Parameter(
            displayName="Default Style for FinalAsset column",
            name="style",
            datatype="GPString",
            parameterType="Optional",
            direction="Input"
        )
        p4.filter.type = "ValueList"
        p4.filter.list = ["LowPoly","Realistic","Schematic"]
        p4.value = "LowPoly"

        return [p1,p2,p3,p4]

    def execute(self, params, messages):
        forestree_path = params[0].valueAsText
        crosswalk_path = params[1].valueAsText
        output_path    = params[2].valueAsText
        style_choice   = params[3].valueAsText

        forestree_crosswalk_fullpath(
            forestree_path,
            crosswalk_path,
            output_path,
            style=style_choice
        )
        arcpy.AddMessage("✅ Completed Forestree Crosswalk (FullPath).")
