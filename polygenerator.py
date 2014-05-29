# -*- coding: utf-8 -*-

#******************************************************************************
#
# osmpoly_export
# ---------------------------------------------------------
# Export vector polygons to poly-files used by Osmosis for cliping OpenStreetMap data
#
# Copyright (C) 2008-2014 NextGIS (info@nextgis.org)
#
# This source is free software; you can redistribute it and/or modify it under
# the terms of the GNU General Public License as published by the Free
# Software Foundation, either version 2 of the License, or (at your option)
# any later version.
#
# This code is distributed in the hope that it will be useful, but WITHOUT ANY
# WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. See the GNU General Public License for more
# details.
#
# A copy of the GNU General Public License is available on the World Wide Web
# at <http://www.gnu.org/licenses/>. You can also obtain it by writing
# to the Free Software Foundation, 51 Franklin Street, Suite 500 Boston,
# MA 02110-1335 USA.
#
#******************************************************************************

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
    self.action.setStatusTip("Export vector polygons to poly-files")

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
      infoString = "No layers selected"
      QMessageBox.information(self.iface.mainWindow(),"Warning",infoString)
      return
    if (curLayer.type() != curLayer.VectorLayer):
      infoString = "Not a vector layer"
      QMessageBox.information(self.iface.mainWindow(),"Warning",infoString)
      return
    if curLayer.geometryType() != QGis.Polygon:
      infoString = "Not a polygon layer"
      QMessageBox.information(self.iface.mainWindow(),"Warning",infoString)
      return
    sel=curLayer.selectedFeatureCount()
    if sel == 0:
      infoString = "No features selected, using all " + str(curLayer.featureCount()) + " features"
      QMessageBox.information(self.iface.mainWindow(),"Warning",infoString)
    else:
      #TODO deal with selection if any
      pass

    fProvider = curLayer.dataProvider()
    myFields = fProvider.fields()
    myFieldsNames=[]
    for f in myFields:
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
    
    adir = QFileDialog.getExistingDirectory(None, "Choose a folder", QDir.currentPath())
    
    i = 0
    
    for f in curLayer.getFeatures():
       geom=f.geometry()
       if geom.isMultipart():
         polygon = geom.asMultiPolygon()
       else:
         polygon = geom.asPolygon()

       attr=f[attrfield]
       fileHandle = open(str(adir) + "/" + attr +'.poly', 'w')
       fileHandle.write(attr.encode('utf-8') + "\n")

       for ring in polygon:
         i = i + 1
         if i>1:
            fileHandle.write("!" + str(i) + "\n")
         else:
            fileHandle.write(str(i) + "\n")

         #del ring[-1]
         for vertex in ring:          
           fileHandle.write("    " + str(vertex[0]) + "     " + str(vertex[1]) +"\n")
         fileHandle.write("END" +"\n")

       fileHandle.write("END" +"\n")
       fileHandle.close()
