import os
import json

CFGFILE = "config.json"

class Config():
    @classmethod
    def readConfig(self):
        if os.path.isfile(CFGFILE):
            f = open(CFGFILE, 'r')
            self.conf = json.load(f)
            f.close()

            self.token = self.conf['discord-token']
        else:
            print("ERR: Config file is missing (%s)" % CFGFILE)
            exit()

    @classmethod
    def getPrefix(self):
        return self.conf['prefix']

    @classmethod
    def setPrefix(self, prefix):
        self.conf['prefix'] = prefix
        f = open(CFGFILE, 'w')
        json.dump(self.conf, f)
        f.close()

config = Config()
config.readConfig()
