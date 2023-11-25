import os
import shutil
import subprocess
import sys
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QAction
from PyQt6.QtWidgets import QApplication, QMainWindow, QTabWidget, QHBoxLayout, QWidget, QSplitter, QStyleFactory

# from balancer_tab import BalancerTab
from local_tab import LocalTab
from proxy_tab import ProxyTab
from routing_tab import RoutingTab


class V2XrayMultiMapper(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("V2XrayMultiMapper")
        self.resize(1040, 620)
        self.create_menu()
        self.create_main_panel()

    def copy_config_and_run(self, folder_name, bat_file):
        try:
            shutil.copy("config.json", f"{folder_name}/config.json")
            subprocess.Popen([f"{folder_name}/{bat_file}"], shell=True)
        except Exception as e:
            print(f"Error running {folder_name}: {e}")

    def create_menu(self):
        menubar = self.menuBar()
        menu_1 = menubar.addMenu('Menu')
        action_1_1 = QAction('Save & Build', self)
        action_1_1.triggered.connect(self.save_and_build)
        action_1_2 = QAction('run v2ray', self)
        action_1_2.triggered.connect(self.run_v2ray)
        action_1_3 = QAction('run xray', self)
        action_1_3.triggered.connect(self.run_xray)
        action_1_4 = QAction('stop', self)
        action_1_4.triggered.connect(self.stop_ray)
        menu_1.addActions([action_1_1, action_1_2, action_1_3, action_1_4])

    def create_main_panel(self):
        central_widget = QWidget(self)
        self.setCentralWidget(central_widget)
        layout_main = QHBoxLayout(central_widget)

        splitter = QSplitter(Qt.Orientation.Horizontal)
        layout_main.addWidget(splitter)

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

        self.local_tab = LocalTab(self.tab_left)
        self.tab_left.addTab(self.local_tab, 'Local')
        self.proxy_tab = ProxyTab(self.tab_left)
        self.tab_left.addTab(self.proxy_tab, 'Proxy')
        # self.tab_left.addTab(BalancerTab(self.tab_left), 'Balancer')

        self.tab_right = QTabWidget()
        splitter.addWidget(self.tab_right)

        self.routing_tab = RoutingTab(self.tab_right)
        self.tab_right.addTab(self.routing_tab, 'Routing')

        splitter.setSizes([300, 300])

    def run_v2ray(self):
        self.copy_config_and_run("v2ray", "run_v2ray.bat")

    def run_xray(self):
        self.copy_config_and_run("xray", "run_xray.bat")

    def save_and_build(self):
        self.local_tab.save_data_to_file()
        self.proxy_tab.save_data_to_file()
        self.routing_tab.save_data_to_file()
        local_data = self.local_tab.extract_table_data()
        proxy_data = self.proxy_tab.extract_table_data()
        self.routing_tab.build_config(local_data, proxy_data)

    def stop_ray(self):
        subprocess.call(["taskkill", "/f", "/im", "v2ray.exe"])
        subprocess.call(["taskkill", "/f", "/im", "xray.exe"])

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle(QStyleFactory.create('Fusion'))
    main_win = V2XrayMultiMapper()
    main_win.show()
    sys.exit(app.exec())
