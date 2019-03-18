from ota_update.main.ota_updater import OTAUpdater


def download_and_install_update_if_available():
    o = OTAUpdater('url-to-github')
    o.download_and_install_update_if_available('wifi-ssid','wifi-password')

def start():
    #custom code
    # import da funcao a executar

def boot():
    download_and_install_update_if_available()
    start()
    
    
boot()
