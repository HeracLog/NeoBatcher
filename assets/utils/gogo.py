import requests
from bs4 import BeautifulSoup as bs, Tag


class GogoanimeBatcher:
    def __init__(self, email:str, password:str, path:str, domain: str) -> None:
        self.email = email
        self.password = password
        self.path = path
        self.domain = domain
        self.session = requests.session()

    def search(self,query: str) -> dict[str:list]:
        link : str = f"https://{self.domain}/search.html?keyword={query.replace(' ','%20')}"

        # Gets the page's source
        htnlData = self.session.get(link).text
        # Parses the data
        soupedData = bs(htnlData, "lxml")
        # Gets the search results container
        numberOfPages = soupedData.find("ul",{"class":"pagination-list"})
        if numberOfPages == None : numberOfPages = 1
        else : numberOfPages = len(numberOfPages.find_all("li"))
        # Creates an empty dicitionary and an index variable
        shows : dict = {}

        for page in range(1,numberOfPages+1):
            pagelink = f"{link}&page={page}"
            htnlData  = self.session.get(pagelink).text
            soupedData = bs(htnlData,'lxml')
            container = soupedData.find("ul",{"class": "items"})
            i : int = 0
            # Loops through all results
            for show in container.find_all("li"):
                # Gets image
                img : str = show.find("img").get("src") 
                # Gets the p tag containing the name and link
                paragraph = show.find("p", {"class":"name"})
                # Gets the a tag within it
                aTag = paragraph.find("a")
                # Gets showname and link
                showName : str = aTag.getText()
                showLink : str = aTag.get("href")
                # Updates the dicitionary and increments i
                shows.update({showName:[showLink,img]})
                i+=1
        return shows        

    def searchWithFilter(self,query : str, filters : dict) -> str | dict:
        link : str = f"https://{self.domain}/filter.html?keyword={query.replace(' ','%20')}&"
        
        for filterName, value in filters.items():
            link+= f"{filterName}%5B%5D={value}&"
        link += 'sort=title_az&'

        # Gets the page's source
        htnlData = self.session.get(link).text
        # Parses the data
        soupedData = bs(htnlData, "lxml")
        # Gets the search results container
        numberOfPages = soupedData.find("ul",{"class":"pagination-list"})
        if numberOfPages == None : numberOfPages = 1
        else : numberOfPages = len(numberOfPages.find_all("li"))
        # Creates an empty dicitionary and an index variable
        shows : dict = {}
        for page in range(1,numberOfPages+1):
            pagelink = f"{link}&page={page}"
            htnlData  = self.session.get(pagelink).text
            soupedData = bs(htnlData,'lxml')
            container = soupedData.find("ul",{"class": "items"})
            i : int = 0
            # Loops through all results
            for show in container.find_all("li"):
                # Gets image
                img : str = show.find("img").get("src") 
                # Gets the p tag containing the name and link
                paragraph = show.find("p", {"class":"name"})
                # Gets the a tag within it
                aTag = paragraph.find("a")
                # Gets showname and link
                showName : str = aTag.getText()
                showLink : str = aTag.get("href")
                # Updates the dicitionary and increments i
                shows.update({showName:[showLink,img]})
                i+=1
        return shows 

    def formatHomePageLink(self,link : str) -> str:
        # We split the link at "-"
        linkPart = link.split("-")
        # We remove the last part
        linkPart = linkPart[:-1]
        # We join the link again
        finalLink = "-".join(linkPart)
        return finalLink
    
    def getAnimeLink(self,link : str) -> str:
        htmldata = self.session.get(link).text
        parsedData = bs(htmldata,'lxml')
        animeinfo = parsedData.find('div',{'class':'anime-info'})
        return animeinfo.find('a').get('href')
    
    def getHomePage(self) -> dict:
        link : str = f"https://{self.domain}/"
        # Gets the html data
        htmlData = self.session.get(link).text
        # Parses the data using lxml parser
        parsedData = bs(htmlData,"lxml")
        # Finds the div container with all the results
        divContainer : Tag = parsedData.find("div",{"class":"last_episodes loaddub"})
        # Finds the actual item container
        actualItems : Tag = divContainer.find("ul",{"class":"items"})
        # Gets all animes
        animes : list[Tag] = actualItems.find_all("li")
        # Creates an empty dict for the anime to be collected
        # The format is {AnimeName : [AnimeLink , LatestEpisode, ImageLink]}
        animeDict : dict[str,list[str]] = {}
        
        # Loops through the animes found 
        for anime in animes:
            # Gets the image link
            img : str = anime.find("img").get("src")
            # Finds the <p> tag with the name class
            nameCont : Tag = anime.find("p",{"class":"name"})
            # Finds the <a> tag with the link and name
            aTag : Tag = nameCont.find("a")
            # Gets the name from the title
            animeName = aTag.get("title")
            # Gets the link and formats it
            animeLink = self.formatHomePageLink(f"https://{self.domain}{aTag.get('href')}")
            # Gets the latest episode number
            episode = anime.find("p",{"class":"episode"}).getText()
            # Places the results in the anime dict
            animeDict.update({animeName:[animeLink,episode,img]})

        return animeDict
        
    def getNumberOfEpisodes(self,link : str) -> int:
        # Creates link to get data
        link = f"https://{self.domain}{link}"
        # Creates new session
        session : requests.Session = requests.session()
        # Gets the page's source
        htmlData = session.get(link).text
        # Parses the data
        soupedData = bs(htmlData, "lxml")
        # Gets the container containing the data
        container = soupedData.find("ul",{"id":"episode_page"})
        # Gets the a tag with the episodes info
        aTag = container.find("a",{"class":"active"})
        # Returns the number of episodes as int
        return int(aTag.get("ep_end"))

    # Function that removes extra parts from the link
    def removeExtraParts(self,link:str) -> str:
        # Loops through the link in reverse
        for i in range(len(link)-1,0,-1):
            # If the letter is a digit or "-"
            if link[i].isdigit() or link[i] == "-":
                link = link[0:i]
            # Otherwise we break
            else:
                break
        # Returns the link
        return link

    # Function to make link to be used in getting episodes links
    def makeLink(self,linkCate : str) -> str:
        # Makes the link
        link : str =f"https://{self.domain}{linkCate}"
        # Creates new session
        session = requests.session()
        text = session.get(link).text

        # Parses the html data
        parsedData = bs(text,"lxml")

        # Gets movie ID
        movieID = parsedData.find("input",{"class":"movie_id"}).get("value")
        # Gets the container with the episodes ranges
        episodeRanges = parsedData.find("ul",{"id":"episode_page"})

        # Gets the start and end episode number
        epStart = episodeRanges.find("li").find("a").get("ep_start")
        epEnd = episodeRanges.find("li").find("a").get("ep_end")
        # Creates a link for getting the episode data
        epLink = f"https://ajax.gogo-load.com/ajax/load-list-episode?ep_start={epStart}&ep_end={epEnd}&id={movieID}&default_ep=0&alias={link.split('/')[-1]}"

        # Gets the episode page
        epData = session.get(epLink).text

        # Parses the episode page
        link = bs(epData,"lxml").find("a").get("href")
        # Formats the link
        if link[0] == " ":
            link = link[1:-1]
        link = f"https://{self.domain}{link}"
        linkParts = link.split("-")
        linkParts = linkParts[:-1]
        link = "-".join(linkParts)
        # Returns the link
        return link

    def login(self):
        linkLogin = f"https://{self.domain}/login.html"
        # Gets the html data
        text = self.session.get(linkLogin).text
        # Sorts the data to be usable
        so = bs(text, "lxml")
        # Looks for CSRF token
        for i in so.find_all("meta"):
            if i.get("name") == "csrf-token":
                csrftoken = i.get("content")
        # Dictionary for storing user data add your email and password 
        login_data = dict(email=self.email, password=self.password, _csrf=csrftoken, next='/')
        # Logs in using the data
        self.session.post(linkLogin,data=login_data, headers=dict(Referer=linkLogin))

    # Function to determine next quality in line for downloading tries
    def getNewQuality(self,tried : list) -> str:
        # Returns the quality next in line
        for quality in ["480","360","1080","720"]:
            if quality not in tried:
                return quality
        # Returns None if all qualities were tried
        return None
    # This function fetches each download link indiviually
    def getDownloadLinks(self,eps,LinkofPath,quality):
        # Array of links to be downloaded
        Links = []
        self.login()
        mainQuality = quality
        for ep in eps:
            tried : list = []
            # Episode link can be changed
            link = f"{format(LinkofPath)}-{ep}"
            
            # Gets html data of the episode page
            html_page= self.session.get(link).text
            # Sorts html data
            soup = bs(html_page, "lxml")
            sizeBefore : int = len(Links)
            tried.append(quality)
            # Finds download links
            for i in range(0,3):
                for link in soup.find_all("a"):
                    # You can set the resloution from '360, 480, 720, 1080'
                    if quality in format(link.text):
                        x = link.get("href")
                        Links.append(x) 
                if sizeBefore == len(Links):
                    print(f"Couldn't get episode {ep} at quality {quality}")
                    quality = self.getNewQuality(tried)
                else:
                    break
        # Returns Links array to other functions
        return Links

    def getAnimeData(self,link: str) -> list:
        link = f"https://{self.domain}{link}"
        htmlData = self.session.get(link).text
        parsedData = bs(htmlData,'lxml')
        container = parsedData.find('div',{"class":"anime_info_body_bg"})
        data = []
        data.append(container.find('img').get("src"))
        pTags = container.find_all("p",{"class":"type"})
        showType = pTags[0].find("a").getText()
        plotSummary = pTags[1].getText()
        if len(plotSummary) >= 279:
            plotSummary = plotSummary[:278]
            plotSummary += "......."
        genres = pTags[2].find_all("a")
        genresText = ''.join([genre.getText() for genre in genres])
        year = pTags[3].getText()
        status = pTags[4].find("a").getText()

        data.append(showType)
        data.append(plotSummary)
        data.append(genresText)
        data.append(year)
        data.append(status)
        return data
    
    