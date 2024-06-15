import json
import os

class PrefUtil:
    def __init__(self) -> None:
        self.path = './preferences.json'
        self.stockDict = {
            "Email": "",
            "Password": "",
            "Mode": "Dark",
            "Color": "random",
            "Directory": "./",
            "Manga_Directory": "./",
            "Domain": "gogoanime3.net",
            "Player": ""
        }
        self.keys = list(self.stockDict.keys())
        self.checkForEntires()
        if not os.path.exists(self.path):
            with open(self.path, 'w') as f: f.write(str(json.dumps(self.stockDict,indent=4)))
    def loadFile(self):
        with open(self.path, 'r') as f: self.data = json.load(f)
        return self.data
    def checkForEntires(self):
        with open(self.path, 'r') as f: 
            data = json.load(f)
        keys = list(data.keys())
        for key in self.keys:
            if key not in keys:
                data.update({key:self.stockDict[key]})
        with open(self.path, 'w') as f: f.write(str(json.dumps(data,indent=4)))


        