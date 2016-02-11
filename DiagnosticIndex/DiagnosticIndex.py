import os, sys
import csv
import unittest
from __main__ import vtk, qt, ctk, slicer
from slicer.ScriptedLoadableModule import *
from types import *


class DiagnosticIndex(ScriptedLoadableModule):
    """Uses ScriptedLoadableModule base class, available at:
  https://github.com/Slicer/Slicer/blob/master/Base/Python/slicer/ScriptedLoadableModule.py
  """

    def __init__(self, parent):
        ScriptedLoadableModule.__init__(self, parent)
        parent.title = "DiagnosticIndex"
        parent.categories = ["Quantification"]
        parent.dependencies = []
        parent.contributors = ["Laura PASCAL (UofM)"]
        parent.helpText = """
            """
        parent.acknowledgementText = """
            This work was supported by the National
            Institutes of Dental and Craniofacial Research
            and Biomedical Imaging and Bioengineering of
            the National Institutes of Health under Award
            Number R01DE024450.
            """


class DiagnosticIndexWidget(ScriptedLoadableModuleWidget):
    def setup(self):
        ScriptedLoadableModuleWidget.setup(self)

        # ---- Widget Setup ----

        # Global Variables
        self.logic = DiagnosticIndexLogic(self)
        self.dictVTKFiles = dict()

        # Interface
        loader = qt.QUiLoader()
        moduleName = 'DiagnosticIndex'
        scriptedModulesPath = eval('slicer.modules.%s.path' % moduleName.lower())
        scriptedModulesPath = os.path.dirname(scriptedModulesPath)
        path = os.path.join(scriptedModulesPath, 'Resources', 'UI', '%s.ui' % moduleName)
        qfile = qt.QFile(path)
        qfile.open(qt.QFile.ReadOnly)

        widget = loader.load(qfile, self.parent)
        self.layout = self.parent.layout()
        self.widget = widget
        self.layout.addWidget(widget)

        #     global variables of the Interface:
        self.pathLineEdit_existingData = self.logic.get('PathLineEdit_existingData')
        self.pathLineEdit_NewGroups = self.logic.get('PathLineEdit_NewGroups')
        self.pathLineEdit_IncreaseExistingData = self.logic.get('PathLineEdit_IncreaseExistingData')
        self.collapsibleGroupBox_previewVTKFiles = self.logic.get('CollapsibleGroupBox_previewVTKFiles')
        self.checkableComboBox_ChoiceOfGroup = self.logic.get('CheckableComboBox_ChoiceOfGroup')
        self.tableWidget_VTKFile = self.logic.get('tableWidget_VTKFile')
        self.pushButton_previewVTKFiles = self.logic.get('pushButton_previewVTKFiles')
        self.pushButton_compute = self.logic.get('pushButton_compute')
        self.spinBox_healthyGroup = self.logic.get('spinBox_healthyGroup')
        self.pushButton_previewGroups = self.logic.get('pushButton_previewGroups')
        self.MRMLTreeView_classificationGroups = self.logic.get('MRMLTreeView_classificationGroups')

        # Widget Configuration

        #     disable/enable
        self.spinBox_healthyGroup.setDisabled(True)
        self.pushButton_previewGroups.setDisabled(True)
        self.pathLineEdit_IncreaseExistingData.setDisabled(True)
        self.pushButton_compute.setDisabled(True)
        self.collapsibleGroupBox_previewVTKFiles.setDisabled(True)
        self.pushButton_compute.setDisabled(True)

        # ------------------------------------------------------------------------------------
        #                                   CONNECTIONS
        # ------------------------------------------------------------------------------------
        self.pathLineEdit_existingData.connect('currentPathChanged(const QString)', self.onExistingData)
        self.pathLineEdit_NewGroups.connect('currentPathChanged(const QString)', self.onNewGroups)
        self.pathLineEdit_IncreaseExistingData.connect('currentPathChanged(const QString)', self.onIncreaseExistingData)


        slicer.mrmlScene.AddObserver(slicer.mrmlScene.EndCloseEvent, self.onCloseScene)

    # function called each time that the user "enter" in Longitudinal Quantification interface
    def enter(self):
        #TODO
        pass

    # function called each time that the user "exit" in Longitudinal Quantification interface
    def exit(self):
        #TODO
        pass

    # function called each time that the scene is closed (if Longitudinal Quantification has been initialized)
    def onCloseScene(self, obj, event):
        #TODO
        pass

    def onExistingData(self):
        print "------Existing Data PathLine------"

        # Read CSV File:
        self.logic.readCSVFile(self.pathLineEdit_existingData.currentPath)
        self.logic.creationDictVTKFiles(self.dictVTKFiles)

        # check if there is one VTK Files for one group
        self.logic.checkCSVFile(self.dictVTKFiles)

        # Set the Maximum value of spinBox_healthyGroup at the max groups possible
        self.spinBox_healthyGroup.setMaximum(len(self.dictVTKFiles))

        # Enable/disable buttons
        self.enabledButtons()
        self.pathLineEdit_NewGroups.setDisabled(True)
        self.pathLineEdit_IncreaseExistingData.setEnabled(True)

    def onNewGroups(self):
        print "------New Groups PathLine------"
        # Download the CSV file
        self.logic.readCSVFile(self.pathLineEdit_NewGroups.currentPath)
        self.logic.creationDictVTKFiles(self.dictVTKFiles)

        # Set the Maximum value of spinBox_healthyGroup at the max groups possible
        self.spinBox_healthyGroup.setMaximum(len(self.dictVTKFiles))

        # Enable/disable buttons
        self.enabledButtons()
        self.pathLineEdit_existingData.setDisabled(True)
        self.collapsibleGroupBox_previewVTKFiles.setEnabled(True)
        self.pushButton_compute.setEnabled(True)

    def enabledButtons(self):
        self.spinBox_healthyGroup.setEnabled(True)
        self.pushButton_previewGroups.setEnabled(True)
        self.MRMLTreeView_classificationGroups.setEnabled(True)

    def onIncreaseExistingData(self):
        print "------Increase Existing Data PathLine------"

        # Download the CSV file
        self.logic.readCSVFile(self.pathLineEdit_IncreaseExistingData.currentPath)

        if self.pathLineEdit_existingData.currentPath:
            self.logic.creationDictVTKFiles(self.dictVTKFiles)
        else:
            # Error:
            slicer.util.errorDisplay('No Existing Data to increase')

        # Enable/disable buttons
        self.collapsibleGroupBox_previewVTKFiles.setEnabled(True)
        self.pushButton_compute.setEnabled(True)

# ------------------------------------------------------------------------------------
#                                   ALGORITHM
# ------------------------------------------------------------------------------------


class DiagnosticIndexLogic(ScriptedLoadableModuleLogic):
    def __init__(self, interface):
        self.interface = interface
        self.allVTKFilesVectors = dict()
        self.table = vtk.vtkTable

    # === Convenience python widget methods === #
    def get(self, objectName):
        return self.findWidget(self.interface.widget, objectName)

    def findWidget(self, widget, objectName):
        if widget.objectName == objectName:
            return widget
        else:
            for w in widget.children():
                resulting_widget = self.findWidget(w, objectName)
                if resulting_widget:
                    return resulting_widget
            return None


    def readCSVFile(self, filename):
        print "CSV FilePath: " + filename
        CSVreader = vtk.vtkDelimitedTextReader()
        CSVreader.SetFieldDelimiterCharacters(",")
        CSVreader.SetFileName(filename)
        CSVreader.SetHaveHeaders(True)
        CSVreader.Update()

        self.table = CSVreader.GetOutput()

    def creationDictVTKFiles(self, dictVTKFiles):
        for i in range(0,self.table.GetNumberOfRows()):
            if not os.path.exists(self.table.GetValue(i,0).ToString()):
                slicer.util.errorDisplay('VTK file not found, path not good at lign ' + str(i+2))
                break
            value = dictVTKFiles.get(self.table.GetValue(i,1).ToInt(), None)
            if value == None:
                tempList = list()
                tempList.append(self.table.GetValue(i,0).ToString())
                dictVTKFiles[self.table.GetValue(i,1).ToInt()] = tempList
            else:
                value.append(self.table.GetValue(i,0).ToString())

        # Check
        print "Number of VTK Files in CSV Files: " + str(len(dictVTKFiles))
        for i in range(1, len(dictVTKFiles) + 1):
            value = dictVTKFiles.get(i, None)
            print "Groupe: " + str(i)
            print "VTK Files: " + str(value)

    def checkCSVFile(self, dictVTKFiles):
        for value in dictVTKFiles.values():
            if len(value) > 1:
                slicer.util.errorDisplay('There are more than one vtk file by groups')
                break

class DiagnosticIndexTest(ScriptedLoadableModuleTest):
    pass