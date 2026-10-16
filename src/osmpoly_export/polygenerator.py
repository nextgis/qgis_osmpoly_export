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

from pathlib import Path
from typing import Iterable, Optional, cast

from qgis.core import (
    NULL,
    QgsApplication,
    QgsCoordinateReferenceSystem,
    QgsCoordinateTransform,
    QgsFeature,
    QgsMapLayer,
    QgsProject,
    QgsVectorLayer,
)
from qgis.gui import QgisInterface
from qgis.PyQt.QtCore import (
    QCoreApplication,
    QDir,
    QLocale,
    QSettings,
    QTranslator,
)
from qgis.PyQt.QtGui import QIcon
from qgis.PyQt.QtWidgets import QAction, QFileDialog, QMenu, QMessageBox

from osmpoly_export import about_dialog
from osmpoly_export.compat import FieldType, GeometryType, LayerType
from osmpoly_export.polygenerator_dlgselfield import FieldSelectionDialog


class osmpoly_export:
    """Export polygon vector layers to Osmosis ``.poly`` files."""

    def tr(self, message: str) -> str:
        """Translate a plugin message.

        :param message: Source message to translate.
        :return: Localized message.
        """
        return QCoreApplication.translate("osmpoly_export", message)

    def __init__(self, iface: QgisInterface) -> None:
        """Initialize the plugin controller.

        :param iface: QGIS application interface used to register actions.
        """
        self.iface = iface
        self.plugin_directory = Path(__file__).resolve().parent
        self.translator: Optional[QTranslator] = None

        override_locale = QSettings().value(
            "locale/overrideFlag", False, type=bool
        )
        if not override_locale:
            locale_full_name = QLocale.system().name()
        else:
            locale_full_name = QSettings().value(
                "locale/userLocale", "", type=str
            )

        self.locale_path = (
            self.plugin_directory
            / "i18n"
            / (f"osmpoly_export_{locale_full_name[:2]}.qm")
        )
        if self.locale_path.is_file():
            self.translator = QTranslator()
            self.translator.load(str(self.locale_path))
            QCoreApplication.installTranslator(self.translator)

    def initGui(self) -> None:
        """Register plugin actions in the QGIS menus and toolbar."""
        self.plugin_menu_name = self.tr("Export OSM Poly")
        plugin_icon = QIcon(
            str(self.plugin_directory / "icons" / "osmpoly_export.svg")
        )
        self.plugin_menu = QMenu(
            self.plugin_menu_name, self.iface.mainWindow()
        )
        self.plugin_menu.setIcon(plugin_icon)

        self.action_run = QAction(self.tr("Export OSM Poly"), self.plugin_menu)
        self.action_run.setIcon(plugin_icon)
        self.action_run.setWhatsThis(self.tr("Start conversion to Poly"))
        self.action_run.setStatusTip(
            self.tr("Export vector polygons to poly-files")
        )

        self.action_about = QAction(self.tr("About"), self.plugin_menu)
        self.action_about.setIcon(
            QgsApplication.getThemeIcon("mActionPropertiesWidget.svg")
        )
        self.action_about.setWhatsThis(self.tr("About OSMPoly_export"))

        self.plugin_menu.addAction(self.action_run)
        self.plugin_menu.addAction(self.action_about)
        self.iface.vectorMenu().addMenu(self.plugin_menu)

        self.iface.addVectorToolBarIcon(self.action_run)

        self.action_run.triggered.connect(self.run)
        self.action_about.triggered.connect(self.about)
        self.iface.currentLayerChanged.connect(self._update_run_action_state)
        self._update_run_action_state(self.iface.activeLayer())

        self.__show_help_action = QAction(
            plugin_icon,
            "osmpoly_export",
            self.iface.mainWindow(),
        )
        self.__show_help_action.triggered.connect(self.about)
        plugin_help_menu = self.iface.pluginHelpMenu()
        assert plugin_help_menu is not None
        plugin_help_menu.addAction(self.__show_help_action)

    def unload(self) -> None:
        """Remove plugin actions and translations from QGIS."""
        self.iface.currentLayerChanged.disconnect(
            self._update_run_action_state
        )
        self.iface.removeVectorToolBarIcon(self.action_run)
        self.iface.vectorMenu().removeAction(self.plugin_menu.menuAction())
        self.plugin_menu.deleteLater()
        plugin_help_menu = self.iface.pluginHelpMenu()
        if plugin_help_menu is not None:
            plugin_help_menu.removeAction(self.__show_help_action)
        self.__show_help_action.deleteLater()

        if self.translator is not None:
            QCoreApplication.removeTranslator(self.translator)
            self.translator = None

    def about(self) -> None:
        """Show the plugin information dialog."""
        dialog = about_dialog.AboutDialog(self.plugin_directory.name)
        dialog.exec()

    def run(self) -> None:
        """Export selected or all features from the current polygon layer."""
        current_layer = self._current_polygon_layer()
        if current_layer is None:
            return

        features = self._features_to_export(current_layer)
        if features is None:
            return

        attribute_field = self._attribute_field(current_layer)
        if attribute_field is None:
            return

        output_directory = QFileDialog.getExistingDirectory(
            None, self.tr("Choose a folder"), QDir.currentPath()
        )
        if output_directory == "":
            return

        output_directory_path = Path(output_directory)
        coordinate_transform = self._coordinate_transform(current_layer)
        for feature_number, feature in enumerate(features, start=1):
            self._write_feature(
                feature,
                attribute_field,
                feature_number,
                output_directory_path,
                coordinate_transform,
            )

    def _current_polygon_layer(self) -> Optional[QgsVectorLayer]:
        """Return the current polygon vector layer or notify the user."""
        current_layer = self.iface.mapCanvas().currentLayer()
        warning_title = self.tr("Warning")
        if current_layer is None:
            information_message = self.tr("No layers selected")
            QMessageBox.information(
                self.iface.mainWindow(), warning_title, information_message
            )
            return None
        if current_layer.type() != LayerType.Vector:
            information_message = self.tr("Not a vector layer")
            QMessageBox.information(
                self.iface.mainWindow(), warning_title, information_message
            )
            return None
        if current_layer.geometryType() != GeometryType.Polygon:
            information_message = self.tr("Not a polygon layer")
            QMessageBox.information(
                self.iface.mainWindow(), warning_title, information_message
            )
            return None

        return cast(QgsVectorLayer, current_layer)

    def _update_run_action_state(
        self, current_layer: Optional[QgsMapLayer]
    ) -> None:
        """Enable export only when the active layer has polygon geometry."""
        is_polygon_vector_layer = (
            isinstance(current_layer, QgsVectorLayer)
            and current_layer.type() == LayerType.Vector
            and current_layer.geometryType() == GeometryType.Polygon
        )
        self.action_run.setEnabled(is_polygon_vector_layer)

    def _features_to_export(
        self, current_layer: QgsVectorLayer
    ) -> Optional[Iterable[QgsFeature]]:
        """Return selected features or all features when none are selected."""
        selected_feature_count = current_layer.selectedFeatureCount()
        if selected_feature_count:
            information_message = self.tr("Using %s selected features") % str(
                selected_feature_count
            )
            QMessageBox.information(
                self.iface.mainWindow(),
                self.tr("Information"),
                information_message,
            )
            return current_layer.selectedFeatures()

        if current_layer.featureCount() == 0:
            QMessageBox.information(
                self.iface.mainWindow(),
                self.tr("Warning"),
                self.tr("Layer is empty"),
            )
            return None

        information_message = self.tr(
            "No features selected, using all %s features"
        ) % str(current_layer.featureCount())
        QMessageBox.information(
            self.iface.mainWindow(),
            self.tr("Information"),
            information_message,
        )
        return current_layer.getFeatures()

    def _attribute_field(self, current_layer: QgsVectorLayer) -> Optional[str]:
        """Return the field selected for exported file names."""
        data_provider = current_layer.dataProvider()
        field_names = [
            field.name()
            for field in data_provider.fields()
            if field.type() == FieldType.QString
        ]
        if len(field_names) == 0:
            QMessageBox.information(
                self.iface.mainWindow(),
                self.tr("Warning"),
                self.tr("No string field names. Exiting"),
            )
            return None
        if len(field_names) == 1:
            return field_names[0]

        field_selection_dialog = FieldSelectionDialog(
            field_names, self.iface.mainWindow()
        )
        if field_selection_dialog.exec():
            return field_selection_dialog.selected_attr()

        return None

    def _coordinate_transform(
        self, current_layer: QgsVectorLayer
    ) -> Optional[QgsCoordinateTransform]:
        """Return a transform from the layer CRS to WGS 84 when required."""
        source_crs = current_layer.crs()
        if source_crs.authid() == "EPSG:4326":
            return None

        destination_crs = QgsCoordinateReferenceSystem("EPSG:4326")
        return QgsCoordinateTransform(
            source_crs, destination_crs, QgsProject.instance()
        )

    def _write_feature(
        self,
        feature: QgsFeature,
        attribute_field: str,
        feature_number: int,
        output_directory: Path,
        coordinate_transform: Optional[QgsCoordinateTransform],
    ) -> None:
        """Write one polygon feature to a ``.poly`` file.

        Empty, null, and non-polygon geometries are ignored.

        :param feature: Feature to export.
        :param attribute_field: Field supplying the output file name.
        :param feature_number: One-based feature number used for null names.
        :param output_directory: Existing directory for exported files.
        :param coordinate_transform: Transform to WGS 84, when needed.
        """
        geometry = feature.geometry()

        if (
            geometry.isNull()
            or geometry.isEmpty()
            or geometry.type() != GeometryType.Polygon
        ):
            return

        if geometry.isMultipart():
            polygons = geometry.asMultiPolygon()
        else:
            polygons = [geometry.asPolygon()]

        if not polygons:
            return

        attribute_value = feature[attribute_field]
        if attribute_value == NULL:
            attribute_value = "feature" + str(feature_number)

        output_path = output_directory / (attribute_value + ".poly")
        with output_path.open("wb") as output_file:
            output_file.write((attribute_value + "\n").encode("utf-8"))

            ring_number = 0
            for polygon in polygons:
                for ring_index, ring in enumerate(polygon, start=1):
                    ring_number += 1
                    if ring_index > 1:
                        output_file.write(
                            ("!" + str(ring_number) + "\n").encode()
                        )
                    else:
                        output_file.write((str(ring_number) + "\n").encode())

                    for vertex in ring:
                        transformed_vertex = vertex
                        if coordinate_transform is not None:
                            transformed_vertex = (
                                coordinate_transform.transform(vertex)
                            )
                        output_file.write(
                            (
                                "    "
                                + str(transformed_vertex[0])
                                + "     "
                                + str(transformed_vertex[1])
                                + "\n"
                            ).encode()
                        )
                    output_file.write(b"END\n")

            output_file.write(b"END\n")
