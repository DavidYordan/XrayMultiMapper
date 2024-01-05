import ipaddress
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
    QMenu,
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
from openwrt import Openwrt
from outbounds_tab import OutboundsTab
from routing_tab import RoutingTab

class XrayMultiMapper(QMainWindow):
    connect_host_failed_signal = pyqtSignal(str)
    inbounds_tag_changed_signal = pyqtSignal(str, str)
    outbounds_tag_changed_signal = pyqtSignal(str, str)
    update_inbounds_background_signal = pyqtSignal(str)
    update_menu_signal = pyqtSignal()
    update_outbounds_background_signal = pyqtSignal(str)
    
    def __init__(self):
        super().__init__()

        self.setWindowTitle("XrayMultiMapper")
        self.setWindowIcon(QIcon('img/XrayMultiMapper.ico'))
        self.resize(1040, 620)
        self.ssh_client = Openwrt(self.connect_host_failed_signal, self.update_menu_signal)
        self.create_menu()
        self.create_main_panel()
        self.connect_host_failed_signal.connect(self.connect_host_failed)
        self.inbounds_tag_changed_signal.connect(self.routing_tab.inbounds_tag_changed)
        self.outbounds_tag_changed_signal.connect(self.routing_tab.outbounds_tag_changed)
        self.update_inbounds_background_signal.connect(self.inbounds_tab.update_background)
        self.update_menu_signal.connect(self.update_openwrt_menu)
        self.update_outbounds_background_signal.connect(self.outbounds_tab.update_background)
        self.user = 'XrayMultiMapper'

        Globals._Log.info(self.user, 'XrayMultiMapper successfully initialized.')

    def closeEvent(self, event):
        # self.ssh_client.stop_xray()
        self.ssh_client.close()

        super().closeEvent(event)

    pyqtSlot(str)
    def connect_host_failed(self, host):
        self.connect_new_host(host)

    def connect_new_host(self, host=None):
        if not host:
            host, ok = QInputDialog.getText(self, 'Connect to Host', 'Enter host address:')
            if not ok or not host:
                return
        try:
            ipaddress.ip_address(host)
        except ValueError:
            Globals._Log.error(self.user, f'Invalid ip: {host}')
            return
            
        user, ok = QInputDialog.getText(self, 'Username', f'[{host}]Enter username:')
        if not ok or not user:
            return

        password, ok = QInputDialog.getText(self, 'Password', f'[{host}]Enter password:', QLineEdit.EchoMode.Password)
        if not ok or not password:
            return

        self.connect_openwrt_host(host, user, password)

    def connect_openwrt_host(self, host, user=None, password=None):
        try:
            self.ssh_client.connect(host, user, password)
        except Exception as e:
            Globals._Log.error(self.user, f'{e}')
            return
        
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

        menu_build = menubar.addMenu('Build')
        action_save_build = QAction('Save Build', self)
        action_save_build.triggered.connect(self.save_and_build)
        menu_build.addActions([action_save_build])

        menu_windows = menubar.addMenu('Windows')
        action_run_xray = QAction('Run Xray', self)
        action_run_xray.triggered.connect(self.run_xray_win)
        action_stop = QAction('Stop', self)
        action_stop.triggered.connect(self.stop_xray_win)
        menu_windows.addActions([action_run_xray, action_stop])

        self.menu_openwrt = menubar.addMenu('Openwrt')
        self.update_openwrt_menu()

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
            self.inbounds_tag_changed_signal
            
        )
        self.tab_left.addTab(self.inbounds_tab, 'Inbounds')

        self.outbounds_tab = OutboundsTab(
            self.tab_left,
            self.outbounds_tag_changed_signal
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
            self.update_inbounds_background_signal,
            self.update_outbounds_background_signal
        )
        self.tab_right.addTab(self.routing_tab, 'Routing')

        splitter.setSizes([300, 300])

        layout_main.addWidget(Globals._log_label, 1)

    def run_xray_win(self):
        self.stop_xray_win()
        if not os.path.exists('config.json'):
            Globals._Log.error(self.user, 'Please build config first')
            return

        shutil.copy('config.json', 'xray/config.json')
        subprocess.Popen(['start', 'xray.exe', 'run', '--config', 'config.json'], shell=True, cwd='xray')

    def save_and_build(self):
        self.inbounds_tab.save_data_to_file()
        self.outbounds_tab.save_data_to_file()
        self.routing_tab.save_data_to_file()
        self.routing_tab.build_config()

    def stop_xray_win(self):
        subprocess.call(["taskkill", "/f", "/im", "xray.exe"])

    @pyqtSlot()
    def update_openwrt_menu(self):
        if self.ssh_client.host:
            self.update_openwrt_menu_connected(self.ssh_client.host)
        else:
            self.update_openwrt_menu_not_connected()

    def update_openwrt_menu_connected(self, host):
        self.menu_openwrt.clear()

        menu_connected = QMenu(f'Connected: {host}', self)
        self.menu_openwrt.addMenu(menu_connected)

        action_disconnect = QAction('Disconnect', self)
        action_disconnect.triggered.connect(self.ssh_client.close)

        menu_connected.addAction(action_disconnect)

        run_xray_action = QAction('Run Xray', self)
        run_xray_action.triggered.connect(self.ssh_client.run_xray)
        stop_action = QAction('Stop', self)
        stop_action.triggered.connect(self.ssh_client.stop_xray)

        self.menu_openwrt.addActions([run_xray_action, stop_action])

    def update_openwrt_menu_not_connected(self):
        self.menu_openwrt.clear()

        connect_new_action = QAction('New', self)
        connect_new_action.triggered.connect(self.connect_new_host)
        self.menu_openwrt.addAction(connect_new_action)
        self.menu_openwrt.addSeparator()

        menu_connect = QMenu('Connect ...', self)
        known_hosts = self.ssh_client.get_known_hosts()
        for host in known_hosts:
            connect_action = QAction(host, self)
            connect_action.triggered.connect(lambda ch, host=host: self.connect_openwrt_host(host))
            menu_connect.addAction(connect_action)
        self.menu_openwrt.addMenu(menu_connect)

if __name__ == "__main__":
    app.setStyle(QStyleFactory.create('Fusion'))
    main_win = XrayMultiMapper()
    main_win.show()
    sys.exit(app.exec())
