import sys
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QAction
from PyQt6.QtWidgets import QApplication, QMainWindow, QTabWidget, QHBoxLayout, QWidget, QSplitter, QStyleFactory

from chain_tab import ChainTab
from local_tab import LocalTab
from proxy_tab import ProxyTab
from routing_tab import RoutingTab


class V2RayConfigTool(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("v2ray_config_tool")
        self.resize(1040, 620)
        self.create_menu()
        self.create_main_panel()

    def create_menu(self):
        menubar = self.menuBar()
        menu_1 = menubar.addMenu('菜单')
        action_1_1 = QAction('测试', self)
        action_1_2 = QAction('子菜单2', self)
        action_1_3 = QAction('子菜单3', self)
        menu_1.addActions([action_1_1, action_1_2, action_1_3])

    def create_main_panel(self):
        central_widget = QWidget(self)
        self.setCentralWidget(central_widget)
        layout_main = QHBoxLayout(central_widget)

        splitter = QSplitter(Qt.Orientation.Horizontal)
        layout_main.addWidget(splitter)

        splitter.setStyleSheet("""
            QSplitter::handle {
                background-color: #0057D8;
                border: 1px solid #004BA0;
            }
            QSplitter::handle:hover {
                background-color: #007BFF;
            }
            QSplitter::handle:pressed {
                background-color: #003E7E;
            }
        """)

        self.tab_left = QTabWidget()
        splitter.addWidget(self.tab_left)

        self.tab_left.addTab(LocalTab(self.tab_left), 'Local')
        self.tab_left.addTab(ProxyTab(self.tab_left), 'Proxy')
        # self.tab_left.addTab(ChainTab(self.tab_left), 'Chain')

        self.tab_right = QTabWidget()
        splitter.addWidget(self.tab_right)

        self.tab_right.addTab(RoutingTab(self.tab_right), 'Routing')

        splitter.setSizes([300, 300])

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle(QStyleFactory.create('Fusion'))
    main_win = V2RayConfigTool()
    main_win.show()
    sys.exit(app.exec())
