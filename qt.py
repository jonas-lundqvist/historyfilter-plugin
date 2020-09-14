#!/usr/bin/env python3

from functools import partial

from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *

from electroncash.plugins import BasePlugin, hook
from electroncash.i18n import _
from electroncash_gui.qt.util import EnterButton, Buttons
from electroncash_gui.qt.util import OkButton, WindowModalDialog

DEFAULT_HISTORY_PREFIX = ';'

class Plugin(BasePlugin):

    def __init__(self, parent, config, name):
        BasePlugin.__init__(self, parent, config, name)
        self.filter_enabled = self.config.get('historyfilter_enabled', False)
        self.filter_prefix = self.config.get('historyfilter_prefix', DEFAULT_HISTORY_PREFIX)
        self.gui = None
        self.initted = False
        self._hide_history_txs = True

    def requires_settings(self):
        return True

    def has_settings_dialog(self):
        return True

    def settings_widget(self, window):
        return EnterButton(_('Settings'), partial(self.settings_dialog, window))

    def settings_dialog(self, window):
        d = WindowModalDialog(window.top_level_window(), _("History Filter Settings"))
        d.ok_button = OkButton(d)

        hbox = QHBoxLayout()
        hbox.addWidget(QLabel(_("Label prefix for hidden transactions")))
        textbox = QLineEdit()
        textbox.setMaxLength(32)
        textbox.setText(self.filter_prefix)
        hbox.addWidget(textbox)
        vbox = QVBoxLayout(d)
        vbox.addLayout(hbox)
        vbox.addSpacing(20)
        vbox.addLayout(Buttons(d.ok_button))
        if not d.exec_():
            return
        self.filter_prefix = str(textbox.text())

        if len(self.filter_prefix) < 1:
            self.filter_prefix = DEFAULT_HISTORY_PREFIX
        self.config.set_key('historyfilter_prefix', self.filter_prefix)

        for w in self.gui.windows:
            w.history_list.update()

    @hook
    def history_list_filter(self, history_list, h_item, label):
        if self._hide_history_txs:
            return bool(label.startswith(self.filter_prefix))
        return None

    @hook
    def history_list_context_menu_setup(self, history_list, menu, item, tx_hash):
        menu.addSeparator()
        def action_callback():
            self._hide_history_txs = not self._hide_history_txs
            self.filter_enabled = self.config.get('historyfilter_enabled', False)
            action.setChecked(self._hide_history_txs)
            if self._hide_history_txs:
                tip = _("Filtered transactions are now hidden")
            else:
                tip = _("Filtered transactions are now shown")
            QToolTip.showText(QCursor.pos(), tip, history_list)
            history_list.update()
            for w in self.gui.windows:
                if history_list is not w.history_list:
                    w.history_list.update()
        action = menu.addAction(_("Apply prefix based filter"), action_callback)
        action.setCheckable(True)
        action.setChecked(self._hide_history_txs)
        self.config.set_key('historyfilter_enabled', self._hide_history_txs)

    @hook
    def init_qt(self, gui):
        if self.initted:
            return
        self.gui = gui
        self.initted = True
