import json
import os
import paramiko
import shutil
import subprocess
import sys
import threading
import time
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

class XrayMultiMapper(QMainWindow):
    inbounds_tag_changed_signal = pyqtSignal(str, str)
    outbounds_tag_changed_signal = pyqtSignal(str, str)
    update_inbounds_background_signal = pyqtSignal(str)
    update_outbounds_background_signal = pyqtSignal(str)
    
    def __init__(self):
        super().__init__()
        paramiko.util.log_to_file('paramiko.log')
        self.setWindowTitle("XrayMultiMapper")
        self.setWindowIcon(QIcon('img/XrayMultiMapper.ico'))
        self.resize(1040, 620)
        self.create_menu()
        self.create_main_panel()
        self.inbounds_tag_changed_signal.connect(self.routing_tab.inbounds_tag_changed)
        self.outbounds_tag_changed_signal.connect(self.routing_tab.outbounds_tag_changed)
        self.remote_ray_thread = None
        self.remote_ray_stop_event = threading.Event()
        self.ssh_client = None
        self.update_inbounds_background_signal.connect(self.inbounds_tab.update_background)
        self.update_outbounds_background_signal.connect(self.outbounds_tab.update_background)

    def closeEvent(self, event):
        if self.remote_ray_thread and self.remote_ray_thread.is_alive():
            print('test1')
            self.remote_ray_stop_event.set()
            print('test2')
            self.remote_ray_thread.join()
            print('test3')

        super().closeEvent(event)

    def connect_to_host(self, host):
        private_key_file = os.path.join(os.getcwd(), '.ssh', f'id_rsa_{host}')
        username = 'root'
        if os.path.exists(private_key_file):
            try:
                mykey = paramiko.RSAKey.from_private_key_file(private_key_file)
                self.ssh_client = paramiko.SSHClient()
                self.ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
                self.ssh_client.connect(host, username=username, pkey=mykey)
                self.update_menu_for_connected_host(host)
            except paramiko.SSHException as e:
                print(e)
                self.prompt_for_credentials_and_generate_keys(host)
        else:
            self.prompt_for_credentials_and_generate_keys(host)

    def connect_new_host(self):
        host, ok = QInputDialog.getText(self, 'Connect to Host', 'Enter host address:')
        if not ok or not host:
            return

        self.prompt_for_credentials_and_generate_keys(host)

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

    def create_connect_submenu(self):
        self.connect_menu = QMenu('Connect ...', self)
        known_hosts = self.parse_known_hosts()
        for host in known_hosts:
            connect_action = QAction(host, self)
            connect_action.triggered.connect(lambda ch, host=host: self.connect_to_host(host))
            self.connect_menu.addAction(connect_action)
        self.connect_menu.addSeparator()
        connect_new_action = QAction('New', self)
        connect_new_action.triggered.connect(self.connect_new_host)
        self.connect_menu.addAction(connect_new_action)
        self.menu_2.addMenu(self.connect_menu)

    def create_menu(self):
        menubar = self.menuBar()
        menu_1 = menubar.addMenu('Menu')
        action_1_1 = QAction('Save Build', self)
        action_1_1.triggered.connect(self.save_and_build)
        action_1_2 = QAction('Run V2ray', self)
        action_1_2.triggered.connect(lambda: self.run_ray('v2ray'))
        action_1_3 = QAction('Run Xray', self)
        action_1_3.triggered.connect(lambda: self.run_ray('xray'))
        action_1_4 = QAction('Stop', self)
        action_1_4.triggered.connect(self.stop_ray)
        menu_1.addActions([action_1_1, action_1_2, action_1_3, action_1_4])

        self.menu_2 = menubar.addMenu('Openwrt')
        self.create_connect_submenu()

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

    def generate_and_save_ssh_keys(self, host, user, password):
        try:
            self.ssh_client = paramiko.SSHClient()
            self.ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            self.ssh_client.connect(host, username=user, password=password)

            private_key = paramiko.RSAKey.generate(2048)
            public_key = f"{private_key.get_name()} {private_key.get_base64()}"

            ssh_stdin, ssh_stdout, ssh_stderr = self.ssh_client.exec_command(
                f'echo "{public_key}" >> /etc/dropbear/authorized_keys'
            )

            ssh_dir = os.path.join(os.getcwd(), '.ssh')
            if not os.path.exists(ssh_dir):
                os.makedirs(ssh_dir)

            private_key_file = os.path.join(ssh_dir, f'id_rsa_{host}')
            private_key.write_private_key_file(private_key_file)

            self.update_menu_for_connected_host(host)
            return True
        except Exception as e:
            Globals._Log.error('main', f'Failed to generate SSH keys: {e}')
            return False

    def parse_known_hosts(self):
        ssh_dir = os.path.join(os.getcwd(), '.ssh')
        if not os.path.exists(ssh_dir):
            return []

        hosts = []
        for filename in os.listdir(ssh_dir):
            if filename.startswith('id_rsa_'):
                host = filename[7:]
                hosts.append(host)

        return hosts
    
    def prompt_for_credentials_and_generate_keys(self, host):
        user, ok = QInputDialog.getText(self, 'Username', 'Enter username:')
        if not ok or not user:
            return

        password, ok = QInputDialog.getText(self, 'Password', 'Enter password:', QLineEdit.EchoMode.Password)
        if not ok or not password:
            return

        self.generate_and_save_ssh_keys(host, user, password)


    def run_ray(self, ray_name):
        self.stop_ray()
        if not os.path.exists('config.json'):
            Globals._Log.error('main', 'Please build config first')
            return

        shutil.copy('config.json', f'{ray_name}/config.json')
        subprocess.Popen(['start', f'{ray_name}.exe', 'run', '--config', 'config.json'], shell=True, cwd=ray_name)

    def run_remote_ray(self, ray):

        def _execute_ray_command(ray):
            try:
                stdin, stdout, stderr = self.ssh_client.exec_command(f'{ray} run --config /usr/{ray}/config.json')

                while not self.remote_ray_stop_event.is_set():
                    line = stdout.readline()
                    if not line:
                        break
                    Globals._Log.info('main', line.strip())

                error_output = stderr.read().decode().strip()
                if error_output:
                    Globals._Log.error('main', f'{ray} execution error: {error_output}')
            except Exception as e:
                Globals._Log.error('main', f'Failed to execute {ray}: {e}')

        self.stop_remote_ray()
        if self.ssh_client is None:
            Globals._Log.error('main', 'No SSH connection')
            return
        if not os.path.exists('config.json'):
            Globals._Log.error('main', 'config.json not found')
            return
        if not os.path.exists('iptables.txt'):
            Globals._Log.error('main', 'iptables.txt not found')
            return
        
        try:
            stdin, stdout, stderr = self.ssh_client.exec_command(f'mkdir -p /usr/{ray}')
            error_output = stderr.read().decode().strip()
            if error_output:
                Globals._Log.error('main', f'Failed to create directory /usr/{ray}: {error_output}')
                return
        except Exception as e:
            Globals._Log.error('main', f'Failed to create directory /usr/{ray}: {e}')
            return

        try:
            with open('config.json', 'r') as file:
                config_content = json.load(file)
                config_json = json.dumps(config_content)
                command = f"echo '{config_json}' > /usr/{ray}/config.json"
                stdin, stdout, stderr = self.ssh_client.exec_command(command)
                error_output = stderr.read().decode().strip()
                if error_output:
                    Globals._Log.error('main', f'Failed to transfer config.json: {error_output}')
                    return
        except Exception as e:
            Globals._Log.error('main', f'Failed to transfer config.json: {e}')
            return

        try:
            with open('iptables.txt', 'r') as file:
                iptables_rules = file.read()
                command = f"echo '{iptables_rules}' > /etc/firewall.user"
                stdin, stdout, stderr = self.ssh_client.exec_command(command)
                error_output = stderr.read().decode().strip()
                if error_output and "critical error condition" in error_output:
                    Globals._Log.error('main', f'Failed to transfer iptables rules: {error_output}')
                    return
                elif error_output:
                    Globals._Log.warning('main', f'Warning during iptables transfer: {error_output}')
            
            stdin, stdout, stderr = self.ssh_client.exec_command('/etc/init.d/firewall restart')
            error_output = stderr.read().decode().strip()
            if error_output and "critical error condition" in error_output:
                Globals._Log.error('main', f'Failed to restart the firewall: {error_output}')
                return
            elif error_output:
                Globals._Log.warning('main', f'Warning during firewall restart: {error_output}')

            Globals._Log.info('main', 'Iptables rules transferred and firewall restarted successfully.')

        except Exception as e:
            Globals._Log.error('main', f'Failed to transfer config.json: {e}')
            return
        

        self.remote_ray_thread = threading.Thread(target=_execute_ray_command, args=(ray,))
        self.remote_ray_thread.start()

    def save_and_build(self):
        self.inbounds_tab.save_data_to_file()
        self.outbounds_tab.save_data_to_file()
        self.routing_tab.save_data_to_file()
        self.routing_tab.build_config()

    def stop_ray(self):
        subprocess.call(["taskkill", "/f", "/im", "v2ray.exe"])
        subprocess.call(["taskkill", "/f", "/im", "xray.exe"])

    def stop_remote_ray(self):
        if self.ssh_client is None:
            Globals._Log.error('main', 'No SSH connection established')
            return
        
        if self.remote_ray_thread and self.remote_ray_thread.is_alive():
            self.remote_ray_stop_event.set()
            self.remote_ray_thread = None
            self.remote_ray_stop_event.clear()

        try:
            command = "kill $(ps | grep '[x]ray run' | awk '{print $1}')"
            stdin, stdout, stderr = self.ssh_client.exec_command(command)
            stdout.channel.recv_exit_status()

            error_msg = stderr.read().decode().strip()
            if error_msg:
                Globals._Log.error('main', f'Error stopping ray processes: {error_msg}')
            else:
                Globals._Log.info('main', 'v2ray and xray processes stopped successfully.')
            
        except Exception as e:
            Globals._Log.error('main', f'Failed to stop ray processes: {e}')

    def update_menu_for_connected_host(self, host):
        self.menu_2.clear()
        self.create_connect_submenu()

        connected_host_action = QAction(f'Connected: {host}', self)
        connected_host_action.setEnabled(False)
        self.menu_2.addAction(connected_host_action)

        run_v2ray_action = QAction('Run V2ray', self)
        run_v2ray_action.triggered.connect(lambda: self.run_remote_ray('v2ray'))
        run_xray_action = QAction('Run Xray', self)
        run_xray_action.triggered.connect(lambda: self.run_remote_ray('xray'))
        stop_action = QAction('Stop', self)
        stop_action.triggered.connect(lambda: self.stop_remote_ray())

        self.menu_2.addActions([run_v2ray_action, run_xray_action, stop_action])

if __name__ == "__main__":
    app.setStyle(QStyleFactory.create('Fusion'))
    main_win = XrayMultiMapper()
    main_win.show()
    sys.exit(app.exec())
