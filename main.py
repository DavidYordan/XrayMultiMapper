import json
import os
import shutil
import subprocess
import sys
from PyQt6.QtCore import (
    pyqtSignal,
    pyqtSlot,
    Qt
)
from PyQt6.QtGui import (
    QAction,
    QIcon,
    QKeySequence,
    QShortcut
)
from PyQt6.QtWidgets import (
    QApplication,
    QHBoxLayout,
    QInputDialog,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QSplitter,
    QStyleFactory,
    QTabWidget,
    QVBoxLayout,
    QWidget
)

if __name__ == "__main__":
    app = QApplication(sys.argv)

from command import Command
from globals import Globals
from inbounds_tab import InboundsTab
from outbounds_tab import OutboundsTab
from routing_tab import RoutingTab

class V2XrayMultiMapper(QMainWindow):
    highlight_inbounds_row_signal = pyqtSignal(str)
    highlight_outbounds_row_signal = pyqtSignal(str)
    statistics_routings_signal = pyqtSignal()
    unhighlight_inbounds_row_signal = pyqtSignal(str)
    unhighlight_outbounds_row_signal = pyqtSignal(str)
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("V2XrayMultiMapper")
        self.setWindowIcon(QIcon('img/V2XrayMultiMapper.ico'))
        self.resize(1040, 620)
        self.create_menu()
        self.create_main_panel()
        self.highlight_inbounds_row_signal.connect(self.inbounds_tab.handle_highlight_row)
        self.unhighlight_inbounds_row_signal.connect(self.inbounds_tab.handle_unhighlight_row)
        self.highlight_outbounds_row_signal.connect(self.outbounds_tab.handle_highlight_row)
        self.unhighlight_outbounds_row_signal.connect(self.outbounds_tab.handle_unhighlight_row)
        self.statistics_routings_signal.connect()

    def command(self):
        self.Command.method = 'command'
        self.Command.kwargs = {'text': self.command_line.text()}
        self.command_line.clear()
        self.command_line.setEnabled(False)
        self.Command.condition.wakeOne()

    @pyqtSlot()
    def command_finished(self):
        self.command_line.setEnabled(True)
        Globals._log_textedit.verticalScrollBar().setValue(Globals._log_textedit.verticalScrollBar().maximum())
        self.command_line.setFocus()

    def command_show_hide(self):
        if not self.command_line.isHidden():
            self.command_line.hide()
            return
        password, ok = QInputDialog.getText(self, 'Password', 'Enter password:', QLineEdit.EchoMode.Password)
        if (password != 'asdf') | (not ok):
            return
        if not hasattr(self, 'Command'):
            self.Command = Command(self)
            self.Command.finished_signal.connect(self.command_finished, Qt.ConnectionType.QueuedConnection)
            self.Command.start()
        self.command_line.show()
        Globals._log_textedit.verticalScrollBar().setValue(Globals._log_textedit.verticalScrollBar().maximum())
        self.command_line.setFocus()

    def create_menu(self):
        menubar = self.menuBar()
        menu_1 = menubar.addMenu('Menu')
        action_1_1 = QAction('Save Build', self)
        action_1_1.triggered.connect(self.save_and_build)
        action_1_2 = QAction('Run Xray', self)
        action_1_2.triggered.connect(lambda: self.run_xray())
        action_1_3 = QAction('Stop Xray', self)
        action_1_3.triggered.connect(self.stop_xray)
        menu_1.addActions([action_1_1, action_1_2, action_1_3])

        ShortAlt_Q = QShortcut(QKeySequence('Alt+Q'), self)
        ShortAlt_Q.activated.connect(self.command_show_hide, Qt.ConnectionType.QueuedConnection)

    def create_main_panel(self):
        central_widget = QWidget(self)
        self.setCentralWidget(central_widget)
        layout_main = QVBoxLayout(central_widget)
        layout_tabs = QHBoxLayout()
        layout_main.addLayout(layout_tabs, 100)

        splitter = QSplitter(Qt.Orientation.Horizontal)
        layout_tabs.addWidget(splitter)

        splitter.setStyleSheet("""
            QSplitter::handle {
                background-color: #FFA500;
                border: 1px solid #E69500;
            }
            QSplitter::handle:hover {
                background-color: #FFB733;
            }
            QSplitter::handle:pressed {
                background-color: #CC8400;
            }
        """)

        self.tab_left = QTabWidget()
        splitter.addWidget(self.tab_left)

        self.inbounds_tab = InboundsTab(
            self.tab_left,
            self.statistics_routings_signal
            
        )
        self.tab_left.addTab(self.inbounds_tab, 'Inbounds')

        self.outbounds_tab = OutboundsTab(
            self.tab_left,
            self.statistics_routings_signal
        )
        self.tab_left.addTab(self.outbounds_tab, 'Outbounds')

        log_widget = QWidget()
        self.tab_left.addTab(log_widget, 'Log')
        log_vlayout = QVBoxLayout(log_widget)
        Globals._log_textedit.setReadOnly(True)
        Globals._log_textedit.document().setMaximumBlockCount(200)
        log_vlayout.addWidget(Globals._log_textedit, 11)
        self.command_line = QLineEdit()
        self.command_line.returnPressed.connect(self.command, Qt.ConnectionType.QueuedConnection)
        log_vlayout.addWidget(self.command_line, 1)
        self.command_line.hide()

        self.tab_right = QTabWidget()
        splitter.addWidget(self.tab_right)

        self.routing_tab = RoutingTab(
            self.tab_right,
            self.highlight_inbounds_row_signal,
            self.highlight_outbounds_row_signal,
            self.unhighlight_inbounds_row_signal,
            self.unhighlight_outbounds_row_signal,
        )
        self.tab_right.addTab(self.routing_tab, 'Routing')

        splitter.setSizes([300, 300])

        layout_main.addWidget(Globals._log_label, 1)

    def run_xray(self):
        self.stop_xray()
        if not os.path.exists('config.json'):
            QMessageBox.warning(self, 'Error!', 'Please build config first')
            return

        shutil.copy('config.json', 'xray/config.json')
        subprocess.Popen(['start', 'xray.exe', 'run', '--config', 'config.json'], shell=True, cwd='Xray')

    def save_and_build(self):
        self.inbounds_tab.save_data_to_file()
        self.outbounds_tab.save_data_to_file()
        self.routing_tab.save_data_to_file()
        self.routing_tab.build_config()

    def stop_xray(self):
        subprocess.call(["taskkill", "/f", "/im", "xray.exe"])

if __name__ == "__main__":
    app.setStyle(QStyleFactory.create('Fusion'))
    main_win = V2XrayMultiMapper()
    main_win.show()
    sys.exit(app.exec())
