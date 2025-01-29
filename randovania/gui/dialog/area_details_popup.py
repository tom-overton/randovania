from __future__ import annotations

import dataclasses
import json
import logging
import traceback
from typing import TYPE_CHECKING

from PySide6 import QtWidgets

from randovania.gui.generated.area_details_popup_ui import Ui_AreaDetailsPopup
from randovania.gui.lib import common_qt_lib
from randovania.gui.lib.editable_list_view import HintFeatureListModel
from randovania.lib import frozen_lib

if TYPE_CHECKING:
    from randovania.game_description.db.area import Area
    from randovania.game_description.game_description import GameDescription


class AreaDetailsPopup(QtWidgets.QDialog, Ui_AreaDetailsPopup):
    def __init__(self, game: GameDescription, area: Area):
        super().__init__()
        self.setupUi(self)
        common_qt_lib.set_default_window_icon(self)

        self.game = game
        self.area = area

        self.hint_feature_box.setModel(HintFeatureListModel(self.game.hint_feature_database))
        self.hint_feature_box.delegate.items = [ft.long_name for ft in self.game.hint_feature_database.values()]

        # Signals
        self.button_box.accepted.connect(self.try_accept)
        self.button_box.rejected.connect(self.reject)

        # Values
        self.name_edit.setText(area.name)
        self.extra_edit.setPlainText(json.dumps(frozen_lib.unwrap(area.extra), indent=4))
        self.hint_feature_box.model.items = sorted(area.hint_features)

    # Final
    def create_new_area(self) -> Area:
        return dataclasses.replace(
            self.area,
            name=self.name_edit.text(),
            hint_features=frozenset(self.hint_feature_box.model.items),
            extra=json.loads(self.extra_edit.toPlainText()),
        )

    def try_accept(self) -> None:
        try:
            self.create_new_area()
            self.accept()
        except Exception as e:
            logging.exception(f"Unable to save area: {e}")

            box = QtWidgets.QMessageBox(
                QtWidgets.QMessageBox.Icon.Warning,
                "Invalid configuration",
                f"Unable to save area: {e}",
                QtWidgets.QMessageBox.StandardButton.Ok,
                None,
            )
            box.setDefaultButton(QtWidgets.QMessageBox.StandardButton.Ok)
            box.setDetailedText("".join(traceback.format_tb(e.__traceback__)))
            common_qt_lib.set_default_window_icon(box)
            box.exec_()
