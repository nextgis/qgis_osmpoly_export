# -*- coding: utf-8 -*-

# ******************************************************************************
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
# ******************************************************************************

from qgis.PyQt.QtCore import (
    QSettings,
    QCoreApplication,
    QFileInfo,
    QTranslator,
    QDir,
    QLocale,
)
from qgis.PyQt.QtGui import QIcon
from qgis.PyQt.QtWidgets import QMessageBox, QAction, QFileDialog
from qgis.core import *
import qgis

from .compat import get_file_path, QGis, PolygonGeometry
from . import about_dialog
from . import resources
import os
from os import path
import sys

_current_path = get_file_path(__file__)

from .polygenerator_dlgselfield import dlgSelField


class osmpoly_export:
    def tr(self, message):
        return QCoreApplication.translate("osmpoly_export", message)

    def __init__(self, iface):
        """Initialize the class"""
        # save reference to QGIS interface
        self.iface = iface
        self.plugin_dir = path.dirname(__file__)

        # i18n support
        override_locale = QSettings().value(
            "locale/overrideFlag", False, type=bool
        )
        if not override_locale:
            locale_full_name = QLocale.system().name()
        else:
            locale_full_name = QSettings().value(
                "locale/userLocale", "", type=str
            )

        self.locale_path = "%s/i18n/osmpoly_export_%s.qm" % (
            _current_path,
            locale_full_name[0:2],
        )
        if QFileInfo(self.locale_path).exists():
            self.translator = QTranslator()
            self.translator.load(self.locale_path)
            QCoreApplication.installTranslator(self.translator)

    def initGui(self):
        """Initialize graphic user interface"""
        self.actionRun = QAction(
            self.tr("Export OSM Poly"), self.iface.mainWindow()
        )
        self.actionRun.setIcon(
            QIcon(":/plugins/osmpoly_export/icons/osmpoly_export.png")
        )
        self.actionRun.setWhatsThis(self.tr("Start conversion to Poly"))
        self.actionRun.setStatusTip(
            self.tr("Export vector polygons to poly-files")
        )

        self.actionAbout = QAction(self.tr("About"), self.iface.mainWindow())
        self.actionAbout.setIcon(
            QIcon(":/plugins/osmpoly_export/icons/about.png")
        )
        self.actionAbout.setWhatsThis(self.tr("About OSMPoly_export"))

        # add plugin menu to Vector
        self.osmpoly_export_menu = self.tr("Export OSM Poly")
        self.iface.addPluginToVectorMenu(
            self.osmpoly_export_menu, self.actionRun
        )
        self.iface.addPluginToVectorMenu(
            self.osmpoly_export_menu, self.actionAbout
        )

        # add icon to new menu item in Vector toolbar
        self.iface.addVectorToolBarIcon(self.actionRun)

        # connect action to the run method
        self.actionRun.triggered.connect(self.run)
        self.actionAbout.triggered.connect(self.about)

    def unload(self):
        self.iface.removeVectorToolBarIcon(self.actionRun)
        self.iface.removePluginVectorMenu(
            self.tr("Export OSM Poly"), self.actionAbout
        )
        self.iface.removePluginVectorMenu(
            self.tr("Export OSM Poly"), self.actionRun
        )

    def about(self):
        dialog = about_dialog.AboutDialog(os.path.basename(self.plugin_dir))
        dialog.exec_()

    def run(self):
        layerslist = []
        curLayer = self.iface.mapCanvas().currentLayer()

        strWarning = self.tr("Warning")
        strInfo = self.tr("Information")
        if curLayer == None:
            infoString = self.tr("No layers selected")
            QMessageBox.information(
                self.iface.mainWindow(), strWarning, infoString
            )
            return
        if curLayer.type() != curLayer.VectorLayer:
            infoString = self.tr("Not a vector layer")
            QMessageBox.information(
                self.iface.mainWindow(), strWarning, infoString
            )
            return
        if curLayer.geometryType() != PolygonGeometry:
            infoString = self.tr("Not a polygon layer")
            QMessageBox.information(
                self.iface.mainWindow(), strWarning, infoString
            )
            return
        if curLayer.selectedFeatureCount():
            infoString = self.tr("Using %s selected features") % str(
                curLayer.selectedFeatureCount()
            )
            QMessageBox.information(
                self.iface.mainWindow(), strInfo, infoString
            )
            features = curLayer.selectedFeatures()
        else:
            if curLayer.featureCount() == 0:
                infoString = self.tr("Layer is empty")
                QMessageBox.information(
                    self.iface.mainWindow(), strWarning, infoString
                )
                return
            else:
                infoString = self.tr(
                    "No features selected, using all %s features"
                ) % str(curLayer.featureCount())
                QMessageBox.information(
                    self.iface.mainWindow(), strInfo, infoString
                )
                features = curLayer.getFeatures()

        fProvider = curLayer.dataProvider()
        myFields = fProvider.fields()
        myFieldsNames = []
        for f in myFields:
            if f.typeName() == "String":
                myFieldsNames.append(f.name())
        if len(myFieldsNames) == 0:
            QMessageBox.information(
                self.iface.mainWindow(),
                strWarning,
                self.tr("No string field names. Exiting"),
            )
            return
        elif len(myFieldsNames) == 1:
            attrfield = myFieldsNames[0]
        else:
            res = dlgSelField(myFieldsNames)
            if res.exec_():
                attrfield = res.selectedAttr()
            else:
                return

        adir = QFileDialog.getExistingDirectory(
            None, self.tr("Choose a folder"), QDir.currentPath()
        )

        crsSrc = curLayer.crs()
        transform = None
        if crsSrc.authid() != "EPSG:4326":
            crsDest = QgsCoordinateReferenceSystem("EPSG:4326")  # WGS 84
            transform = QgsCoordinateTransform(
                crsSrc, crsDest, QgsProject.instance()
            )

        if adir != "":
            num = 0
            for f in features:
                num = num + 1
                geom = f.geometry()

                polygons = geom.asMultiPolygon()
                if len(polygons) == 0:
                    polygons = [geom.asPolygon()]

                attr = f[attrfield]
                if attr == qgis.core.NULL:
                    attr = "feature" + str(num)

                f = open(adir + "/" + attr + ".poly", "wb")
                f.write((attr + "\n").encode("utf-8"))

                i = 0
                for polygon in polygons:
                    j = 0
                    for ring in polygon:
                        j = j + 1
                        i = i + 1
                        if j > 1:
                            f.write(("!" + str(i) + "\n").encode())
                        else:
                            f.write((str(i) + "\n").encode())

                        # del ring[-1]
                        for vertex in ring:
                            v2 = vertex
                            if transform is not None:
                                v2 = transform.transform(vertex)
                            f.write(
                                (
                                    "    "
                                    + str(v2[0])
                                    + "     "
                                    + str(v2[1])
                                    + "\n"
                                ).encode()
                            )
                        f.write("END\n".encode())

                f.write("END\n".encode())
                f.close()
