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

import os

from qgis.PyQt import uic
from qgis.PyQt.QtGui import QPixmap, QTextDocument, QDesktopServices
from qgis.PyQt.QtWidgets import QDialogButtonBox, QDialog
from qgis.PyQt.QtCore import QSettings, QUrl, QLocale

from . import resources
from .compat import configparser

FORM_CLASS, _ = uic.loadUiType(os.path.join(os.path.dirname(__file__), 'ui/aboutdialogbase.ui'))


class AboutDialog(QDialog, FORM_CLASS):
    def __init__(self, parent=None):
        super(AboutDialog, self).__init__(parent)
        self.setupUi(self)

        self.btnHelp = self.buttonBox.button(QDialogButtonBox.Help)

        self.lblLogo.setPixmap(QPixmap(':/plugins/osmpoly_export/icons/osmpoly_export.png'))

        cfg = configparser.SafeConfigParser()
        cfg.read(os.path.join(os.path.dirname(__file__), 'metadata.txt'))
        version = cfg.get('general', 'version')

        self.lblVersion.setText(self.tr('Version: %s') % version)
        self.lblName.setText(self.tr('Export OSM Poly'))

        doc = QTextDocument()
        doc.setHtml(self.getAboutText())
        self.textBrowser.setDocument(doc)
        self.textBrowser.setOpenExternalLinks(True)

        self.buttonBox.helpRequested.connect(self.openHelp)

    def reject(self):
        QDialog.reject(self)

    def openHelp(self):
        overrideLocale = QSettings().value('locale/overrideFlag', False, type=bool)
        if not overrideLocale:
            localeFullName = QLocale.system().name()
        else:
            localeFullName = QSettings().value('locale/userLocale', '')

        localeShortName = localeFullName[0:2]
        if localeShortName in ['ru', 'uk']:
            QDesktopServices.openUrl(QUrl('http://gis-lab.info/qa/osmpoly.html'))
        else:
            QDesktopServices.openUrl(QUrl('http://gis-lab.info/qa/osmpoly-en.html'))

    def getAboutText(self):
        return self.tr('<p>This plugin exports vector polygons in OSM Poly format.</p>'
            '<p>Its export all or selected set of polygons and names output files according to table of attributes.'
            '<p><strong>Developer</strong>: Maxim Dubinin'
            ' (<a href="http://nextgis.com">NextGIS</a>).</p>'
            '<p><strong>Homepage</strong>: '
            '<a href="https://github.com/nextgis/osmpoly_export">'
            'https://github.com/nextgis/osmpoly_export</a></p>'
            '<p>Please report bugs at '
            '<a href="https://github.com/nextgis/osmpoly_export/issues">'
            'bugtracker</a></p>'
            )
