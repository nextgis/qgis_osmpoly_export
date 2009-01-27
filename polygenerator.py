# -*- coding: utf-8 -*-
from PyQt4.QtCore import *
from PyQt4.QtGui import *
from qgis.core import *

# инициализируем ресурсы Qt из файла resouces.py
import resources

class osmpoly_export:

  def __init__(self, iface):
    """Initialize the class"""
    # сохраним ссылку на интерфейс QGIS
    self.iface = iface
  
  def initGui(self):
    # создадим действие, которое будет запускать конфигурацию расширения
    self.action = QAction(QIcon(":/plugins/osmpoly_export/icon.png"), "Export to OSM Poly(s)", self.iface.mainWindow())
    self.action.setStatusTip("Generate Poly files from polygons")
    
    # connect the action to the run method
    QObject.connect(self.action, SIGNAL("activated()"), self.run)
    
    # добавим строку вызова в новое подменю
    self.iface.addPluginToMenu("&Export OSM Poly", self.action)
    
  def unload(self):
    # удалить меню расширения и иконку
    self.iface.removePluginMenu("&Export OSM Poly",self.action)
    self.iface.removeToolBarIcon(self.action)

  def run(self):
    layersmap=QgsMapLayerRegistry.instance().mapLayers()
    layerslist=[]
    curLayer = self.iface.mapCanvas().currentLayer()
    if (curLayer == None):
      infoString = QString("No layers selected")
      QMessageBox.information(self.iface.mainWindow(),"Warning",infoString)
    if (curLayer.type() <> curLayer.VectorLayer):
      infoString = QString("Not a vector layer")
      QMessageBox.information(self.iface.mainWindow(),"Warning",infoString)
    if curLayer.geometryType() <> QGis.Polygon: 
      infoString = QString("Not a polygon layer")
      QMessageBox.information(self.iface.mainWindow(),"Warning",infoString)
    featids=curLayer.selectedFeaturesIds()
    if (len(featids) == 0):
      infoString = QString("No features selected")
      QMessageBox.information(self.iface.mainWindow(),"Warning",infoString)
    fileHandle = open ('c:\\Gis\\OSGeo4W\\apps\\qgis\\python\\plugins\\osmpoly_export\\test.txt', 'a')
    for fid in featids: 
       features={}
       result={}
       features[fid]=QgsFeature()
       curLayer.featureAtId(fid,features[fid])
       result[fid]=features[fid].geometry()
       i=0
       vertex=result[fid].vertexAt(i)
       while (vertex!=QgsPoint(0,0)):
         fileHandle.write (str(vertex.x())+ " " + str(vertex.y()) +"\n")
         i+=1
         vertex=result[fid].vertexAt(i) 
    QMessageBox.information(self.iface.mainWindow(),"Warning",QString("done"))
    fileHandle.close()