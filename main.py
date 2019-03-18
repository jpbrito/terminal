from main.ota_updater import OTAUpdater
#from main.terminal import Terminal

node_name = "node8"
node_ip = "192.168.1.28"
node_gateway = "192.168.1.1"
node_ssidname = "terminalUTAD"
node_ssidpassword = "ecocampus2019"
gitaddress = "https://github.com/jpbrito/terminal"



def download_and_install_update_if_available():
    o = OTAUpdater(gitaddress)
    o.using_network(node_ssidname,node_ssidpassword,node_ip)
    o.download_and_install_update_if_available(node_ssidname,node_ssidpassword,node_ip)
def start():
    # aqui executa o codigo principal e so chamar a funcao main.principal
    # import da funcao a executar
    from main.terminal import Terminal
    t = Terminal(node_name,node_ip,node_gateway,node_ssidname,node_ssidpassword)
    t.read()

def boot():
    download_and_install_update_if_available()
    start()

boot()