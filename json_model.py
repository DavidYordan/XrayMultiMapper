class JsonModel(object):
    @property
    def inbound(self):
        return {
            "port": 0,
            "listen": "0.0.0.0",
            "protocol": "socks",
            "settings": {},
            "tag": "tag"
        }
    
    @property
    def inbound_settings_http(self):
        return {
            "timeout": 0,
            "allowTransparent": False,
            "userLevel": 0
        }
    
    @property
    def inbound_settings_socks(self):
        return {
            "auth": "noauth",
            "udp": True,
            "ip": "127.0.0.1",
            "userLevel": 0
        }
    
    @property
    def log(self):
        return {
            "access": "log.log",
            "error": "error.log",
            "loglevel": "warning"
        }
    
    @property
    def main(self):
        return {
            "log": {},
            "routing": {},
            "inbounds": [],
            "outbounds": []
        }
    
    @property
    def outbound(self):
        return {
            "protocol": "socks",
            "settings": {},
            "tag": "tag"
        }
    
    @property
    def outbound_settings_shadowsocks(self):
        return {
            "servers": [{
                "address": "",
                "port": 0,
                "method": "",
                "password": "",
                "uot": True,
                "UoTVersion": 2,
                "level": 0
            }]
        }
    
    @property
    def outbound_settings_socks(self):
        return {
            "servers": [{
                "address": "",
                "port": 0,
                "users": []
            }]
        }
    
    @property
    def outbound_settings_trojan(self):
        return {
            "servers": [{
                "address": "127.0.0.1",
                "port": 1234,
                "password": "password",
                "email": "",
                "level": 0
            }]
        }
    
    @property
    def outbound_settings_vless(self):
        return {
            "vnext": [{
                "address": "example.com",
                "port": 443,
                "users": [{
                        "id": "",
                        "encryption": "none",
                        "flow": "",
                        "level": 0
                    }]
            }]
        }
    
    @property
    def outbound_settings_vmess(self):
        return {
            "vnext": [{
                "address": "127.0.0.1",
                "port": 37192,
                "users": [{
                    "id": "",
                    "security": "auto",
                    "level": 0
                }]
            }]
        }
    
    @property
    def outbound_streamSettings(self):
        return {
            "network": "tcp", # "tcp" | "kcp" | "ws" | "http" | "domainsocket" | "quic" | "grpc"
            "security": "none", # "none" | "tls" | "reality"
            "tlsSettings": {},
            "tcpSettings": {},
            "kcpSettings": {},
            "wsSettings": {},
            "httpSettings": {},
            "quicSettings": {},
            "dsSettings": {},
            "grpcSettings": {},
            "sockopt": {
                "mark": 0,
                "tcpFastOpen": False,
                "tproxy": "off",
                "domainStrategy": "AsIs",
                "dialerProxy": "",
                "acceptProxyProtocol": False,
                "tcpKeepAliveInterval": 0,
                "V6Only": False
            }
        }
    
    @property
    def outbound_streamSettings_network_domainsocket(self):
        return {
            "path": "/path/to/ds/file",
            "abstract": False,
            "padding": False
        }
    
    @property
    def outbound_streamSettings_network_grpc(self):
        return {
            "serviceName": "name",
            "multiMode": False,
            "user_agent": "custom user agent",
            "idle_timeout": 60,
            "health_check_timeout": 20,
            "permit_without_stream": False,
            "initial_windows_size": 0
        }
    
    @property
    def outbound_streamSettings_network_http(self):
        return {
            "host": ["xray.com"],
            "path": "/random/path",
            "read_idle_timeout": 10,
            "health_check_timeout": 15,
            "method": "PUT",
            "headers": {
                "Header": ["value"]
            }
        }
    
    @property
    def outbound_streamSettings_network_kcp(self):
        return {
            "mtu": 1350,
            "tti": 50,
            "uplinkCapacity": 12,
            "downlinkCapacity": 100,
            "congestion": False,
            "readBufferSize": 2,
            "writeBufferSize": 2,
            "header": {
                "type": "none"
            },
            "seed": "Password"
        }
    
    @property
    def outbound_streamSettings_network_quic(self):
        return {
            "security": "none",
            "key": "",
            "header": {
                "type": "none"
            }
        }
    
    @property
    def outbound_streamSettings_network_tcp(self):
        return {
            "acceptProxyProtocol": False,
            "header": {
                "type": "none"
            }
        }
    
    @property
    def outbound_streamSettings_network_tcp_http(self):
        return {
            "version": "1.1",
            "method": "GET",
            "path": ["/"],
            "headers": {
                "Host": ["www.baidu.com", "www.bing.com"],
                "User-Agent": [
                    "Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/53.0.2785.143 Safari/537.36",
                    "Mozilla/5.0 (iPhone; CPU iPhone OS 10_0_2 like Mac OS X) AppleWebKit/601.1 (KHTML, like Gecko) CriOS/53.0.2785.109 Mobile/14A456 Safari/601.1.46"
                ],
                "Accept-Encoding": ["gzip, deflate"],
                "Connection": ["keep-alive"],
                "Pragma": "no-cache"
            }
        }
    
    @property
    def outbound_streamSettings_network_ws(self):
        return {
            "acceptProxyProtocol": False,
            "path": "/",
            "headers": {
                "Host": "xray.com"
            }
        }
    
    @property
    def outbound_streamSettings_security_reality(self):
        return {
            "show": False,
            "dest": "example.com:443",
            "xver": 0,
            "serverNames": ["example.com", "www.example.com"],
            "privateKey": "",
            "minClientVer": "",
            "maxClientVer": "",
            "maxTimeDiff": 0,
            "shortIds": ["", "0123456789abcdef"],
            "fingerprint": "chrome",
            "serverName": "",
            "publicKey": "",
            "shortId": "",
            "spiderX": ""
        }
    
    @property
    def outbound_streamSettings_security_tls(self):
        return {
            "serverName": "xray.com",
            "rejectUnknownSni": False,
            "allowInsecure": False,
            "alpn": ["h2", "http/1.1"],
            "minVersion": "1.2",
            "maxVersion": "1.3",
            "cipherSuites": "",
            "certificates": [],
            "disableSystemRoot": False,
            "enableSessionResumption": False,
            "fingerprint": "safari",
            "pinnedPeerCertificateChainSha256": [""]
        }
    
    @property
    def outbound_streamSettings_sockopt(self):
        return {
            "mark": 0,
            "tcpMaxSeg": 1440,
            "tcpFastOpen": False,
            "tproxy": "off",
            "domainStrategy": "AsIs",
            "dialerProxy": "",
            "acceptProxyProtocol": False,
            "tcpKeepAliveInterval": 0,
            "tcpKeepAliveIdle": 300,
            "tcpUserTimeout": 10000,
            "tcpcongestion": "bbr",
            "interface": "wg0",
            "V6Only": False
        }
    
    @property
    def routing(self):
        return {
            "domainStrategy": "AsIs",
            "rules": [],
            "balancers": []
        }
    
    @property
    def routing_balancer(self):
        return {
            "tag": "balancer",
            "selector": []
        }
    
    @property
    def routing_rule(self):
        return {
            "type": "field",
            "inboundTag": [],
            "outboundTag": ""
        }