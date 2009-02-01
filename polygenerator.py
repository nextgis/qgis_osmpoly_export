# -*- coding: utf-8 -*-
from PyQt4.QtCore import *
from PyQt4.QtGui import *
from qgis.core import *

import resources
from polygenerator_dlgselfield import dlgSelField

class osmpoly_export:

  def __init__(self, iface):
    """Initialize the class"""
    self.iface = iface
  
  def initGui(self):
    self.action = QAction(QIcon(":/plugins/osmpoly_export/icon.png"), "Export to OSM Poly(s)", self.iface.mainWindow())
    self.action.setStatusTip("Generate Poly files from polygons")
    
    QObject.connect(self.action, SIGNAL("activated()"), self.run)
    
    self.iface.addPluginToMenu("&Export OSM Poly", self.action)
    
  def unload(self):
    self.iface.removePluginMenu("&Export OSM Poly",self.action)
    self.iface.removeToolBarIcon(self.action)

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
    fileHandle = open ('c:\\temp\\test.txt', 'w')
	res = dlgSelField()
	QMessageBox.information(self.iface.mainWindow(),"Warning","res")
    j=0
    for fid in featids: 
       j+=1
       fileHandle.write(str(j)+"\n")
       features={}
       result={}
       features[fid]=QgsFeature()
       curLayer.featureAtId(fid,features[fid])
       result[fid]=features[fid].geometry()
       attrmap=features[fid].attributeMap()
       attrvals=attrmap.values()
       for attr in attrvals:
         QMessageBox.information(self.iface.mainWindow(),"Warning",attr.toString())
       i=0
       vertex=result[fid].vertexAt(i)
       while (vertex!=QgsPoint(0,0)):
         fileHandle.write("    "+str(vertex.x())+ "     " + str(vertex.y()) +"\n")
         i+=1
         vertex=result[fid].vertexAt(i) 
       fileHandle.write("END" +"\n")
    fileHandle.write("END" +"\n")
    fileHandle.close()