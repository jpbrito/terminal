import usocket
import os
import gc
import machine
import time

#Este script conecta ao servidor OTA Proprietario e encarrega-se de efetuar download de todas as informacoes
class OTAUpdater:

    def __init__(self,gateway, module='', main_dir='main'):
        self.http_client = HttpClient()
        self.github_repo = 'http://' + gateway + '/otaserver/upload'
        self.main_dir = main_dir
        self.module = module.rstrip('/')
        self.gateway = gateway


    #conecta a rede e configura dhcp
    @staticmethod
    def using_network(ssid, password, ipaddress):
        import network
        sta_if = network.WLAN(network.STA_IF)
        if not sta_if.isconnected():
            print('connecting to network...')
            sta_if.active(True)
            sta_if.ifconfig((ipaddress,'255.255.255.0','192.168.1.1','1.1.1.1'))
            sta_if.connect(ssid, password)
            while not sta_if.isconnected():
                pass
        print('IP Address: ', sta_if.ifconfig()[0])


    #procura por updates , se ecistir
    def check_updates(self, ssid, password, ipaddress):
        # se a versao atual for menor que a versao do servidor
        # chama a fucao install update
        # caso contrario nao ha updates
        self.using_network(ssid,password,ipaddress)
        self.apply_pending_updates_if_available()
        current_version = self.get_version()
        ota_version = self.get_latest_version()
        if int(current_version) != int(ota_version):
            print("Current Software Version: " + str(current_version))
            print('**New Update available**:  ' +  str(ota_version))
            self._download_and_install_update(ssid, password, ipaddress)
        else:
            print('Current Software Version: ' + str(current_version))


    #vai ao servidor OTA e procura por updates existentes
    def _download_and_install_update(self,ssid, password, ipaddress):
        OTAUpdater.using_network(ssid, password, ipaddress) #confirma ligacao a rede
        print("**Installing Update, please wait...**")
        self.download_all_files() #efetua download de todos os ficheiros
        self.rmtree(self.modulepath(self.main_dir)) #remove a pasta main
        #os.rename(self.modulepath('next/.version_on_reboot'), self.modulepath('next/.version')) #modifica o nome da versao que efetuou download
        os.rename(self.modulepath('next'), self.modulepath(self.main_dir)) #modifica nome da pasta next para main
        machine.reset()


    #aplica updates se existir a pasta next e o ficheiro .version nessa pasta
    def apply_pending_updates_if_available(self):
        if 'next' in os.listdir(self.module):
                self.rmtree(self.modulepath(self.main_dir))
                os.rename(self.modulepath('next'), self.modulepath(self.main_dir))
                print('Aplied pending update,  rock and roll baby!!')
        else:
            print('No pending updates available!')

    #removes all directory in path
    def rmtree(self, directory):
        for entry in os.ilistdir(directory):
            is_dir = entry[1] == 0x4000
            if is_dir:
                self.rmtree(directory + '/' + entry[0])
            else:
                os.remove(directory + '/' + entry[0])
        os.rmdir(directory)
    # returns current version from esp32 file
    def get_version(self):
         if "ota_version.txt" in os.listdir(self.module + "main"):
             f = open(self.modulepath(self.module + 'main/ota_version.txt')) #vai buscar versao atual do ficheiro ota, testar esta merda...
             version = f.read()
             f.close()
             return version
         return '0'
    # returns last version from ota server
    def get_latest_version(self):
        latest_release = self.http_client.get(self.github_repo + '/ota_version.txt')
        last_ver = int(latest_release.text)
        latest_release.close()
        return last_ver

    # downloads all files from url
    # moves all files to path designated
    def download_all_files(self):
        file_list = self.http_client.get(self.github_repo + "/files.json")
        file_content = file_list.json()
        os.mkdir(self.modulepath('next')) #cria a pasta next que vai conter temporariamente os ficheiros download
        for file in file_content:
            download_url = self.github_repo + "/" + file[1]
            download_path = self.modulepath('next/' + file[1])
            self.download_file(download_url,download_path)
        file_list.close()

    def download_file(self, url, path):
        print('\tDownloading: ', path)
        with open(path, 'w') as outfile:
            try:
                response = self.http_client.get(url)
                outfile.write(response.text)
            finally:
                response.close()
                outfile.close()
                gc.collect()

    def modulepath(self, path):
        return self.module + '/' + path if self.module else path


class Response:

    def __init__(self, f):
        self.raw = f
        self.encoding = 'utf-8'
        self._cached = None

    def close(self):
        if self.raw:
            self.raw.close()
            self.raw = None
        self._cached = None

    @property
    def content(self):
        if self._cached is None:
            try:
                self._cached = self.raw.read()
            finally:
                self.raw.close()
                self.raw = None
        return self._cached

    @property
    def text(self):
        return str(self.content, self.encoding)

    def json(self):
        import ujson
        return ujson.loads(self.content)


class HttpClient:

    def request(self, method, url, data=None, json=None, headers={}, stream=None):
        try:
            proto, dummy, host, path = url.split('/', 3)
        except ValueError:
            proto, dummy, host = url.split('/', 2)
            path = ''
        if proto == 'http:':
            port = 80
        elif proto == 'https:':
            import ussl
            port = 443
        else:
            raise ValueError('Unsupported protocol: ' + proto)

        if ':' in host:
            host, port = host.split(':', 1)
            port = int(port)

        ai = usocket.getaddrinfo(host, port, 0, usocket.SOCK_STREAM)
        #print(ai)
        ai = ai[0]

        s = usocket.socket(ai[0], ai[1], ai[2])
        try:
            s.connect(ai[-1])
            if proto == 'https:':
                s = ussl.wrap_socket(s, server_hostname=host)
            s.write(b'%s /%s HTTP/1.0\r\n' % (method, path))
            if not 'Host' in headers:
                s.write(b'Host: %s\r\n' % host)
            # Iterate over keys to avoid tuple alloc
            for k in headers:
                s.write(k)
                s.write(b': ')
                s.write(headers[k])
                s.write(b'\r\n')
            # add user agent
            s.write('User-Agent')
            s.write(b': ')
            s.write('MicroPython OTAUpdater')
            s.write(b'\r\n')
            if json is not None:
                assert data is None
                import ujson
                data = ujson.dumps(json)
                s.write(b'Content-Type: application/json\r\n')
            if data:
                s.write(b'Content-Length: %d\r\n' % len(data))
            s.write(b'\r\n')
            if data:
                s.write(data)

            l = s.readline()
            #print(l)
            l = l.split(None, 2)
            status = int(l[1])
            reason = ''
            if len(l) > 2:
                reason = l[2].rstrip()
            while True:
                l = s.readline()
                if not l or l == b'\r\n':
                    break
                #print(l)
                if l.startswith(b'Transfer-Encoding:'):
                    if b'chunked' in l:
                        raise ValueError('Unsupported ' + l)
                elif l.startswith(b'Location:') and not 200 <= status <= 299:
                    raise NotImplementedError('Redirects not yet supported')
        except OSError:
            s.close()
            raise

        resp = Response(s)
        resp.status_code = status
        resp.reason = reason
        return resp

    def head(self, url, **kw):
        return self.request('HEAD', url, **kw)

    def get(self, url, **kw):
        return self.request('GET', url, **kw)

    def post(self, url, **kw):
        return self.request('POST', url, **kw)

    def put(self, url, **kw):
        return self.request('PUT', url, **kw)

    def patch(self, url, **kw):
        return self.request('PATCH', url, **kw)

    def delete(self, url, **kw):
        return self.request('DELETE', url, **kw)


o = OTAUpdater('192.168.1.1')
o.check_updates('terminalUTAD','ecocampus2019','192.168.1.28')
