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