from ota_update.main.ota_updater import OTAUpdater

def download_and_install_update_if_available():
    o = OTAUpdater('https://github.com/jpbrito/terminal')
    o.download_and_install_update_if_available('terminalUTAD','ecocampus2019')

def start():
    #custom code
    # import da funcao a executar
    import main.principal

def boot():
    download_and_install_update_if_available()
    start()

boot()
