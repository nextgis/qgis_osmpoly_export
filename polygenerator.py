# -*- coding: utf-8 -*-
from PyQt4.QtCore import *
from PyQt4.QtGui import *
from qgis.core import *

import resources_rc
from polygenerator_dlgselfield import dlgSelField

class osmpoly_export:

  def __init__(self, iface):
    """Initialize the class"""
    self.iface = iface

  def initGui(self):
    self.action = QAction(QIcon(":/plugins/osmpoly_export/icon.png"), "Export to OSM Poly(s)", self.iface.mainWindow())
    self.action.setStatusTip("Generate Poly files from polygons")

    QObject.connect(self.action, SIGNAL("triggered()"), self.run)

    if hasattr( self.iface, "addPluginToVectorMenu" ):
      self.iface.addPluginToVectorMenu("&Export OSM Poly", self.action)
    else:
      self.iface.addPluginToMenu("&Export OSM Poly", self.action)

  def unload(self):
    if hasattr( self.iface, "addPluginToVectorMenu" ):
      self.iface.removePluginVectorMenu("&Export OSM Poly",self.action)
    else:
      self.iface.removePluginMenu("&Export OSM Poly",self.action)

  def run(self):
    layersmap=QgsMapLayerRegistry.instance().mapLayers()
    layerslist=[]
    curLayer = self.iface.mapCanvas().currentLayer()
    if (curLayer == None):
      infoString = QString("No layers selected")
      QMessageBox.information(self.iface.mainWindow(),"Warning",infoString)
      return
    if (curLayer.type() <> curLayer.VectorLayer):
      infoString = QString("Not a vector layer")
      QMessageBox.information(self.iface.mainWindow(),"Warning",infoString)
      return
    if curLayer.geometryType() <> QGis.Polygon:
      infoString = QString("Not a polygon layer")
      QMessageBox.information(self.iface.mainWindow(),"Warning",infoString)
      return
    featids=curLayer.selectedFeaturesIds()
    if (len(featids) == 0):
      infoString = QString("No features selected, using all " + str(curLayer.featureCount()) + " features")
      QMessageBox.information(self.iface.mainWindow(),"Warning",infoString)
      featids = range(curLayer.featureCount())
    fProvider = curLayer.dataProvider()
    myFields = fProvider.fields()
    allFieldsNames= [f.name() for f in myFields.values()]
    myFieldsNames=[]
    for f in myFields.values():
       if f.typeName() == "String":
          myFieldsNames.append(f.name())
    if len(myFieldsNames) == 0:
       QMessageBox.information(self.iface.mainWindow(),"Warning","No string field names. Exiting")
       return
    elif len(myFieldsNames) == 1:
       attrfield = myFieldsNames[0]
    else:
      res = dlgSelField(myFieldsNames)
      if res.exec_():
        attrfield=res.selectedAttr()
      else:
        return
    attrindex = allFieldsNames.index(attrfield)
    #app = QApplication([])
    adir = QFileDialog.getExistingDirectory(None, "Open Directory", QDir.currentPath())
    j=1
    for fid in featids:
       features={}
       result={}
       features[fid]=QgsFeature()
       curLayer.featureAtId(fid,features[fid])
       result[fid]=features[fid].geometry()
       attrmap=features[fid].attributeMap()
       attr=attrmap.values()[attrindex]
       fileHandle = open (str(adir) + "/" + attr.toString() +'.poly', 'w')
       fileHandle.write(attr.toString()+"\n")
       fileHandle.write(str(j)+"\n")
       i=0
       vertex=result[fid].vertexAt(i)
       while (vertex!=QgsPoint(0,0)):
         fileHandle.write("    "+str(vertex.x())+ "     " + str(vertex.y()) +"\n")
         i+=1
         vertex=result[fid].vertexAt(i)
       fileHandle.write("END" +"\n")
       fileHandle.write("END" +"\n")
       fileHandle.close()
