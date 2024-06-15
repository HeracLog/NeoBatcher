import json
import os


class RecentsManager:
    def __init__(self) -> None:
        self.preset : dict = {
            'Manga':{},
            'Anime':{},
            'Home':{}
        } 
        self.keys = ['Manga','Anime',"Home"]
        self.path = './recents.json'

        if not os.path.exists(self.path):
            with open(self.path,'w') as f:
                f.write(str(json.dumps(self.preset,indent=4)))
    def loadFile(self)->dict:
        with open(self.path, 'r') as f: self.data = json.load(f)
        self.data['Manga'] = self.data['Manga']
        self.data['Anime'] = self.data['Anime']
        self.data['Home'] = self.data['Home']
        return self.data
    
    def checkForEntires(self):
        with open(self.path, 'r') as f: 
            data = json.load(f)
        keys = list(data.keys())
        for key in self.keys:
            if key not in keys:
                data.update({key:self.preset[key]})
        with open(self.path, 'w') as f: f.write(str(json.dumps(data,indent=4)))
    def revDict(self,data:dict):
        return {k:v for k,v in zip(reversed(list(data.keys())),reversed(list(data.values())))}
    def addManga(self,entry:tuple):
        self.data['Manga'] = self.data['Manga']
        self.data['Manga'].update(entry)

    def addAnime(self,entry):
        self.data['Anime'] = self.data['Anime']
        self.data['Anime'].update(entry)
    def addHome(self,entry):
        self.data['Home'] = self.data['Home']
        self.data['Home'].update(entry)
    def save(self):
        with open(self.path,'w') as f:
            f.write(str(json.dumps(self.data,indent=4)))