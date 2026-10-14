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

from typing import Optional, Sequence

from qgis.PyQt.QtWidgets import (
    QDialog,
    QHBoxLayout,
    QPushButton,
    QRadioButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)


class FieldSelectionDialog(QDialog):
    """Let the user select one string field for exported file names."""

    def __init__(
        self,
        field_names: Sequence[str],
        parent: Optional[QWidget] = None,
    ) -> None:
        """Create a field selection dialog.

        :param field_names: Non-empty field names available for selection.
        :param parent: Parent widget that owns the dialog.
        """
        super().__init__(parent)
        self.radio_buttons = [
            QRadioButton(field_name) for field_name in field_names
        ]
        self.radio_buttons[0].setChecked(True)

        fields_layout = QVBoxLayout()
        for radio_button in self.radio_buttons:
            fields_layout.addWidget(radio_button)
        scroll_area = QScrollArea()
        scroll_area_widget = QWidget()
        scroll_area_widget.setLayout(fields_layout)
        scroll_area.setWidget(scroll_area_widget)

        buttons_layout = QHBoxLayout()
        accept_button = QPushButton("Yes", self)
        cancel_button = QPushButton("Cancel", self)
        buttons_layout.addWidget(accept_button)
        buttons_layout.addWidget(cancel_button)

        dialog_layout = QVBoxLayout(self)
        dialog_layout.addWidget(scroll_area)
        dialog_layout.addLayout(buttons_layout)

        accept_button.clicked.connect(self.accept)
        cancel_button.clicked.connect(self.reject)

    def selected_attr(self) -> str:
        """Return the selected field name."""
        for radio_button in self.radio_buttons:
            if radio_button.isChecked():
                return radio_button.text()

        raise RuntimeError("No field is selected")
