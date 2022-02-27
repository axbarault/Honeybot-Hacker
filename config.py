import os
import json

CFGFILE = "config.json"


class Config():
    def __init__(self):
        self.readConfig()

    def readConfig(self):
        if os.path.isfile(CFGFILE):
            f = open(CFGFILE, 'r')
            self.conf = json.load(f)
            f.close()

            self.token = self.conf['discord-token']
            self.rulesMessageId = self.conf['rules-message-id']
            self.rulesChannelId = self.conf['rules-channel-id']
        else:
            print("Fichier config non trouvé ou non valide:", CFGFILE)
            exit()

    def getPrefix(self):
        return self.conf['prefix']

    def setPrefix(self, prefix):
        self.conf['prefix'] = prefix
        f = open(CFGFILE, 'w')
        json.dump(self.conf, f)
        f.close()


config = Config()
