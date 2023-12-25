from PyQt6.QtCore import (
    Qt
)
from PyQt6.QtGui import (
    QIntValidator,
    QValidator
)
from PyQt6.QtWidgets import (
    QComboBox,
    QDialog,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget
)

from globals import Globals

class OutboundsDialog(QDialog):
    def __init__(
            self,
            parent,
            row_signal,
            protocol,
            row = -1
        ):
        super().__init__(parent)

        self.user = f'{protocol} dialog'
        self.allowed_nets = []
        self.columns = []
        self.old_data = {}
        self.protocol = protocol
        self.row = row
        self.row_signal = row_signal

        self.setWindowTitle(f'{self.protocol} settings')
        self.setWindowFlag(Qt.WindowType.WindowStaysOnTopHint)
        self.setup_ui()
        self.exec()

        if self.row != -1:
            self.old_data = self.fill_data(self.get_data())

        Globals._Log.info(self.user, f'{self.protocol} dialog successfully initialized.')

    def fill_data(self, data):
        if self.protocol == 'shadowsocks':
            return self.ui_shadowsocks_fill(data)
        elif self.protocol == 'socks':
            return self.ui_socks_fill(data)
        elif self.protocol == 'vless':
            return self.ui_vless_fill(data)
        elif self.protocol == 'vmess':
            return self.ui_vmess_fill(data)
        elif self.protocol == 'trojan':
            return self.ui_trojan_fill(data)
        else:
            self.close()

    def get_data(self):
        source_tag, protocol, address, port, encryption, net, security, remarks, key = self.parent().parse_row_data(self.row)
        with Globals.outbounds_lock:
            if key in Globals.outbounds_dict:
                return Globals.outbounds_dict[key]
        return {
            'source_tag': source_tag,
            'protocol': protocol,
            'address': address,
            'port': port,
            'encryption': encryption,
            'net': net,
            'security': security,
            'remarks': remarks
        }

    def setup_ui(self):
        if self.protocol == 'shadowsocks':
            self.ui_shadowsocks()
        elif self.protocol == 'socks':
            self.ui_socks()
        elif self.protocol == 'trojan':
            self.ui_trojan()
        elif self.protocol == 'vless':
            self.ui_vless()
        elif self.protocol == 'vmess':
            self.ui_vmess()
        else:
            self.close()

    def ui_shadowsocks(self):
        layout = QVBoxLayout()
        
        hlayout_source_tag = QHBoxLayout()
        layout.addLayout(hlayout_source_tag, 1)
        hlayout_source_tag.addWidget(QLabel('source_tag', self))
        self.line_source_tag = QLineEdit(self)
        hlayout_source_tag.addWidget(self.line_source_tag)
        
        hlayout_source = QHBoxLayout()
        layout.addLayout(hlayout_source, 1)
        hlayout_source.addWidget(QLabel('source', self))
        self.line_source = QLineEdit(self)
        hlayout_source.addWidget(self.line_source)
        
        layout.addStretch(1)
        
        hlayout_tag = QHBoxLayout()
        layout.addLayout(hlayout_tag, 1)
        hlayout_tag.addWidget(QLabel('tag', self))
        self.line_tag = QLineEdit(self)
        hlayout_tag.addWidget(self.line_tag)

        hlayout_address = QHBoxLayout()
        layout.addLayout(hlayout_address, 1)
        hlayout_address.addWidget(QLabel('address*', self))
        self.line_address = QLineEdit(self)
        hlayout_address.addWidget(self.line_address)

        hlayout_port = QHBoxLayout()
        layout.addLayout(hlayout_port, 1)
        hlayout_port.addWidget(QLabel('port*', self))
        self.line_port = QLineEdit(self)
        self.line_port.setValidator(PortValidator(self))
        hlayout_port.addWidget(self.line_port)

        hlayout_user = QHBoxLayout()
        layout.addLayout(hlayout_user, 1)
        hlayout_user.addWidget(QLabel('user', self))
        self.line_user = QLineEdit(self)
        hlayout_user.addWidget(self.line_user)

        hlayout_password = QHBoxLayout()
        layout.addLayout(hlayout_password, 1)
        hlayout_password.addWidget(QLabel('password', self))
        self.line_password = QLineEdit(self)
        hlayout_password.addWidget(self.line_password)

        hlayout = QHBoxLayout()
        layout.addLayout(hlayout, 1)
        self.button_save = QPushButton('Save')
        self.button_save.clicked.connect(self.ui_socks_save)
        hlayout.addWidget(self.button_save)
        self.button_cancel = QPushButton('Cancel')
        self.button_cancel.clicked.connect(self.close)
        hlayout.addWidget(self.button_cancel)

        self.setLayout(layout)

    def ui_shadowsocks_fill(self, data):
        print(data)

    def ui_shadowsocks_save(self):
        pass

    def ui_socks(self):
        layout = QVBoxLayout()
        
        hlayout_source_tag = QHBoxLayout()
        layout.addLayout(hlayout_source_tag, 1)
        hlayout_source_tag.addWidget(QLabel('source_tag', self))
        self.line_source_tag = QLineEdit(self)
        hlayout_source_tag.addWidget(self.line_source_tag)
        
        hlayout_source = QHBoxLayout()
        layout.addLayout(hlayout_source, 1)
        hlayout_source.addWidget(QLabel('source', self))
        self.line_source = QLineEdit(self)
        hlayout_source.addWidget(self.line_source)
        
        layout.addStretch(1)
        
        hlayout_tag = QHBoxLayout()
        layout.addLayout(hlayout_tag, 1)
        hlayout_tag.addWidget(QLabel('tag', self))
        self.line_tag = QLineEdit(self)
        hlayout_tag.addWidget(self.line_tag)

        hlayout_address = QHBoxLayout()
        layout.addLayout(hlayout_address, 1)
        hlayout_address.addWidget(QLabel('address*', self))
        self.line_address = QLineEdit(self)
        hlayout_address.addWidget(self.line_address)

        hlayout_port = QHBoxLayout()
        layout.addLayout(hlayout_port, 1)
        hlayout_port.addWidget(QLabel('port*', self))
        self.line_port = QLineEdit(self)
        self.line_port.setValidator(PortValidator(self))
        hlayout_port.addWidget(self.line_port)

        hlayout_user = QHBoxLayout()
        layout.addLayout(hlayout_user, 1)
        hlayout_user.addWidget(QLabel('user', self))
        self.line_user = QLineEdit(self)
        hlayout_user.addWidget(self.line_user)

        hlayout_password = QHBoxLayout()
        layout.addLayout(hlayout_password, 1)
        hlayout_password.addWidget(QLabel('password', self))
        self.line_password = QLineEdit(self)
        hlayout_password.addWidget(self.line_password)

        hlayout = QHBoxLayout()
        layout.addLayout(hlayout, 1)
        self.button_save = QPushButton('Save')
        self.button_save.clicked.connect(self.ui_socks_save)
        hlayout.addWidget(self.button_save)
        self.button_cancel = QPushButton('Cancel')
        self.button_cancel.clicked.connect(self.close)
        hlayout.addWidget(self.button_cancel)

        self.setLayout(layout)

    def ui_socks_fill(self, data):
        print(data)
        return
        with Globals.outbounds_lock:
            data = Globals.outbounds_dict.get(key, {})
        self.line_source_tag.setText(data.get('source_tag', ''))
        self.line_source.setText(data.get('source', ''))
        self.line_tag.setText(data.get('tag', ''))
        self.line_address.setText(data.get('address', ''))
        self.line_port.setText(data.get('port', ''))
        self.line_user.setText(data.get('user', ''))
        self.line_password.setText(data.get('password', ''))
        return data

    def ui_socks_save(self):
        source_tag = self.line_source_tag.text()
        source = self.line_source.text()

        address = self.line_address.text()
        if not address:
            QMessageBox.warning(self, 'Error!', 'Address field cannot be empty.')
            return
        if '.' not in address:
            QMessageBox.warning(self, 'Error!', 'Invalid address.')
            return
        
        port = self.line_port.text()
        key = f'{address}:{port}'
        with Globals.outbounds_lock:
            keys = list(Globals.outbounds_dict.keys())
        if bool(self.key) and self.key in keys:
            keys.remove(self.key)
        if not self.key:
            if key in keys:
                QMessageBox.warning(self, 'Error!', f'Duplicate entry found with key: {key}.')
                return
        
        with Globals.routing_used_outbounds_keys_lock:
            tags = Globals.routing_used_outbounds_keys.keys()
        tag = self.line_tag.text()
        if tag in tags:
            QMessageBox.warning(self, 'Error!', f'Duplicate tag found with {tag}.')
            return
        
        user = self.line_user.text()
        password = self.line_password.text()
        if (bool(user) != bool(password)):
            QMessageBox.warning(self, 'Error!', f'Either both User and Password must be filled or both empty.')
            return
        
        if self.key:
            self.row_signal.emit({
                'address': address,
                'password': password,
                'port': port,
                'protocol': 'socks',
                'source': source,
                'source_tag': source_tag,
                'tag': tag,
                'user': user
            }, self.row)
        else:
            with Globals.outbounds_lock:
                Globals.outbounds_dict[key] = {
                    'address': address,
                    'password': password,
                    'port': port,
                    'protocol': 'socks',
                    'source': source,
                    'source_tag': source_tag,
                    'tag': tag,
                    'user': user
                }
            self.row_signal.emit(key)

        self.close()

    def ui_trojan(self):
        layout = QVBoxLayout()
        
        hlayout_source_tag = QHBoxLayout()
        layout.addLayout(hlayout_source_tag, 1)
        hlayout_source_tag.addWidget(QLabel('source_tag', self))
        self.line_source_tag = QLineEdit(self)
        hlayout_source_tag.addWidget(self.line_source_tag)
        
        hlayout_source = QHBoxLayout()
        layout.addLayout(hlayout_source, 1)
        hlayout_source.addWidget(QLabel('source', self))
        self.line_source = QLineEdit(self)
        hlayout_source.addWidget(self.line_source)
        
        layout.addStretch(1)
        
        hlayout_tag = QHBoxLayout()
        layout.addLayout(hlayout_tag, 1)
        hlayout_tag.addWidget(QLabel('tag', self))
        self.line_tag = QLineEdit(self)
        hlayout_tag.addWidget(self.line_tag)

        hlayout_address = QHBoxLayout()
        layout.addLayout(hlayout_address, 1)
        hlayout_address.addWidget(QLabel('address*', self))
        self.line_address = QLineEdit(self)
        hlayout_address.addWidget(self.line_address)

        hlayout_port = QHBoxLayout()
        layout.addLayout(hlayout_port, 1)
        hlayout_port.addWidget(QLabel('port*', self))
        self.line_port = QLineEdit(self)
        self.line_port.setValidator(PortValidator(self))
        hlayout_port.addWidget(self.line_port)

        hlayout_user = QHBoxLayout()
        layout.addLayout(hlayout_user, 1)
        hlayout_user.addWidget(QLabel('user', self))
        self.line_user = QLineEdit(self)
        hlayout_user.addWidget(self.line_user)

        hlayout_password = QHBoxLayout()
        layout.addLayout(hlayout_password, 1)
        hlayout_password.addWidget(QLabel('password', self))
        self.line_password = QLineEdit(self)
        hlayout_password.addWidget(self.line_password)

        hlayout = QHBoxLayout()
        layout.addLayout(hlayout, 1)
        self.button_save = QPushButton('Save')
        self.button_save.clicked.connect(self.ui_trojan_save)
        hlayout.addWidget(self.button_save)
        self.button_cancel = QPushButton('Cancel')
        self.button_cancel.clicked.connect(self.close)
        hlayout.addWidget(self.button_cancel)

        self.setLayout(layout)

    def ui_trojan_fill(self, data):
        print(data)

    def ui_trojan_save(self):
        pass

    def ui_vless(self):
        layout = QVBoxLayout()
        
        hlayout_source_tag = QHBoxLayout()
        layout.addLayout(hlayout_source_tag, 1)
        hlayout_source_tag.addWidget(QLabel('source_tag', self))
        self.line_source_tag = QLineEdit(self)
        hlayout_source_tag.addWidget(self.line_source_tag)
        
        hlayout_source = QHBoxLayout()
        layout.addLayout(hlayout_source, 1)
        hlayout_source.addWidget(QLabel('source', self))
        self.line_source = QLineEdit(self)
        hlayout_source.addWidget(self.line_source)
        
        layout.addStretch(1)
        
        hlayout_tag = QHBoxLayout()
        layout.addLayout(hlayout_tag, 1)
        hlayout_tag.addWidget(QLabel('tag', self))
        self.line_tag = QLineEdit(self)
        hlayout_tag.addWidget(self.line_tag)

        hlayout_address = QHBoxLayout()
        layout.addLayout(hlayout_address, 1)
        hlayout_address.addWidget(QLabel('address*', self))
        self.line_address = QLineEdit(self)
        hlayout_address.addWidget(self.line_address)

        hlayout_port = QHBoxLayout()
        layout.addLayout(hlayout_port, 1)
        hlayout_port.addWidget(QLabel('port*', self))
        self.line_port = QLineEdit(self)
        self.line_port.setValidator(PortValidator(self))
        hlayout_port.addWidget(self.line_port)

        hlayout_user = QHBoxLayout()
        layout.addLayout(hlayout_user, 1)
        hlayout_user.addWidget(QLabel('user', self))
        self.line_user = QLineEdit(self)
        hlayout_user.addWidget(self.line_user)

        hlayout_password = QHBoxLayout()
        layout.addLayout(hlayout_password, 1)
        hlayout_password.addWidget(QLabel('password', self))
        self.line_password = QLineEdit(self)
        hlayout_password.addWidget(self.line_password)

        hlayout = QHBoxLayout()
        layout.addLayout(hlayout, 1)
        self.button_save = QPushButton('Save')
        self.button_save.clicked.connect(self.ui_socks_save)
        hlayout.addWidget(self.button_save)
        self.button_cancel = QPushButton('Cancel')
        self.button_cancel.clicked.connect(self.close)
        hlayout.addWidget(self.button_cancel)

        self.setLayout(layout)

    def ui_vless_fill(self, data):
        print(data)

    def ui_vless_save(self):
        pass

    def ui_vmess(self):
        layout = QVBoxLayout()
        
        hlayout_source_tag = QHBoxLayout()
        layout.addLayout(hlayout_source_tag, 1)
        hlayout_source_tag.addWidget(QLabel('source_tag', self))
        self.line_source_tag = QLineEdit(self)
        hlayout_source_tag.addWidget(self.line_source_tag)
        
        hlayout_source = QHBoxLayout()
        layout.addLayout(hlayout_source, 1)
        hlayout_source.addWidget(QLabel('source', self))
        self.line_source = QLineEdit(self)
        hlayout_source.addWidget(self.line_source)
        
        layout.addStretch(1)
        
        hlayout_tag = QHBoxLayout()
        layout.addLayout(hlayout_tag, 1)
        hlayout_tag.addWidget(QLabel('tag', self))
        self.line_tag = QLineEdit(self)
        hlayout_tag.addWidget(self.line_tag)

        hlayout_address = QHBoxLayout()
        layout.addLayout(hlayout_address, 1)
        hlayout_address.addWidget(QLabel('address*', self))
        self.line_address = QLineEdit(self)
        hlayout_address.addWidget(self.line_address)

        hlayout_port = QHBoxLayout()
        layout.addLayout(hlayout_port, 1)
        hlayout_port.addWidget(QLabel('port*', self))
        self.line_port = QLineEdit(self)
        self.line_port.setValidator(PortValidator(self))
        hlayout_port.addWidget(self.line_port)

        hlayout_user = QHBoxLayout()
        layout.addLayout(hlayout_user, 1)
        hlayout_user.addWidget(QLabel('user', self))
        self.line_user = QLineEdit(self)
        hlayout_user.addWidget(self.line_user)

        hlayout_password = QHBoxLayout()
        layout.addLayout(hlayout_password, 1)
        hlayout_password.addWidget(QLabel('password', self))
        self.line_password = QLineEdit(self)
        hlayout_password.addWidget(self.line_password)

        hlayout = QHBoxLayout()
        layout.addLayout(hlayout, 1)
        self.button_save = QPushButton('Save')
        self.button_save.clicked.connect(self.ui_socks_save)
        hlayout.addWidget(self.button_save)
        self.button_cancel = QPushButton('Cancel')
        self.button_cancel.clicked.connect(self.close)
        hlayout.addWidget(self.button_cancel)

        self.setLayout(layout)

    def ui_vmess_fill(self, data):
        print(data)

    def ui_vmess_save(self):
        pass

class PortValidator(QIntValidator):
    def __init__(self, parent=None):
        super().__init__(parent)

    def fixup(self, input):
        try:
            port = int(input)
            if port < 1:
                return '1'
            elif port > 65535:
                return '65535'
        except ValueError:
            return '1'

    def validate(self, input, pos):
        if not input:
            return QValidator.State.Intermediate, input, pos

        try:
            port = int(input)
        except ValueError:
            return QValidator.State.Invalid, input, pos

        if 1 <= port <= 65535:
            return QValidator.State.Acceptable, input, pos
        else:
            return QValidator.State.Invalid, input, pos