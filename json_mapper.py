from bidict import bidict

class JsonMapper(object):
    @property
    def trojanMapper(self):
        return bidict({
            'security': 'security',
            'sni': 'security:serverName',
            'alpn': 'security:alpn',
            'fp': 'network:fingerprint',
            'pbk': 'security:publicKey',
            'sid': 'security:shorId',
            'type': 'network',
            'path': 'security:path',
            'headerType': 'network:http',
            'host': 'network:host'
        })
    
    @property
    def vlessMapper(self):
        return bidict({
            'security': 'security',
            'sni': 'security:serverName',
            'alpn': 'security:alpn',
            'fp': 'network:fingerprint',
            'pbk': 'security:publicKey',
            'sid': 'security:shorId',
            'type': 'network',
            'serviceName': '/path',
            'flow': 'flow',
            'encryption': 'encryption'
        })
    
    @property
    def vmessMapper(self):
        return bidict({
            'add': 'address',
            'aid': 'aid',
            'host': 'network:host',
            'id': 'uuid',
            'net': 'network',
            'path': 'network:path',
            'port': 'port',
            'ps': 'remarks',
            'scy': 'security',
            'sni': 'security:serverName',
            'tls': 'security:security',
            'type': 'network:type',
            'alpn': 'security:alpn',
            'v': 'v'
        })