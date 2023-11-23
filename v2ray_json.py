import os

def client(log_path=os.getcwd(), log_level = 'warning', inbounds = [], outbounds = [], routing = {}):
    return {
        "log": {
            "access": os.path.join(log_path, "log.log"),
            "error": os.path.join(log_path, "error.log"),
            "loglevel": log_level
        },
        "inbounds": inbounds,
        "outbounds": outbounds,
        "routing": routing
    }

def make_inbound(tag, port, listen='0.0.0.0', protocal='socks'):
    if protocal == 'socks':
        settings = socks_in()
    return {
        "tag": tag,
        "listen": listen,
        "port": port,
        "protocol": protocal,
        "settings": settings
    }

def outbound():
    return {
        "tag": "",
        "protocol": "",
        "settings": {},
        "proxySettings": {}
    }

def routing_rules():
    return {
        "type": "field",
        "inboundTag": [],
        "outboundTag": ""
    }


def socks_in(auth = 'noauth', user = '', password = ''):
    return {
        "auth": auth, # noauth、password
        "accounts": [
            {
                "user": user,
                "pass": password
            }
        ],
        "udp": True
    }

def socks_out():
    return {
        "servers": [
            {
                "address": "",
                "port": 0,
                "users": [
                    {
                        "user": "",
                        "pass": ""
                    }
                ]
            }
        ]
    }

def shadowsocks_out():
    return {
        "servers": [
            {
                "address": "",
                "port": 0,
                "method": "",
                "password": ""
            }
        ]
    }