from main.ota_updater import OTAUpdater

def download_and_install_update_if_available():
    o = OTAUpdater('https://github.com/jpbrito/terminal')
    o.using_network('terminalUTAD','ecocampus2019','192.168.1.28')
    o.download_and_install_update_if_available('terminalUTAD','ecocampus2019', '192.168.1.28')
    o.check_for_update_to_install_during_next_reboot()
def start():
    #custom code
    # import da funcao a executar
    import main.principal
    #check_for_update_to_install_during_next_reboot()
    print("ok")

def boot():
    download_and_install_update_if_available()
    start()

boot()
