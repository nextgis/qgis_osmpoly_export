# -*- coding: utf-8 -*-

#******************************************************************************
#
# osmpoly_export
# ---------------------------------------------------------
# Export vector polygons to poly-files used by Osmosis for cliping OpenStreetMap data
#
# Author: 2008-2016 Maxim Dubinin (maxim.dubinin@nextgis.com)
# Copyright (C) NextGIS (info@nextgis.com)
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

import aboutdialog
import resources
from os import path
import sys
_fs_encoding = sys.getfilesystemencoding()
_current_path = unicode(path.abspath(path.dirname(__file__)), _fs_encoding)
from polygenerator_dlgselfield import dlgSelField

class osmpoly_export:
    def tr(self, message):
        return QCoreApplication.translate('osmpoly_export', message)

    def __init__(self, iface):
        """Initialize the class"""
        # save reference to QGIS interface
        self.iface = iface
        self.qgsVersion = unicode(QGis.QGIS_VERSION_INT)
        
        # i18n support
        override_locale = QSettings().value('locale/overrideFlag', False, type=bool)
        if not override_locale:
            locale_full_name = QLocale.system().name()
        else:
            locale_full_name = QSettings().value('locale/userLocale', '', type=unicode)

        self.locale_path = '%s/i18n/osmpoly_export_%s.qm' % (_current_path, locale_full_name[0:2])
        if QFileInfo(self.locale_path).exists():
            self.translator = QTranslator()
            self.translator.load(self.locale_path)
            QCoreApplication.installTranslator(self.translator)

    def initGui(self):
        """Initialize graphic user interface"""
        #check if the plugin is ran below 2.0
        if int(self.qgsVersion) < 20000:
            qgisVersion = self.qgsVersion[0] + "." + self.qgsVersion[2] + "." + self.qgsVersion[3]
            QMessageBox.warning(self.iface.mainWindow(),
                                'osmpoly_export', self.tr('Error'),
                                'osmpoly_export', self.tr('QGIS %s detected.\n') % (qgisVersion) +
                                'osmpoly_export', self.tr('This version of OSMPoly_export requires at least QGIS version 2.0.\nPlugin will not be enabled.'))
            return None
        
        self.actionRun = QAction(self.tr('Export OSM Poly'), self.iface.mainWindow())
        self.actionRun.setIcon(QIcon(':/plugins/osmpoly_export/icons/osmpoly_export.png'))
        self.actionRun.setWhatsThis(self.tr('Start conversion to Poly'))
        self.actionRun.setStatusTip(self.tr('Export vector polygons to poly-files'))
        
        self.actionAbout = QAction(self.tr('About'), self.iface.mainWindow())
        self.actionAbout.setIcon(QIcon(':/plugins/osmpoly_export/icons/about.png'))
        self.actionAbout.setWhatsThis(self.tr('About OSMPoly_export'))
        
        # add plugin menu to Vector
        self.osmpoly_export_menu = self.tr(u'Export OSM Poly')
        self.iface.addPluginToVectorMenu(self.osmpoly_export_menu,self.actionRun)
        self.iface.addPluginToVectorMenu(self.osmpoly_export_menu,self.actionAbout)
        
        # add icon to new menu item in Vector toolbar
        self.iface.addVectorToolBarIcon(self.actionRun)
        
        # connect action to the run method
        self.actionRun.triggered.connect(self.run)
        self.actionAbout.triggered.connect(self.about)

    def unload(self):
        self.iface.removeVectorToolBarIcon(self.actionRun)
        self.iface.removePluginVectorMenu(self.tr('Export OSM Poly'),self.actionAbout)
        self.iface.removePluginVectorMenu(self.tr('Export OSM Poly'),self.actionRun)
        
    def about(self):
        d = aboutdialog.AboutDialog()
        d.exec_()
    
    def run(self):
        layersmap=QgsMapLayerRegistry.instance().mapLayers()
        layerslist=[]
        curLayer = self.iface.mapCanvas().currentLayer()
        
        strWarning = self.tr('Warning')
        strInfo = self.tr('Information')
        if (curLayer == None):
            infoString = self.tr('No layers selected')
            QMessageBox.information(self.iface.mainWindow(),strWarning,infoString)
            return
        if (curLayer.type() != curLayer.VectorLayer):
            infoString = self.tr('Not a vector layer')
            QMessageBox.information(self.iface.mainWindow(),strWarning,infoString)
            return
        if curLayer.geometryType() != QGis.Polygon:
            infoString = self.tr('Not a polygon layer')
            QMessageBox.information(self.iface.mainWindow(),strWarning,infoString)
            return
        if curLayer.selectedFeatureCount():
            infoString = self.tr('Using %s selected features')% str(curLayer.selectedFeatureCount())
            QMessageBox.information(self.iface.mainWindow(),strInfo,infoString)
            features = curLayer.selectedFeatures()
        else:
            if curLayer.featureCount() == 0:
                infoString = self.tr('Layer is empty')
                QMessageBox.information(self.iface.mainWindow(),strWarning,infoString)
                return
            else:
                infoString = self.tr('No features selected, using all %s features')% str(curLayer.featureCount())
                QMessageBox.information(self.iface.mainWindow(),strInfo,infoString)
                features = curLayer.getFeatures()

        fProvider = curLayer.dataProvider()
        myFields = fProvider.fields()
        myFieldsNames=[]
        for f in myFields:
           if f.typeName() == "String":
              myFieldsNames.append(f.name())
        if len(myFieldsNames) == 0:
           QMessageBox.information(self.iface.mainWindow(),strWarning,self.tr('No string field names. Exiting'))
           return
        elif len(myFieldsNames) == 1:
           attrfield = myFieldsNames[0]
        else:
          res = dlgSelField(myFieldsNames)
          if res.exec_():
            attrfield=res.selectedAttr()
          else:
            return

        adir = QFileDialog.getExistingDirectory(None, self.tr('Choose a folder'), QDir.currentPath())

        if adir != '':
            num = 0
            for f in features: 
                num = num + 1
                geom=f.geometry()
                
                polygons = geom.asMultiPolygon()
                if len(polygons) == 0: polygons = [geom.asPolygon()]

                attr=f[attrfield]
                if isinstance(attr, QPyNullVariant): attr = 'feature' + str(num)
                
                f = open(adir + "/" + attr +'.poly', 'w')
                f.write(attr.encode('utf-8') + "\n")

                i = 0
                for polygon in polygons:
                    j = 0
                    for ring in polygon:
                         j = j + 1
                         i = i + 1
                         if j>1:
                            f.write("!" + str(i) + "\n")
                         else:
                            f.write(str(i) + "\n")

                         #del ring[-1]
                         for vertex in ring:          
                           f.write("    " + str(vertex[0]) + "     " + str(vertex[1]) +"\n")
                         f.write("END" +"\n")

                f.write("END" +"\n")
                f.close()
