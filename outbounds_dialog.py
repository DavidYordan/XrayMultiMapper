import os
from PyQt6.QtCore import (
    QRegularExpression,
    Qt
)
from PyQt6.QtGui import (
    QIntValidator,
    QRegularExpressionValidator,
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
    QVBoxLayout
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
        self.bindings_protocol = {}
        self.bindings_transport = {}
        self.columns = []
        self.old_data = {}
        self.protocol = protocol
        self.protocol_rows = ProtocolRows(self)
        self.row = row
        self.row_signal = row_signal
        self.widgets_protocol = {}
        self.widgets_protocol_extend = {}
        self.widgets_transport = {}
        self.widgets_transport_extend = {}

        self.setWindowTitle(f"{self.protocol.capitalize()} Configuration")
        self.setModal(True)
        self.setup_ui()

        if self.row != -1:
            self.old_data = self.fill_data()

        self.exec()

        Globals._Log.info(self.user, f'{self.protocol} dialog successfully initialized.')

    def setup_ui(self):
        layout_main = QVBoxLayout(self)
        layout_main_top = QHBoxLayout()
        layout_main.addLayout(layout_main_top)
        layout_main_bottom = QHBoxLayout()
        layout_main.addLayout(layout_main_bottom)
        
        protocol_params, self.bindings_protocol = getattr(self.protocol_rows, self.protocol)
        
        layout_protocol = QVBoxLayout()
        layout_protocol.setAlignment(Qt.AlignmentFlag.AlignTop)
        layout_main_top.addLayout(layout_protocol)
        for param in protocol_params:
            vlayout = QVBoxLayout()
            hlayout = QHBoxLayout()
            
            label_text = f"{param['key']}{'*' if param['required'] else ''}"
            label = QLabel(label_text)
            hlayout.addWidget(label)

            widget = None
            if param['widget'] == QLineEdit:
                widget = QLineEdit(self)
                if 'validator' in param:
                    widget.setValidator(param['validator'])
                    widget.textChanged.connect(lambda text, widget=widget: self.on_text_changed(text, widget))
                if 'default' in param:
                    widget.setText(param['default'])
            elif param['widget'] == QComboBox:
                widget = QComboBox(self)
                widget.addItems(param['options'])
                widget.setCurrentText(param['default'])
                if 'allowedEdit' in param and param['allowedEdit']:
                    widget.setEditable(True)
                if param['key'] in self.bindings_protocol:
                    widget.currentTextChanged.connect(lambda value, key=param['key'], vlayout=vlayout: self.on_protocol_combobox_changed(value, key, vlayout))

            self.widgets_protocol[param['key']] = widget
            hlayout.addWidget(widget)
            vlayout.addLayout(hlayout)
            if param['widget'] == QComboBox:
                self.on_protocol_combobox_changed(param['default'], param['key'], vlayout)
            layout_protocol.addLayout(vlayout)

        transport_params, self.bindings_transport = getattr(self.protocol_rows, 'transport')

        for param in transport_params:
            layout_transport = QVBoxLayout()
            layout_transport.setAlignment(Qt.AlignmentFlag.AlignTop)
            layout_main_top.addLayout(layout_transport)
            vlayout = QVBoxLayout()
            hlayout = QHBoxLayout()
            
            label_text = f"{param['key']}{'*' if param['required'] else ''}"
            label = QLabel(label_text)
            hlayout.addWidget(label)

            widget = None
            if param['widget'] == QLineEdit:
                widget = QLineEdit(self)
                if 'validator' in param:
                    widget.setValidator(param['validator'])
                    widget.textChanged.connect(lambda text, widget=widget: self.on_text_changed(text, widget))
                if 'default' in param:
                    widget.setText(param['default'])
            elif param['widget'] == QComboBox:
                widget = QComboBox(self)
                widget.addItems(param['options'])
                widget.setCurrentText(param['default'])
                if 'allowedEdit' in param and param['allowedEdit']:
                    widget.setEditable(True)
                if param['key'] in self.bindings_transport:
                    widget.currentTextChanged.connect(lambda value, key=param['key'], vlayout=vlayout: self.on_transport_combobox_changed(value, key, vlayout))

            self.widgets_transport[param['key']] = widget
            hlayout.addWidget(widget)
            vlayout.addLayout(hlayout)
            if param['widget'] == QComboBox:
                self.on_transport_combobox_changed(param['default'], param['key'], vlayout)
            layout_transport.addLayout(vlayout)

        buttons_layout = QHBoxLayout()
        layout_main_bottom.addLayout(buttons_layout)
        ok_button = QPushButton("OK", self)
        ok_button.clicked.connect(self.on_ok_clicked)
        cancel_button = QPushButton("Cancel", self)
        cancel_button.clicked.connect(self.reject)
        buttons_layout.addWidget(ok_button)
        buttons_layout.addWidget(cancel_button)

        self.setLayout(layout_main)

    def add_protocol_widget(self, key, param, vlayout):
        hlayout = QHBoxLayout()
        label = QLabel(f"{param['key']}{'*' if param['required'] else ''}")
        hlayout.addWidget(label)
        widget = self.create_widget(param)
        hlayout.addWidget(widget)
        vlayout.addLayout(hlayout)
        self.widgets_protocol_extend[key][param['key']] = [label, widget, hlayout]

    def add_transport_widget(self, key, param, vlayout):
        hlayout = QHBoxLayout()
        label = QLabel(f"{param['key']}{'*' if param['required'] else ''}")
        hlayout.addWidget(label)
        widget = self.create_widget(param)
        hlayout.addWidget(widget)
        vlayout.addLayout(hlayout)
        self.widgets_transport_extend[key][param['key']] = [label, widget, hlayout]

    def create_widget(self, param):
        widget = None
        if param['widget'] == QLineEdit:
            widget = QLineEdit(self)
            if 'validator' in param:
                widget.setValidator(param['validator'])
                widget.textChanged.connect(lambda text, widget=widget: self.on_text_changed(text, widget))
            if 'default' in param:
                widget.setText(param['default'])
        elif param['widget'] == QComboBox:
            widget = QComboBox(self)
            widget.addItems(param['options'])
            widget.setCurrentText(param['default'])
            if 'allowedEdit' in param and param['allowedEdit']:
                widget.setEditable(True)
        return widget

    def extract_data(self):
        data = {}
        for key, widget in self.widgets_protocol.items():
            if isinstance(widget, QLineEdit):
                data[key] = widget.text()
            elif isinstance(widget, QComboBox):
                data[key] = widget.currentText()

        for key, items in self.widgets_protocol_extend.items():
            for k, item in items.items():
                if isinstance(item[1], QLineEdit):
                    data[f'{key}:{k}'] = item[1].text()
                elif isinstance(item[1], QComboBox):
                    data[f'{key}:{k}'] = item[1].currentText()

        for key, widget in self.widgets_transport.items():
            if isinstance(widget, QLineEdit):
                data[f'network:{key}'] = widget.text()
            elif isinstance(widget, QComboBox):
                data[f'network:{key}'] = widget.currentText()

        for key, items in self.widgets_transport_extend.items():
            for k, item in items.items():
                if isinstance(item[1], QLineEdit):
                    data[f'{key}:{k}'] = item[1].text()
                elif isinstance(item[1], QComboBox):
                    data[f'{key}:{k}'] = item[1].currentText()

        return data

    def fill_data(self):
        data = self.get_data()
        print(data)
        address = data['address']
        port = data['port']
        key = f'{address}:{port}'
        print(Globals.outbounds_dict[key])

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

    def on_ok_clicked(self):
        if not self.validate_data():
            return

        data = self.extract_data()

        if not self.validate_on_parent(data):
            return
        
        self.process_data(data)
        
        self.accept()

    def on_protocol_combobox_changed(self, value, key, vlayout):
        if key in self.widgets_protocol_extend:
            self.remove_protocol_binding_widgets(key)

        if key in self.bindings_protocol:
            if value in self.bindings_protocol[key]:
                self.widgets_protocol_extend[key] = {}
                for param in self.bindings_protocol[key][value]:
                    self.add_protocol_widget(key, param, vlayout)

        self.adjustSize()

    def on_text_changed(self, text, widget: QLineEdit):
        validator = widget.validator()
        state = validator.validate(text, 0)[0]
        if state == validator.State.Acceptable:
            widget.setStyleSheet("")
        else:
            widget.setStyleSheet("border: 2px solid red;")

    def on_transport_combobox_changed(self, value, key, vlayout):
        if key in self.widgets_transport_extend:
            self.remove_transport_binding_widgets(key)

        if key in self.bindings_transport:
            if value in self.bindings_transport[key]:
                self.widgets_transport_extend[key] = {}
                for param in self.bindings_transport[key][value]:
                    self.add_transport_widget(key, param, vlayout)

        self.adjustSize()

    def process_data(self, data):
        print(data)

    def remove_protocol_binding_widgets(self, key):
        for _, items in self.widgets_protocol_extend[key].items():
            for item in items:
                item.deleteLater()
        del self.widgets_protocol_extend[key]

    def remove_transport_binding_widgets(self, key):
        for _, items in self.widgets_transport_extend[key].items():
            for item in items:
                item.deleteLater()
        del self.widgets_transport_extend[key]

    def validate_data(self):
        all_valid = set()
        for key, widget in self.widgets_protocol.items():
            if isinstance(widget, QLineEdit):
                all_valid.add(self.validate_widget(widget))
            if key not in self.widgets_protocol_extend:
                continue
            for _, items in self.widgets_protocol_extend[key].items():
                if isinstance(items[1], QLineEdit):
                    all_valid.add(self.validate_widget(items[1]))

        for key, widget in self.widgets_transport.items():
            if isinstance(widget, QLineEdit):
                all_valid.add(self.validate_widget(widget))
            if key not in self.widgets_transport_extend:
                continue
            for _, items in self.widgets_transport_extend[key].items():
                if isinstance(items[1], QLineEdit):
                    all_valid.add(self.validate_widget(items[1]))

        return False if 'F' in all_valid else True

    def validate_on_parent(self, data):
        duplicate_row = self.parent().valid_key(self.row, data['address'], data['port'])
        if duplicate_row != -1:
            QMessageBox.warning(None, 'Error!', f"Duplicated {data['address']}:{data['port']} with row: {duplicate_row+1}")
            return False
        duplicate_row = self.parent().valid_remarks(self.row, data['remarks'])
        if duplicate_row != -1:
            QMessageBox.warning(None, 'Error!', f"Duplicated {data['remarks']} with row: {duplicate_row+1}")
            return False
        return True

    def validate_widget(self, widget):
        if widget.hasAcceptableInput():
            return 'T'
        widget.setStyleSheet("border: 2px solid red;")
        return 'F'


class ProtocolRows(object):
    def __init__(self, parent):
        self.parent = parent

    @property
    def shadowsocks(self):
        return [
            {'key': 'source_tag', 'required': False, 'widget': QLineEdit, 'validator': ForbiddenCharValidator(self.parent, ['|'])},
            {'key': 'source', 'required': False, 'widget': QLineEdit},
            {'key': 'remarks', 'required': False, 'widget': QLineEdit, 'validator': ForbiddenCharValidator(self.parent, ['|'])},
            {'key': 'email', 'required': False, 'widget': QLineEdit, 'validator': EmailValidator(self.parent)},
            {'key': 'address', 'required': True, 'widget': QLineEdit, 'validator': AddressValidator(self.parent, True)},
            {'key': 'port', 'required': True, 'widget': QLineEdit, 'validator': IntValidator(1, 65535, self.parent, True)},
            {'key': 'encryption', 'required': False, 'widget': QComboBox, 'options': [
                    '2022-blake3-aes-128-gcm', '2022-blake3-aes-256-gcm', '2022-blake3-chacha20-poly1305', 'aes-128-gcm', 'aes-256-gcm',
                    'chacha20-ietf-poly1305', 'chacha20-poly1305', 'none', 'plain', 'xchacha20-ietf-poly1305', 'xchacha20-poly1305'
                ], 'default': 'none'
            },
            {'key': 'password', 'required': True, 'widget': QLineEdit, 'validator': RequiredValidator(self.parent)},
            {'key': 'uot', 'required': False, 'widget': QComboBox, 'options': ['True', 'False'], 'default': 'True'},
            {'key': 'level', 'required': True, 'widget': QLineEdit, 'validator': IntValidator(0, 99, self.parent, True), 'default': '0'}
        ], {
            'uot': {
                'True': [{'key': 'UoTVersion', 'required': False, 'widget': QComboBox, 'options': ['1', '2'], 'default': '2'}]
            }
        }
    
    @property
    def socks(self):
        return [
            {'key': 'source_tag', 'required': False, 'widget': QLineEdit, 'validator': ForbiddenCharValidator(self.parent, ['|'])},
            {'key': 'source', 'required': False, 'widget': QLineEdit},
            {'key': 'remarks', 'required': False, 'widget': QLineEdit, 'validator': ForbiddenCharValidator(self.parent, ['|'])},
            {'key': 'address', 'required': True, 'widget': QLineEdit, 'validator': AddressValidator(self.parent, True)},
            {'key': 'port', 'required': True, 'widget': QLineEdit, 'validator': IntValidator(1, 65535, self.parent, True)},
            {'key': 'user', 'required': False, 'widget': QLineEdit},
            {'key': 'password', 'required': False, 'widget': QLineEdit},
            {'key': 'level', 'required': True, 'widget': QLineEdit, 'validator': IntValidator(0, 99, self.parent, True), 'default': '0'}
        ], {}
    
    @property
    def trojan(self):
        return [
            {'key': 'source_tag', 'required': False, 'widget': QLineEdit, 'validator': ForbiddenCharValidator(self.parent, ['|'])},
            {'key': 'source', 'required': False, 'widget': QLineEdit},
            {'key': 'remarks', 'required': False, 'widget': QLineEdit, 'validator': ForbiddenCharValidator(self.parent, ['|'])},
            {'key': 'email', 'required': False, 'widget': QLineEdit, 'validator': EmailValidator(self.parent)},
            {'key': 'address', 'required': True, 'widget': QLineEdit, 'validator': AddressValidator(self.parent, True)},
            {'key': 'port', 'required': True, 'widget': QLineEdit, 'validator': IntValidator(1, 65535, self.parent, True)},
            {'key': 'password', 'required': True, 'widget': QLineEdit, 'validator': RequiredValidator(self.parent)},
            {'key': 'level', 'required': True, 'widget': QLineEdit, 'validator': IntValidator(0, 99, self.parent, True), 'default': '0'}
        ], {}
    
    @property
    def vless(self):
        return [
            {'key': 'source_tag', 'required': False, 'widget': QLineEdit, 'validator': ForbiddenCharValidator(self.parent, ['|'])},
            {'key': 'source', 'required': False, 'widget': QLineEdit},
            {'key': 'remarks', 'required': False, 'widget': QLineEdit, 'validator': ForbiddenCharValidator(self.parent, ['|'])},
            {'key': 'address', 'required': True, 'widget': QLineEdit, 'validator': AddressValidator(self.parent, True)},
            {'key': 'port', 'required': True, 'widget': QLineEdit, 'validator': IntValidator(1, 65535, self.parent, True)},
            {'key': 'id', 'required': True, 'widget': QLineEdit, 'validator': ByteLengthValidator(29, self.parent, True)},
            {'key': 'encryption', 'required': False, 'widget': QComboBox, 'options': [
                    '2022-blake3-aes-128-gcm', '2022-blake3-aes-256-gcm', '2022-blake3-chacha20-poly1305', 'aes-128-gcm', 'aes-256-gcm',
                    'chacha20-ietf-poly1305', 'chacha20-poly1305', 'none', 'plain', 'xchacha20-ietf-poly1305', 'xchacha20-poly1305'
                ], 'default': 'none'
            },
            {'key': 'flow', 'required': False, 'widget': QComboBox, 'options': [
                    'none', 'xtls-rprx-vision', 'xtls-rprx-vision-udp443'
                ], 'default': 'none'
            },
            {'key': 'level', 'required': True, 'widget': QLineEdit, 'validator': IntValidator(0, 99, self.parent, True), 'default': '0'}
        ], {}
    
    @property
    def vmess(self):
        return [
            {'key': 'source_tag', 'required': False, 'widget': QLineEdit, 'validator': ForbiddenCharValidator(self.parent, ['|'])},
            {'key': 'source', 'required': False, 'widget': QLineEdit},
            {'key': 'remarks', 'required': False, 'widget': QLineEdit, 'validator': ForbiddenCharValidator(self.parent, ['|'])},
            {'key': 'address', 'required': True, 'widget': QLineEdit, 'validator': AddressValidator(self.parent, True)},
            {'key': 'port', 'required': True, 'widget': QLineEdit, 'validator': IntValidator(1, 65535, self.parent, True)},
            {'key': 'id', 'required': True, 'widget': QLineEdit, 'validator': ByteLengthValidator(29, self.parent, True)},
            {'key': 'security', 'required': False, 'widget': QComboBox, 'options': [
                    'auto', 'aes-128-gcm', 'chacha20-poly1305', 'none', 'zero'
                ], 'default': 'auto'
            },
            {'key': 'level', 'required': True, 'widget': QLineEdit, 'validator': IntValidator(0, 99, self.parent, True), 'default': '0'}
        ], {}
    
    @property
    def transport(self):
        return [
            {'key': 'network', 'required': False, 'widget': QComboBox, 'options': [
                    'domainsocket', 'grpc', 'http', 'kcp', 'quic', 'tcp', 'ws'
                ], 'default': 'tcp'
            },
            {'key': 'security', 'required': False, 'widget': QComboBox, 'options': [
                    'none', 'tls', 'reality'
                ], 'default': 'none'
            },
            {'key': 'sockopt', 'required': False, 'widget': QComboBox, 'options': ['True', 'False'], 'default': 'False'}
        ], {
            'network': {
                'domainsocket': [
                    {'key': 'path', 'required': True, 'widget': QLineEdit, 'validator': PathValidator(self.parent, True)},
                    {'key': 'abstract', 'required': False, 'widget': QComboBox, 'options': ['True', 'False'], 'default': 'False'},
                    {'key': 'padding', 'required': False, 'widget': QComboBox, 'options': ['True', 'False'], 'default': 'False'}
                ],
                'grpc': [
                    {'key': 'serviceName', 'required': False, 'widget': QLineEdit},
                    {'key': 'multiMode', 'required': False, 'widget': QComboBox, 'options': ['True', 'False'], 'default': 'False'},
                    {'key': 'user_agent', 'required': False, 'widget': QLineEdit},
                    {'key': 'idle_timeout', 'required': False, 'widget': QLineEdit, 'default': '60', 'validator': IntValidator(10, 1440, self.parent)},
                    {'key': 'health_check_timeout', 'required': False, 'widget': QLineEdit, 'default': '20', 'validator': IntValidator(0, 1440, self.parent)},
                    {'key': 'permit_without_stream', 'required': False, 'widget': QComboBox, 'options': ['True', 'False'], 'default': 'False'},
                    {'key': 'initial_windows_size', 'required': False, 'widget': QLineEdit, 'default': '0', 'validator': IntValidator(0, 99999, self.parent)}
                ],
                'http': [
                    {'key': 'host', 'required': False, 'widget': QLineEdit},
                    {'key': 'path', 'required': False, 'widget': QLineEdit, 'default': '/'},
                    {'key': 'read_idle_timeout', 'required': False, 'widget': QLineEdit, 'default': '60', 'validator': IntValidator(10, 1440, self.parent)},
                    {'key': 'health_check_timeout', 'required': False, 'widget': QLineEdit, 'default': '15', 'validator': IntValidator(0, 1440, self.parent)},
                    {'key': 'method', 'required': False, 'widget': QComboBox, 'options': [
                            'CONNECT', 'DELETE', 'GET', 'HEAD', 'OPTIONS', 'PATCH', 'POST', 'PUT', 'TRACE'
                        ], 'default': 'PUT'},
                    {'key': 'Header', 'required': False, 'widget': QLineEdit}
                ],
                'kcp': [
                    {'key': 'mtu', 'required': True, 'widget': QLineEdit, 'default': '1350', 'validator': IntValidator(576, 1460, self.parent, True)},
                    {'key': 'tti', 'required': True, 'widget': QLineEdit, 'default': '50', 'validator': IntValidator(10, 100, self.parent, True)},
                    {'key': 'uplinkCapacity', 'required': True, 'widget': QLineEdit, 'default': '20', 'validator': IntValidator(0, 9999, self.parent, True)},
                    {'key': 'downlinkCapacity', 'required': True, 'widget': QLineEdit, 'default': '100', 'validator': IntValidator(0, 9999, self.parent, True)},
                    {'key': 'congestion', 'required': False, 'widget': QComboBox, 'options': ['True', 'False'], 'default': 'False'},
                    {'key': 'readBufferSize', 'required': True, 'widget': QLineEdit, 'default': '2', 'validator': IntValidator(0, 9999, self.parent, True)},
                    {'key': 'writeBufferSize', 'required': True, 'widget': QLineEdit, 'default': '2', 'validator': IntValidator(0, 9999, self.parent, True)},
                    {'key': 'type', 'required': False, 'widget': QComboBox, 'options': [
                            'dtls', 'none', 'srtp', 'utp', 'wechat-video', 'wireguard'
                        ], 'default': 'none'
                    },
                    {'key': 'seed', 'required': False, 'widget': QLineEdit}
                ],
                'quic': [
                    {'key': 'security', 'required': False, 'widget': QComboBox, 'options': ['aes-128-gcm', 'none', 'chacha20-poly1305'], 'default': 'none'},
                    {'key': 'type', 'required': False, 'widget': QComboBox, 'options': [
                            'dtls', 'none', 'srtp', 'utp', 'wechat-video', 'wireguard'
                        ], 'default': 'none'
                    },
                    {'key': 'key', 'required': False, 'widget': QLineEdit}
                ],
                'tcp': [
                    {'key': 'acceptProxyProtocol', 'required': False, 'widget': QComboBox, 'options': ['True', 'False'], 'default': 'False'},
                    {'key': 'type', 'required': False, 'widget': QComboBox, 'options': ['http', 'none'], 'default': 'none'},
                    {'key': 'host', 'required': False, 'widget': QLineEdit},
                    {'key': 'path', 'required': False, 'widget': QLineEdit}
                ],
                'ws': [
                    {'key': 'acceptProxyProtocol', 'required': False, 'widget': QComboBox, 'options': ['True', 'False'], 'default': 'False'},
                    {'key': 'path', 'required': False, 'widget': QLineEdit, 'default': '/'},
                    {'key': 'Host', 'required': False, 'widget': QLineEdit}
                ]
            },
            'security': {
                'tls': [
                    {'key': 'serviceName', 'required': True, 'widget': QLineEdit, 'validator': AddressValidator(self.parent, True)},
                    {'key': 'rejectUnknownSni', 'required': False, 'widget': QComboBox, 'options': ['True', 'False'], 'default': 'False'},
                    {'key': 'allowInsecure', 'required': False, 'widget': QComboBox, 'options': ['True', 'False'], 'default': 'False'},
                    {'key': 'alpn', 'required': False, 'widget': QComboBox, 'options': ['h2', 'http/1.1', 'h2,http/1.1'], 'default': 'h2,http/1.1'},
                    {'key': 'minVersion', 'required': False, 'widget': QComboBox, 'options': ['1.0', '1.1', '1.2', '1.3'], 'default': '1.2'},
                    {'key': 'maxVersion', 'required': False, 'widget': QComboBox, 'options': ['1.0', '1.1', '1.2', '1.3'], 'default': '1.3'},
                    {'key': 'cipherSuites', 'required': False, 'widget': QLineEdit},
                    {'key': 'certificates', 'required': False, 'widget': QLineEdit},
                    {'key': 'disableSystemRoot', 'required': False, 'widget': QComboBox, 'options': ['True', 'False'], 'default': 'False'},
                    {'key': 'enableSessionResumption', 'required': False, 'widget': QComboBox, 'options': ['True', 'False'], 'default': 'False'},
                    {'key': 'fingerprint', 'required': False, 'widget': QComboBox, 'options': [
                            '360', 'android', 'chrome', 'edge', 'firefox', 'ios', 'qq', 'random', 'randomized', 'safari'
                        ], 'default': 'random', 'allowedEdit': True
                    },
                    {'key': 'pinnedPeerCertificateChainSha256', 'required': False, 'widget': QLineEdit}
                ],
                'reality': [
                    {'key': 'serverName', 'required': True, 'widget': QLineEdit, 'validator': RequiredValidator(self.parent)},
                    {'key': 'fingerprint', 'required': False, 'widget': QComboBox, 'options': [
                            '360', 'android', 'chrome', 'edge', 'firefox', 'ios', 'qq', 'random', 'randomized', 'safari'
                        ], 'default': 'random', 'allowedEdit': True
                    },
                    {'key': 'publicKey', 'required': True, 'widget': QLineEdit, 'validator': RequiredValidator(self.parent)},
                    {'key': 'shortId', 'required': True, 'widget': QLineEdit, 'validator': RequiredValidator(self.parent)},
                    {'key': 'spiderX', 'required': False, 'widget': QLineEdit}
                ]
            },
            'sockopt': {
                'True': [
                    {'key': 'mark', 'required': True, 'widget': QLineEdit, 'default': '0', 'validator': QIntValidator(self.parent)},
                    {'key': 'tcpMaxSeg', 'required': False, 'widget': QLineEdit, 'default': '1440'},
                    {'key': 'tcpFastOpen', 'required': False, 'widget': QComboBox, 'options': ['True', 'False', '0'], 'default': '0'},
                    {'key': 'tproxy', 'required': False, 'widget': QComboBox, 'options': ['off', 'redirect', 'tproxy'], 'default': 'off'},
                    {'key': 'domainStrategy', 'required': False, 'widget': QComboBox, 'options': ['AsIs', 'UseIP', 'UseIPv4', 'UseIPv6'], 'default': 'AsIs'},
                    {'key': 'dialerProxy', 'required': False, 'widget': QLineEdit},
                    {'key': 'acceptProxyProtocol', 'required': False, 'widget': QComboBox, 'options': ['True', 'False'], 'default': 'False'},
                    {'key': 'tcpKeepAliveInterval', 'required': False, 'widget': QLineEdit, 'default': '0', 'validator': IntValidator(0, 1440, self.parent)},
                    {'key': 'tcpKeepAliveIdle', 'required': False, 'widget': QLineEdit, 'default': '0', 'validator': IntValidator(0, 1440, self.parent)},
                    {'key': 'tcpUserTimeout', 'required': False, 'widget': QLineEdit, 'default': '10000', 'validator': QIntValidator(self.parent)},
                    {'key': 'tcpcongestion', 'required': False, 'widget': QComboBox, 'options': ['', 'bbr', 'cubic', 'reno'], 'default': ''},
                    {'key': 'interface', 'required': False, 'widget': QLineEdit, 'default': 'wg0'},
                    {'key': 'V6Only', 'required': False, 'widget': QComboBox, 'options': ['True', 'False'], 'default': 'False'}
                ]
            }
        }
    
class AddressValidator(QRegularExpressionValidator):
    def __init__(self, parent, required=False):
        super().__init__(parent)
        address_regex = QRegularExpression(
            r"^(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}"
            r"(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$|"
            r"^(?:(?:[a-zA-Z0-9-]+\.)*[a-zA-Z]{2,})$"
        )
        self.required = required
        self.setRegularExpression(address_regex)

    def validate(self, string, pos):
        if not self.required and string == "":
            return QValidator.State.Acceptable, string, pos
        return super().validate(string, pos)

class ByteLengthValidator(QValidator):
    def __init__(self, max_length, parent, required=False):
        super().__init__(parent)
        self.max_length = max_length
        self.required = required

    def validate(self, string, pos):
        if not self.required and string == "":
            return QValidator.State.Acceptable, string, pos
        byte_length = len(string.encode('utf-8'))
        if byte_length > self.max_length:
            return QValidator.State.Invalid, string, pos
        else:
            return QValidator.State.Acceptable, string, pos

    def fixup(self, string):
        return string[:self.max_length]

class EmailValidator(QRegularExpressionValidator):
    def __init__(self, parent, required=False):
        super().__init__(parent)
        email_regex = QRegularExpression("[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}")
        self.required = required
        self.setRegularExpression(email_regex)

    def validate(self, string, pos):
        if not self.required and string == "":
            return QValidator.State.Acceptable, string, pos
        return super().validate(string, pos)

class ForbiddenCharValidator(QValidator):
    def __init__(self, parent, forbidden_chars, required=False):
        super().__init__(parent)
        self.forbidden_chars = forbidden_chars
        self.required = required

    def fixup(self, string):
        for char in self.forbidden_chars:
            string = string.replace(char, "")
        return string

    def validate(self, string, pos):
        if not self.required and string == "":
            return QValidator.State.Acceptable, string, pos
        for char in self.forbidden_chars:
            if char in string:
                return QValidator.State.Invalid, string, pos
        return QValidator.State.Acceptable, string, pos

class IntValidator(QIntValidator):
    def __init__(self, min, max, parent, required=False):
        super().__init__(min, max, parent)
        self.required = required

    def validate(self, string, pos):
        if not self.required and string == "":
            return QValidator.State.Acceptable, string, pos
        return super().validate(string, pos)
    
class PathValidator(QValidator):
    def __init__(self, parent, required=False):
        super().__init__(parent)
        self.required = required

    def validate(self, string, pos):
        if not self.required and string == "":
            return QValidator.State.Acceptable, string, pos

        if os.path.isabs(string) and os.path.exists(os.path.dirname(string)):
            return QValidator.State.Acceptable, string, pos
        else:
            return QValidator.State.Invalid, string, pos
    
class RequiredValidator(QValidator):
    def __init__(self, parent):
        super().__init__(parent)

    def validate(self, string, pos):
        if string == "":
            return QValidator.State.Intermediate, string, pos
        else:
            return QValidator.State.Acceptable, string, pos