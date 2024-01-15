import random
import string
import time
import requests
from PIL import Image
from pypdf import PdfMerger
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from io import BytesIO
from bs4 import BeautifulSoup as bs, Tag
import os
import flet as ft
from tqdm import tqdm
import json 


# Function that loads the data from the preferences file
def loadData() -> dict:
    # Opens the data file
    jsonData = open("./preferences.json","r")
    # Parses the data from json to dict
    dataDict = json.load(jsonData)
    # Returns the dict
    return dataDict
# Global variables that will be used throughout the execution process
link : str= ""
linkRaw : str= ""
name : str = ""
results : dict = {}
episodesNumber : int = 0
resultsList : list = []
# Results page intialization 
resultsPage = ft.Column(
    controls= resultsList
)
# Loads the data
data = loadData()
direc = data["Directory"]
mangaDirec = data["Manga_Directory"]
cvlcPath = data['Player']
try:
    os.mkdir(direc)
except: pass
try:
    os.mkdir(mangaDirec)
except : pass
# Finds theme for the app
defaultMode = data["Mode"]
# Loads the domain from the file
domain : str = data["Domain"]

selectedEpisode = ''
query = ""
language = ""
# Function that searches for managa
def searchForManga(query : str) -> dict:
    link = f'https://api.mangadex.org/manga?title={query}&limit=25&contentRating[]=safe&includes[]=cover_art&order[relevance]=desc'
    session = requests.session()
    data = session.get(link).content.decode("utf-8")
    data = json.loads(data)
    # parsedData = bs(data,'lxml')
    results : dict = {}
    for result in data['data']:
        mangaID = result['id']
        mangaName = result['attributes']['title']['en']
        for i in result['relationships']:
            if i["type"] == 'cover_art':
                coverart = i['attributes']['fileName']
        photolink = f'https://mangadex.org/covers/{mangaID}/{coverart}'
        mangalink = f'https://mangadex.org/title/{mangaID}/{mangaName.replace(" ","-")}'
        results.update({mangaName:[mangaID,photolink,mangalink]})
    return results

def getAbout(mangaID : str) :
    link = f"https://api.mangadex.org/manga/{mangaID}?includes[]=artist&includes[]=author&includes[]=cover_art"
    session : requests.Session = requests.session()
    data = session.get(link).content.decode('utf-8')
    data = json.loads(data)
    attributes = data['data']['attributes']
    description = attributes['description']
    return description['en']

def getChapters(managaID : str) -> dict:
    startAmmount = 200
    link : str = f"https://api.mangadex.org/manga/{managaID}/feed?limit=200&includes[]=scanlation_group&includes[]=user&order[volume]=asc&order[chapter]=asc&offset=0&contentRating[]=safe&contentRating[]=suggestive&contentRating[]=erotica&contentRating[]=pornographic"
    session : requests.Session = requests.session()
    data = session.get(link).content.decode('utf-8')
    data = json.loads(data)
    allData = list()
    allData.extend(data['data'])
    total = data["total"]
    chapterData : dict = {}
    if total > startAmmount:
        while total > startAmmount:
            newLink = f"https://api.mangadex.org/manga/{managaID}/feed?limit={200}&includes[]=scanlation_group&includes[]=user&order[volume]=asc&order[chapter]=asc&offset={startAmmount}&contentRating[]=safe&contentRating[]=suggestive&contentRating[]=erotica&contentRating[]=pornographic"
            newData = session.get(newLink).content.decode('utf-8')
            newData = json.loads(newData)
            allData.extend(newData['data'])
            startAmmount += 200
    for entry in allData:
        entryID = entry["id"]
        attributes = entry["attributes"]
        language = attributes["translatedLanguage"]
        title = attributes["title"]
        chapterNum = attributes["chapter"]
        if title == None or len(title) == 0:
            title = chapterNum
        else:
            title = f'{chapterNum}-{title}'
        pageNum = attributes["pages"]

        if language not in chapterData:
            chapterData.update({language:{}})
        chapterData[language].update({title:[chapterNum,entryID,pageNum]})
    return chapterData

def getPageNumber(pageHash : str) -> int:
    return "".join(i for i in pageHash.split("-")[0] if i.isnumeric())


def getPages(chapterID : str,mangaName : str, chapterNumber : str,page:ft.Page): 
    link = f"https://api.mangadex.org/at-home/server/{chapterID}?forcePort443=false"
    session : requests.Session = requests.session()
    data = session.get(link).content.decode('utf-8')
    data = json.loads(data)
    chapterData = data["chapter"]
    chapterHash = chapterData["hash"]
    imgs = chapterData["data"]
    baseUrl = "https://uploads.mangadex.org/data"
    try:
        os.mkdir(f"{mangaDirec}{name}/{name}-{chapterNumber}")
    except:
        print("Directory exists")
    progress_bar = ft.ProgressBar(
        width=600,
        color= generate_hex_color_code()
    )
    labelText = ft.Text(f"Saving chapter {chapterNumber}:     0/{len(imgs)}")
    page.controls.append(labelText)
    page.controls.append(progress_bar)
    page.update()

    for img in imgs:
        i = imgs.index(img)
        imgurl = f"{baseUrl}/{chapterHash}/{img}"
        pageNumber = getPageNumber(img)
        response = session.get(imgurl)

        if response.status_code == 200:
            image_content = BytesIO(response.content)
            image = Image.open(image_content)
            image = image.convert('RGB')
            image.save(f"{mangaDirec}{mangaName}/{mangaName}-{chapterNumber}/{pageNumber}.jpg")
            progress_bar.value = (i+1)/len(imgs)
            labelText.value = f"Saving chapter {chapterNumber}:     {i+1}/{len(imgs)}"
            labelText.update()
            progress_bar.update()
            page.update()
        else:
            print(f"Couldn't get page {pageNumber}")


# Function that makes pdfs of the manga chapter 
def pdfize(_dir,name,chapter,page:ft.Page):
        # Alert of pdfing the chapter initialization
        print(f"Started pdfiziing chapter {chapter}")
        # Selects all image files in a directory acoording to certain parameters
        image_files = [f for f in os.listdir(_dir) if f.endswith('.jpg') or f.endswith('.jpeg') or f.endswith('.png')]

        # Creates a pdf canvas of letter size and name of the manga and its chapter
        pdf = canvas.Canvas(f'{_dir}/{name}-{chapter}.pdf', pagesize=letter)
        progress_bar = ft.ProgressBar(
            width=600,
            color= generate_hex_color_code()
            )
        labelText = ft.Text(f"Pdfizing chapter {chapter}:     0/{len(image_files)}")
        page.controls.append(labelText)
        page.controls.append(progress_bar)
        page.update()

        # Loops through all image files and creates a loading bar for it
        for i in range(0,len(image_files)):
            # Defines images path in numerical order
            image_path =f"{_dir}/{i+1}.jpg"
            # Opens the image file to be written in the pdf
            img = Image.open(image_path)
            # Calculate the scaling factor to fit the image within the PDF page
            # img.size is a tuple of (width,height)
            width, height = img.size
            # Gets the max size of the page
            max_width, max_height = letter
            # Scaling factor is the max dim / img dim,
            # We select the smallest so the other dimension gets displayed properly
            scaling_factor = min(max_width/width, max_height/height)

            # Scale the image size
            new_width = int(width * scaling_factor)
            new_height = int(height * scaling_factor)

            # Draw the image on the PDF canvas
            pdf.drawImage(image_path, 0, 0, width=new_width, height=new_height, preserveAspectRatio=True)
            progress_bar.value = (i+1)/len(image_files)
            labelText.value = f"Pdfizing chapter {chapter}:     {i+1}/{len(image_files)}"
            labelText.update()
            progress_bar.update()
            page.update()
            # Check if its the last page
            # If its not we create a new page
            if i < len(image_files) - 1:
                pdf.showPage()
        # Saves the pdf file
        pdf.save()
        # Alerts the pdf is done
        print(f"Done pdfizing chapter {chapter}")

# Function to merge all pdf files of a manga into one pdf file
def mergePDFS(direc,name,page : ft.Page):
    # Finds all chapter direcetories 
    directiories = [d for d in os.listdir(direc) if os.path.isdir(os.path.join(direc,d))]
    # Makes an empty list where the pdf files will be
    pdfFiles = []
    # Loops through directories and finds all pdf files
    for dirr in directiories:
        for f in os.listdir(os.path.join(direc,dirr)):
            if f.endswith(".pdf"):
                pdfFiles.append(os.path.join(direc,os.path.join(dirr,f)))

    # Function that finds the numeric part of the pdf name
    def get_numeric_part(filename):
        return float(filename.split("-")[-1].replace(".pdf",""))

    # Sorts the pdf files according to the chapter number
    pdfFiles.sort(key=get_numeric_part)
    # Makes a pdf merger object
    merger = PdfMerger()
    progressBar = ft.ProgressBar(
        width= 600,
        color= generate_hex_color_code()
    )
    labelText = ft.Text(value=f"Merging all PDFs....     0/{len(pdfFiles)}")
    page.controls.append(labelText)
    page.controls.append(progressBar)
    page.update()
    # Loops through all files append them while displaying the progress in a progress bar
    for i in range(len(pdfFiles)):
        file = pdfFiles[i]
        merger.append(file)
        labelText.value = f"Merging all PDFs....     {i+1}/{len(pdfFiles)}"
        progressBar.value = (i+1)/len(pdfFiles)
        labelText.update()
        progressBar.update()
        page.update()
    # Creates the file and closes the megrger object
    merger.write(f"{direc}{name}.pdf")
    merger.close()


resultsPage = ""
name = ""
dictChap = {}
results = []
optionsRes = []
startChapterDropdown = ft.Dropdown(
        options = optionsRes,
        label="Start chapter",
        disabled=True
    )
endChapterDropdown = ft.Dropdown(
        options = optionsRes,
        label="End chapter",
        disabled=True
    )
downloadPage = ft.Column(

)
newColorCode : str = ""
randomColorCode : str = ""
# Function to change domain name
# Search function
def search(search : str) -> str | dict:
    link : str = f"https://{domain}/search.html?keyword={search.replace(' ','%20')}"

    # Creates a new session
    session : requests.Session = requests.session()
    # Gets the page's source
    htnlData = session.get(link).text
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
        htnlData  = session.get(pagelink).text
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

# Search function
def searchWithFilter(search : str, filters : dict) -> str | dict:
    link : str = f"https://{domain}/filter.html?keyword={search.replace(' ','%20')}&"
    for filterName, value in filters.items():
        link+= f"{filterName}%5B%5D={value}&"
    link += 'sort=title_az&'
    # Creates a new session
    session : requests.Session = requests.session()
    # Gets the page's source
    htnlData = session.get(link).text
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
        htnlData  = session.get(pagelink).text
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

# Function to format links from homepage
def formatHomePageLink(link : str) -> str:
    # We split the link at "-"
    linkPart = link.split("-")
    # We remove the last part
    linkPart = linkPart[:-1]
    # We join the link again
    finalLink = "-".join(linkPart)
    return finalLink
def getAnimeLink(link : str) -> str:
    session = requests.session()
    htmldata = session.get(link).text
    parsedData = bs(htmldata,'lxml')
    animeinfo = parsedData.find('div',{'class':'anime-info'})
    return animeinfo.find('a').get('href')
# Function that fetches homepage
def getHomePage() -> dict:
    # Link is simply just the domain
    link : str = f"https://{domain}/"
    # Creates a new session
    session : requests.Session = requests.session()
    # Gets the html data
    htmlData = session.get(link).text
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
        animeLink = formatHomePageLink(f"https://{domain}{aTag.get('href')}")
        # Gets the latest episode number
        episode = anime.find("p",{"class":"episode"}).getText()
        # Places the results in the anime dict
        animeDict.update({animeName:[animeLink,episode,img]})

    return animeDict

# Function to get the number of episodes
def getNumberOfEpisodes(link : str) -> int:
    # Creates link to get data
    link = f"https://{domain}{link}"
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
def removeExtraParts(link:str) -> str:
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
def makeLink(linkCate : str) -> str:
    # Makes the link
    link : str =f"https://{domain}{linkCate}"
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
    link = f"https://{domain}{link}"
    linkParts = link.split("-")
    linkParts = linkParts[:-1]
    link = "-".join(linkParts)
    # Returns the link
    return link

# This function logs in and fetches each download link indiviually
def LoginAndGoToLink(eps,LinkofPath,quality,email,password):
    # Array of links to be downloaded
    Links = []
    # Login page link
    
    linkLogin = f"https://{domain}/login.html"

    # Requests session to start handshake
    s = requests.session()
    # Gets the html data
    text = s.get(linkLogin).text
    # Sorts the data to be usable
    so = bs(text, "lxml")
    # Looks for CSRF token
    for i in so.find_all("meta"):
        if i.get("name") == "csrf-token":
            csrftoken = i.get("content")

    # Dictionary for storing user data add your email and password 
    login_data = dict(email=email, password=password, _csrf=csrftoken, next='/')

    # Logs in using the data
    s.post(linkLogin,data=login_data, headers=dict(Referer=linkLogin))
    # Loops for all episodes
    mainQuality = quality
    for ep in eps:
        tried : list = []
        # Episode link can be changed
        link = f"{format(LinkofPath)}-{ep}"
        
        # Gets html data of the episode page
        html_page= s.get(link).text
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
                quality = getNewQuality(tried)
            else:
                break
    # Returns Links array to other functions
    return Links

# Function to generate random color codes
def generate_hex_color_code():
    # Generate a random 6-digit hex number
    hex_num = ''.join(random.choices(string.hexdigits, k=6))
    # Prepend '#' to the hex number to get a valid color code
    color_code = '#' + hex_num
    return color_code

# Function to determine next quality in line for downloading tries
def getNewQuality(tried : list) -> str:
    # Returns the quality next in line
    for quality in ["480","360","1080","720"]:
        if quality not in tried:
            return quality
    # Returns None if all qualities were tried
    return None

# Main function where all the magic happens
# This is mostly flet stuff and GUI
def main(page : ft.Page):
    # Inializes email and password fields 
    emailField = ft.TextField(
        label="Email"
    )
    passwordField = ft.TextField(
        label="Password",
        password = True,
        can_reveal_password= True
    )
    # Login action function
    def login(e):
        # If the fields aren't empty
        if emailField.value and passwordField.value:
            # Chanegs email in the data dict
            data["Email"] = emailField.value
            # Chanegs password in the data dict
            data["Password"] = passwordField.value
            # Saves the data into the json file
            with open("./preferences.json",'w') as f:
                json.dump(data,f,indent=4)
            # Removes everything from the main page
            page.clean()
            # Adds the main page
            page.add(mainPage)
    
    # Login screen column
    loginScreen = ft.Column(
        # Controls of the column
        controls=[
            # Container with the app name
            ft.Container(
                content=ft.Text(
                value="NeoBatcher",
                # Bold font weight
                weight= ft.FontWeight.BOLD,
                # Size of 32
                size= 32,
                ),
                # Centre allignment
                alignment=ft.alignment.center
            )
            ,
            # Adds fields we created before
            emailField,passwordField,
            # Login button that runs the "login" function
            ft.ElevatedButton(text="Login",on_click=login)
        ]
    )

    colorCode = ""
    # If the color theme prefernces is random
    if data["Color"] == "random":
        # We generate a random color code for the theme
        randomColorCode = generate_hex_color_code()
        colorCode = randomColorCode
    else:
        # Otherwise we use the one provided
        colorCode = data["Color"]
    # Sets the app theme as the one prefered  
    page.theme_mode = defaultMode
    # Sets up the thene with the color code from above
    page.theme = ft.Theme(
        color_scheme=ft.ColorScheme(
            primary= colorCode
        ))
    # Setting up screen size
    page.window_width = 600
    page.window_height = 500
    page.window_resizeable = False
    page.window_maximizable = False
    page.update()
    # Sets scroll mode to auto
    # Meaning if there is something on page that is beyond bounds it enables the scrolling feature
    page.scroll = ft.ScrollMode.AUTO
    # Sets page title
    page.title = "NeoBatcher"
    # Setting up allignment
    page.vertical_alignment=ft.MainAxisAlignment.CENTER,
    page.horizontal_alignment=ft.CrossAxisAlignment.CENTER
    
    # Intializes fields to be used in download menu
    # Defines the episode we start from
    epFromField = ft.TextField(
        label = "Start from episode",
        width = 187,
        keyboard_type= ft.KeyboardType.NUMBER
    )
    # Defines the episode we stop at
    epNumField = ft.TextField(
        label = "Till episode",
        width = 187,
        keyboard_type= ft.KeyboardType.NUMBER
    )
    # Dropdown menu for download qualities
    quaityDropDown = ft.Dropdown(
        width=187,
        options=[
            ft.dropdown.Option("360"),
            ft.dropdown.Option("480"),
            ft.dropdown.Option("720"),
            ft.dropdown.Option("1080")
        ],
        hint_text="Quality"
    )
    # Function to change main domain
    def changeDomain(newDomain : str) -> None:
        # Changes domain in the data dict
        data["Domain"] = newDomain
        # Saves the changes to the json file
        with open("./preferences.json","w") as f:
            json.dump(data,f,indent=4)
    
    # Function to load the search page
    def loadSearchPage(e):
        # Removes everything from the page
        page.clean()
        # Adds the search page
        page.add(searchPage)

    # Function to load the main page
    def loadMainPage(e):
        # Removes everything from the page
        page.clean()
        # Adds the main page
        page.add(mainPage)

    # Function to place results
    def tempSearch(e):
        options = {}
        # If the search field isn't empty
        if searchField.value:

            if genreDropDown.value != 'None':
                options.update({"genre":genreDropDown.value.lower().replace(' ','-')})
            if languageDropDown.value != 'None':
                options.update({"language":languageDropDown.value.lower().replace(' ','-')})
            if yearDropdown.value != 'None':
                options.update({"year":yearDropdown.value.lower().replace(' ','-')})
            if seasonDropDown.value != 'None':
                options.update({"season":seasonDropDown.value.lower().replace(' ','-')})
            # Sets the results dict as global
            global results
            if len(options) != 0:
                results = searchWithFilter(searchField.value,options)
            else:    
                # Fetches the search results
                results = search(searchField.value)
            # Places all the buttons containing the anime names
            placeResults(results.keys())
            clear()
    # Search field contains the anime to be searched for
    searchField = ft.TextField(
        label= "Enter anime name",
        on_submit= tempSearch
    )
    def tempMangaSearch(e):
        # If the search field isn't empty
        if searchMangaField.value:
            # Sets the results dict as global
            global results
            # Fetches the search results
            global query
            query = searchMangaField.value
            results = searchForManga(searchMangaField.value)
            # Places all the buttons containing the anime names
            placeMangaResults(results)
            clear()
    # Search field contains the anime to be searched for
    searchMangaField = ft.TextField(
        label= "Enter manga name",
        on_submit= tempMangaSearch
    )
    def clear():
        mangaLangDropdown.options.clear()
        mangaLangDropdown.options.append(ft.dropdown.Option('None'))
        startChapterDropdown.options.clear()
        endChapterDropdown.options.clear()
        searchMangaField.value = ''
        searchField.value = ''
        languageDropDown.value = "None"
        genreDropDown.value = 'None'
        yearDropdown.value = 'None'
        seasonDropDown.value = 'None'
        epFromField.value = ""
        epNumField.value = ""
        quaityDropDown.value = None
    def save(e):
        try:
            os.mkdir(f"{mangaDirec}{name}")
        except:
            print("Directory exists")
        clear()
        page.clean()
        page.add(
            ft.Container(content=ft.Text(value=f"{name}"),))
        container = ft.Column(
        )
        page.add(container)
        page.add(ft.ElevatedButton(text="Main menu",on_click=loadMainPage))
        startChapter = startChapterDropdown.value
        endChapter = endChapterDropdown.value
        startChapterNum = list(results[language].keys()).index(startChapter)
        endChapterNum = list(results[language].keys()).index(endChapter)
        chaptersList = list(results[language].keys())
        for i in range(startChapterNum,endChapterNum+1):
            chapterNumber = results[language][chaptersList[i]][0]
            getPages(results[language][chaptersList[i]][1],name,chapterNumber,container)
            pdfize(f"{mangaDirec}{name}/{name}-{chapterNumber}",name,chapterNumber,container)
        mergePDFS(f"{mangaDirec}{name}",name,container)

    def changeValues(e):
        selectedLanguage = e.control.value
        if selectedLanguage != "None":
            global language
            language = selectedLanguage
            startChapterDropdown.disabled = False
            endChapterDropdown.disabled = False
            startChapterDropdown.options = [ft.dropdown.Option(l) for l in results[selectedLanguage].keys() if l != None]
            endChapterDropdown.options = [ft.dropdown.Option(l) for l in results[selectedLanguage].keys() if l != None]
        page.update()

    mangaLangDropdown = ft.Dropdown(
        label="Language",
        options= [ft.dropdown.Option('None')],
        value = "None",
        on_change=changeValues
    )
    def selectMangaResult(e : ft.ControlEvent):
        text = e.control.text
        global name
        global results
        name = text
        print(text, "selected")
        mangaImg = results[text][1]
        mangaID = results[text][0]
        mangaDesc = getAbout(mangaID)
        results = getChapters(mangaID)
        for i in results.keys():
            if i != None:
                mangaLangDropdown.options.append(ft.dropdown.Option(i))
        global optionsRes

        descSection = ft.Text(
            value='',
        )
        if mangaDesc != None:
            descSection.value = mangaDesc
        saveButton = ft.ElevatedButton(
            text = "Save",
            width = 190,
            on_click=save
            )
        backButton = ft.ElevatedButton(
                text = "Back",
                width = 190,
                on_click=back
            )
        mainMenuButton = ft.ElevatedButton(
                text= "Main Menu",
                width = 190,
                on_click=loadMainPage
            )
        thisResultPage = ft.Column(
            controls=[
                ft.Text(value=text),
                ft.Row(
                    controls = [
                        ft.Image(
                            src = mangaImg,
                            width= 213,
                            height = 300
                        ),
                        ft.Column(
                            controls = [
                                ft.Container(content = descSection, width = 310),mangaLangDropdown
                            ]
                        )

                    ]
                ),
                startChapterDropdown,
                endChapterDropdown,
                ft.Row(
                    controls=[
                        saveButton,backButton,mainMenuButton
                    ],
                    width = 600
                )
            ]
        )
        page.clean()
        page.add(thisResultPage)

    def placeMangaResults(resultKeys):
            # Sets variables as global
            global resultsPage

            # List of results
            resultsList : list = []
            # Results page column
            resultsPage = ft.Column(
                controls= resultsList
            )
            searchquery = searchField.value
            searchquery = searchquery.capitalize()
            resultsPage.controls.append(
                ft.Container(
                    content= ft.Text(
                        value=f"Search : {searchquery}",
                        weight= ft.FontWeight.BOLD,
                        size = 23,
                    ),
                    alignment= ft.alignment.top_center
                )
            )
            # The index variable we use to know the placement of the button
            i : int = 1

            # Loops through the results on page
            for result in resultKeys:
                # If i is 1 then we add a new row
                if i == 1:
                    # Creates a new row list
                    resultsRow : list = []
                    # Creates a new Row with the list
                    thisrow = ft.Row(
                        controls=resultsRow
                    )
                # Appends a button to the result row list
                resultsRow.append(
                    ft.Container(
                        content = ft.Column(
                            controls = [
                                
                                ft.Image(
                                    src = results[result][1],
                                    width= 140,
                                    height = 198,
                                    fit=ft.ImageFit.FILL,
                                    repeat=ft.ImageRepeat.NO_REPEAT,
                                    border_radius=ft.border_radius.all(10)
                                ),
                                ft.TextButton(
                                    text= f"{result}",
                                    on_click= selectMangaResult
                                )
                        ]),
                        width =  200
                    ) 
                )
                # Increments the i
                i += 1
                # If i is 4
                if i == 4:
                    # We append the row to the list
                    resultsList.append(thisrow)
                    # Returns the i to 1
                    i = 1
            # At the end if i isn't 1 then there are results that aren't placed 
            if i != 1:
                # Adds the result list
                resultsList.append(thisrow)
            resultsPage.controls.append(
                ft.Container(
                    content = ft.ElevatedButton(text ="Back",on_click=loadMainPage)
                )
            )
            # Cleans the page
            page.clean()
            # Adds the results page
            page.add(resultsPage)
    # Search page column
    mangaSearchPage = ft.Column(
        controls=[
            # Bold text of size 23
            ft.Text(
                value= "Search for manga",
                weight=ft.FontWeight.BOLD,
                size = 23
            ),
            # Search field that we defined before
            searchMangaField,
            # Row containing the buttons we will use
            ft.Row(
                controls=
                [
                    # Container containing the Search button
                    ft.Container(
                        # Search button that runs the "tempSearch" function
                        content = ft.ElevatedButton(text = "Search",on_click=tempMangaSearch),
                        # The container is alligned to top left
                        alignment= ft.alignment.top_left
                    ),
                    # Container acting as a spacer
                    ft.Container(
                        visible=True,
                        width =390
                    ),
                    # Container containing the Back button
                    ft.Container(
                        # Back button that runs the "loadMainPage" function
                        content = ft.ElevatedButton(text = "Back",on_click=loadMainPage),
                        # Container is alligned to top right
                        alignment= ft.alignment.top_right,
                    )
                ],
                # The row is restricted by width 400
                width = 600,
            ),
            
        ]
    )
    # Back button function
    def back(e):
        clear()
        # Removes everything from the page
        page.clean()
        # Adds the result page
        page.add(resultsPage)

    # Function to load the main menu
    def mainMenu(e):
        clear()
        # Removes everything from the page
        page.clean()
        # Adds the main menu
        page.add(mainPage)

    # Actual function to download the videos
    def DownloadTheFilesFlet(Links,path,startEp,mainLink,quality,email,password,name):
        # Creates a new column for the download page
        pageColumn = ft.Column(
            controls = [ft.Text(value = name, weight=ft.FontWeight.BOLD)]
        )
        downloadPage.controls.append(pageColumn)
        # Adds the page column
        page.add(downloadPage)
        # Adds the main buttons to the page
        page.add(
            ft.Row(

                controls=[
                    # Back buttton to return to the result page
                    ft.ElevatedButton(text = "Back",on_click=back,width=120),
                    # Back button to return to main menu
                    ft.ElevatedButton(text = "Main menu",on_click=mainMenu,width=120),
                ]
            )
        )
        # Sets the name variable as the start episode number
        name = startEp
        # Loops through all links
        for link in Links:
            # The quality of the start atempt
            workingQuality : str = quality
            # List of tried qualities
            tried : list = []
            # Max number of attempts
            max_attempts = 3
            # Saves the time before downloading this episode
            timeBefore = time.time()
            for attempt in range(max_attempts+1):
                # Get the file in chunks
                response = requests.get(link, stream=True)
                if response.status_code == 200:
                    # Calculate size in Bytes
                    total_size_in_bytes = int(response.headers.get('content-length', 0))
                    # Block size of progress bar
                    block_size = 1024  # 1 Kibibyte
                    # Actual progress bar
                    # Creates a progress bar with a random color code
                    progress_bar = ft.ProgressBar(
                        width=600,
                        color= generate_hex_color_code()
                    )
                    # Total bytes collected
                    totalGotten = 0
                    # Sets the text as downloaded data in megabytes over the total to be downloaded in megabytes, all rounded to the hundreth
                    textF = ft.Text(f"{round(totalGotten/(1024*1024),2)} / {round(total_size_in_bytes/(1024*1024),2)} MBs")
                    # Adds the episdoe name in the column
                    pageColumn.controls.append(
                        ft.Text(f"EP{name}"))
                    # Adds the download text and the progress bar to the column
                    pageColumn.controls.append(
                        ft.Column([textF, progress_bar]))
                    
                    # Opens file in binary write mode
                    with open(f"{path}/EP{name}.mp4", "wb") as file:
                        speedTime = time.time()
                        timePassed = 0
                        totalBytes = 0
                        speed = 0
                        # Loops through response as it write it in chunks
                        for data in tqdm(response.iter_content(block_size), desc = f'EP{name}'):
                            totalGotten += len(data)
                            # Updates progress bar
                            progress_bar.value = totalGotten/total_size_in_bytes
                            # Writes data
                            speedDiff = time.time() - speedTime
                            timePassed += speedDiff
                            totalBytes += 1024
                            if timePassed > 0.05:
                                speed = totalBytes / timePassed
                                totalBytes = 0
                                timePassed = 0
                            file.write(data)
                            # Updates the download text
                            textF.value = f"{round(totalGotten/(1024*1024),2)} / {round(total_size_in_bytes/(1024*1024),2)} MBs  {speed/1024: .2f}KBs/s"
                            # Updates the whole page
                            page.update()
                            speedTime = time.time()
                    # Saves the time after the episode is saved
                    timeAfter = time.time()
                    # If it took less than 10 seconds it is most probably an error
                    if timeAfter - timeBefore < 10:
                        # We append the working quality
                        tried.append(workingQuality)
                        # We get a new quality
                        workingQuality = getNewQuality(tried)
                        # If the quality isn't None
                        if workingQuality != None:
                            # We get the new link and try again to download
                            link = LoginAndGoToLink(list(range(name,name+1)),mainLink,workingQuality,email,password)[0]
                            print("Attempt failed, retrying....")
                        else:
                            # Otherwise the episode is unable to be gotten
                            print("Unable to get this episode")
                    else:
                        # Otherwise if all is well we break and download the next episode
                        break
                # If the response wasn't 200 OK
                else:
                    # We append the working quality
                    tried.append(workingQuality)
                    # We get a new quality
                    workingQuality = getNewQuality(tried)
                    # If the quality isn't None
                    if workingQuality != None:
                        # We get the new link and try again to download
                        link = LoginAndGoToLink(list(range(name,name+1)),mainLink,workingQuality,email,password)[0]
                        print("Attempt failed, retrying....")
                        time.sleep(3)
                    else:
                        # Otherwise the episode is unable to be gotten
                        print("Unable to get this episode")
            # Increments name
            name+=1

    genreDropDown = ft.Dropdown(
        options = [
            ft.dropdown.Option('None'),
            ft.dropdown.Option("Action"),
            ft.dropdown.Option("Adventure"),
            ft.dropdown.Option("Anthropomorphic"),
            ft.dropdown.Option("Avant Garde"),
            ft.dropdown.Option("Cars"),
            ft.dropdown.Option("CGDCT"),
            ft.dropdown.Option("Childcare"),
            ft.dropdown.Option("Comedy"),
            ft.dropdown.Option("Comic"),
            ft.dropdown.Option("Crime"),
            ft.dropdown.Option("Delinquents"),
            ft.dropdown.Option("Dementia"),
            ft.dropdown.Option("Demons"),
            ft.dropdown.Option("Detective"),
            ft.dropdown.Option("Drama"),
            ft.dropdown.Option("Dub"),
            ft.dropdown.Option("Family"),
            ft.dropdown.Option("Fantasy"),
            ft.dropdown.Option("Gag Humor"),
            ft.dropdown.Option("Game"),
            ft.dropdown.Option("Gourmet"),
            ft.dropdown.Option("Harem"),
            ft.dropdown.Option("High Stakes Game"),
            ft.dropdown.Option("Historical"),
            ft.dropdown.Option("Horror"),
            ft.dropdown.Option("Isekai"),
            ft.dropdown.Option("Iyashikei"),
            ft.dropdown.Option("Josei"),
            ft.dropdown.Option("Kids"),
            ft.dropdown.Option("Magic"),
            ft.dropdown.Option("Mahou Shoujo"),
            ft.dropdown.Option("Martial Arts"),
            ft.dropdown.Option("Mecha"),
            ft.dropdown.Option("Medical"),
            ft.dropdown.Option("Military"),
            ft.dropdown.Option("Music"),
            ft.dropdown.Option("Mystery"),
            ft.dropdown.Option("Mythology"),
            ft.dropdown.Option("Organized Crime"),
            ft.dropdown.Option("Parody"),
            ft.dropdown.Option("Performing Arts"),
            ft.dropdown.Option("Pets"),
            ft.dropdown.Option("Police"),
            ft.dropdown.Option("Psychological"),
            ft.dropdown.Option("Racing"),
            ft.dropdown.Option("Reincarnation"),
            ft.dropdown.Option("Romance"),
            ft.dropdown.Option("Romantic Subtext"),
            ft.dropdown.Option("Samurai"),
            ft.dropdown.Option("School"),
            ft.dropdown.Option("Sci-Fi"),
            ft.dropdown.Option("Seinen"),
            ft.dropdown.Option("Shoujo"),
            ft.dropdown.Option("Shoujo Ai"),
            ft.dropdown.Option("Shounen"),
            ft.dropdown.Option("Showbiz"),
            ft.dropdown.Option("Slice of Life"),
            ft.dropdown.Option("Space"),
            ft.dropdown.Option("Sports"),
            ft.dropdown.Option("Strategy Game"),
            ft.dropdown.Option("Super Power"),
            ft.dropdown.Option("Supernatural"),
            ft.dropdown.Option("Survival"),
            ft.dropdown.Option("Suspense"),
            ft.dropdown.Option("Team Sports"),
            ft.dropdown.Option("Thriller"),
            ft.dropdown.Option("Time Travel"),
            ft.dropdown.Option("Vampire"),
            ft.dropdown.Option("Video Game"),
            ft.dropdown.Option("Visual Arts"),
            ft.dropdown.Option("Work Life"),
            ft.dropdown.Option("Workplace"),
        ],
        value = 'None',
        label = 'Genre',
        width = 199
    )
    yearDropdown = ft.Dropdown(
        options = [
            ft.dropdown.Option('None'),
            ft.dropdown.Option("1999"),
            ft.dropdown.Option("2000"),
            ft.dropdown.Option("2001"),
            ft.dropdown.Option("2002"),
            ft.dropdown.Option("2003"),
            ft.dropdown.Option("2004"),
            ft.dropdown.Option("2005"),
            ft.dropdown.Option("2006"),
            ft.dropdown.Option("2007"),
            ft.dropdown.Option("2008"),
            ft.dropdown.Option("2009"),
            ft.dropdown.Option("2010"),
            ft.dropdown.Option("2011"),
            ft.dropdown.Option("2012"),
            ft.dropdown.Option("2013"),
            ft.dropdown.Option("2014"),
            ft.dropdown.Option("2015"),
            ft.dropdown.Option("2016"),
            ft.dropdown.Option("2017"),
            ft.dropdown.Option("2018"),
            ft.dropdown.Option("2019"),
            ft.dropdown.Option("2020"),
            ft.dropdown.Option("2021"),
            ft.dropdown.Option("2022"),
            ft.dropdown.Option("2023"),
        ],
        value = 'None',
        label = 'Year',
        width = 130
    )
    languageDropDown = ft.Dropdown(
        options = [
            ft.dropdown.Option("None"),
            ft.dropdown.Option("Sub"),
            ft.dropdown.Option("Dub"),
        ],
        value = 'None',
        label = 'Language',
        width = 110
    )
    seasonDropDown = ft.Dropdown(
        options = [
            ft.dropdown.Option("None"),
            ft.dropdown.Option("Spring"),
            ft.dropdown.Option("Summer"),
            ft.dropdown.Option("Fall"),
            ft.dropdown.Option("Winter"),
        ],
        value = 'None',
        label = 'Season',
        width = 110
    )
    # Search page column
    searchPage = ft.Column(
        controls=[
            # Bold text of size 23
            ft.Text(
                value= "Search for anime",
                weight=ft.FontWeight.BOLD,
                size = 23
            ),
            ft.Row(
                controls = [
                    genreDropDown,yearDropdown,languageDropDown,seasonDropDown
                ],
                width = 600
            ),
            # Search field that we defined before
            searchField,
            # Row containing the buttons we will use
            ft.Row(
                controls=
                [
                    # Container containing the Search button
                    ft.Container(
                        # Search button that runs the "tempSearch" function
                        content = ft.ElevatedButton(text = "Search",on_click=tempSearch),
                        # The container is alligned to top left
                        alignment= ft.alignment.top_left
                    ),
                    # Container acting as a spacer
                    ft.Container(
                        visible=True,
                        width =390
                    ),
                    # Container containing the Back button
                    ft.Container(
                        # Back button that runs the "loadMainPage" function
                        content = ft.ElevatedButton(text = "Back", on_click=loadMainPage),
                        # Container is alligned to top right
                        alignment= ft.alignment.top_right,
                    )
                ],
                # The row is restricted by width 400
                width = 600,
            ),
            
        ]
    )

    # Download Button function 
    def download(e):
        # Prints the download settings
        print("From",epFromField.value)
        print("To",epNumField.value)
        print("Quality", quaityDropDown.value)
        # Adds a text till the links are fetched
        page.add(ft.Text("Fetching videos......"))
        # Defines the episodes range
        eps = list(range(int(epFromField.value),1+int(epNumField.value)))
        # Fetches the links using the "LoginAndGoToLink" function
        videosLinks = LoginAndGoToLink(eps,link,quaityDropDown.value,data["Email"],data["Password"])
        # Cleans the page 
        page.clean()
        # Adds a bold text with the anime name
        
        # Defines path of the anime directory, the name will be derived from the link
        path = f"{data['Directory']}{linkRaw.split('/')[-1]}"
        try:
            # Tries to create the folder
            os.mkdir(path)
        except:
            ...
        # Downloads the episodes
        DownloadTheFilesFlet(videosLinks,path,int(epFromField.value),link,quaityDropDown.value,data["Email"],data["Password"],name)
    def getData(link: str) -> list:
        link = f"https://{domain}{link}"
        session = requests.session()
        htmlData = session.get(link).text
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
    def changeValue(e, episode):
        global selectedEpisode
        selectedEpisode = episode
    def loadPlayPage(e):
        episodesNumber = getNumberOfEpisodes(results[e.control.tooltip][0])
        animeData = getData(results[e.control.tooltip][0])
        eps = list(range(1,int(episodesNumber)+1))
        episodeDropDown = ft.Dropdown(
            label='Episodes',
            on_change= lambda e: changeValue(e,episodeDropDown.value),width=200,

        )
        for ep in eps:
            episodeDropDown.options.append(
                ft.dropdown.Option(f'{ep}')
            )
        playButton = ft.ElevatedButton(text='Play', on_click=lambda e:play(e,int(selectedEpisode),data['Directory']))
        playPage = ft.Column(
        controls=[
            # A text containing the anime name
            ft.Text(e.control.text),

            ft.Row(
                controls = [
                    ft.Image(
                        src=animeData[0],
                        width=213,
                        height=300,
                    ),
                    ft.Column(
                        controls = [
                            ft.Container(content = ft.Text(animeData[2]), width = 310),
                            ft.Text(animeData[1]),
                            ft.Text(animeData[3]),
                            ft.Text(animeData[4]),
                            ft.Text(animeData[5]),
                            ft.Text(f"{episodesNumber} episodes"),
                        ]
                    )
                ]
            ),
            # A text containinf the latest episode number
            # A Container acting as a spacer
            ft.Container(
                height=13
            ),
            # A row with the control fields      data["Password"] = passwordPField.value
   
            ft.Row(
                controls=[
                    # The control fields we defined earlier
                    episodeDropDown,quaityDropDown,
                    ft.Column( controls = [playButton,ft.ElevatedButton(text='Stop', on_click=lambda e:stop(e,data['Directory']))])
                ],
                # The row is restricted to width 400
                width = 600
            ),
            # Another row containg other controls
            ft.Row(
                controls=[
                    # Back button and main menu button with functions "back" and "mainMenu" respectively
                    ft.ElevatedButton(text = "Back",tooltip=name,on_click=selectResult,width=187),
                    ft.ElevatedButton(text = "Main menu",on_click=mainMenu,width=187),
                ]
            )
        ]
        )
        page.clean()
        page.add(playPage)
        page.update()
    def play(e,num :int, path ):
        eps = list(range(num,num+1))
        videosLinks = LoginAndGoToLink(eps,link,quaityDropDown.value,data["Email"],data["Password"])
        print('Got video link')
        if os.name == 'posix':
            print('Playing')
            if os.path.exists(f'{path}vlc.pid'):
                stop(e,path)
            os.system(f'cvlc {videosLinks[0]} & echo $! -> {path}vlc.pid')
        elif os.name == 'nt':
            os.system(f'"{cvlcPath}" {videosLinks[0]}')
    def stop(e,path):
        if os.name == 'posix':
            if os.path.exists(f'{path}vlc.pid'):
                os.system(f'kill -9 $(cat {path}vlc.pid)')
                os.remove(f'{path}vlc.pid')
        elif os.name == 'nt':
            os.system(f'taskkill /im cvlc.exe /f')

    # Function that runs when you select a search result
    def selectResult(e : ft.ControlEvent):
        # Prints the anime name selected
        if e.control.text == 'Back':
            e.control.text = e.control.tooltip
        print(e.control.text, "selected")

        # Edits the variable episodesNumber as the number of episodes availabe for this anime
        global episodesNumber
        episodesNumber = getNumberOfEpisodes(results[e.control.text][0])
        animeData = getData(results[e.control.text][0])
        # Edits the linkRaw variable to the link before formatting
        global linkRaw
        linkRaw = results[e.control.text][0]
        # Edits the name variable to the anime name
        global name
        name = e.control.text
        # Creates a download button with the click event as the "download" function 
        downloadButton = ft.ElevatedButton(text = "Download",on_click=download,width=187)
        # Creates a result page for the selected anime
        resultPage = ft.Column(
        controls=[
            # A text containing the anime name
            ft.Text(e.control.text),

            ft.Row(
                controls = [
                    ft.Image(
                        src=animeData[0],
                        width=213,
                        height=300,
                    ),
                    ft.Column(
                        controls = [
                            ft.Container(content = ft.Text(animeData[2]), width = 310),
                            ft.Text(animeData[1]),
                            ft.Text(animeData[3]),
                            ft.Text(animeData[4]),
                            ft.Text(animeData[5]),
                            ft.Text(f"{episodesNumber} episodes")
                            ,ft.ElevatedButton(text='Play',tooltip=name,on_click=loadPlayPage)
                        ]
                    )
                ]
            ),
            # A text containinf the latest episode number
            # A Container acting as a spacer
            ft.Container(
                height=13
            ),
            # A row with the control fields
            ft.Row(
                controls=[
                    # The control fields we defined earlier
                    epFromField,epNumField,quaityDropDown
                ],
                # The row is restricted to width 400
                width = 600
            ),
            # Another row containg other controls
            ft.Row(
                controls=[
                    # The download button we defined above
                    downloadButton,
                    # Back button and main menu button with functions "back" and "mainMenu" respectively
                    ft.ElevatedButton(text = "Back",on_click=back,width=187),
                    ft.ElevatedButton(text = "Main menu",on_click=mainMenu,width=187),
                ]
            )
        ]
        )
        # Cleans the page
        page.clean()
        # Disables the download button
        downloadButton.disabled = True
        # Adds the result page above
        page.add(resultPage)
        # Adds a text to have the user wait until the link is made
        page.add(ft.Text("Making link....."))
        # Edits the link variable to the link "makeLink" function return value
        global link
        link = makeLink(results[e.control.text][0])
        # We enable the download button
        downloadButton.disabled = False
        # Updates the items
        downloadButton.update()
        resultPage.update()
        page.update()
        # Prints got link
        print("Got link")
        # Removes the text saying "Making link"
        page.remove_at(-1)

    # Function to get the numeric part of the text
    def getNumeric(text : str) -> int:
        num : str = ""
        # Loops through the letters
        for l in text:
            # If the letter is a digit we append it to the num str
            if l.isdigit():
                # Adds the letter
                num += l
        # Returns the num variable as an int
        return int(num)
    
    # Function that runs when you select a search result from the homepage
    def selectHomePageResult(e : ft.ControlEvent):
        # Prints the anime name selected
        print(e.control.text, "selected")
        # Edits the variable episodesNumber as the number of episodes availabe for this anime
        global episodesNumber
        quaityDropDown.disabled = False
        episodesNumber = getNumeric(results[e.control.text][1])
        animeData = getData(getAnimeLink(f'{results[e.control.text][0]}-{episodesNumber}'))
        # Edits the linkRaw variable to the link before formatting
        global linkRaw
        linkRaw = formatHomePageLink(results[e.control.text][0])
        # Edits the name variable to the anime name
        global name
        name = e.control.text
        # Creates a download button with the click event as the "download" function 
        downloadButton = ft.ElevatedButton(text = "Download",on_click=download,width=187)
        # Creates a result page for the selected anime
        resultPage = ft.Column(
        controls=[
            # A text containing the anime name
            ft.Text(e.control.text),
            ft.Row(
                controls = [
                    ft.Image(
                        src=animeData[0],
                        width=213,
                        height=300,
                    ),
                    ft.Column(
                        controls = [
                            ft.Container(content = ft.Text(animeData[2]), width = 310),
                            ft.Text(animeData[1]),
                            ft.Text(animeData[3]),
                            ft.Text(animeData[4]),
                            ft.Text(animeData[5]),
                            ft.Text(f"{episodesNumber} episodes"),
                        ]
                    )
                ]
            ),
            # A text containinf the latest episode number
            # A Container acting as a spacer
            ft.Container(
                height=13
            ),
            # A row with the control fields
            ft.Row(
                controls=[
                    # The control fields we defined earlier
                    epFromField,epNumField,quaityDropDown
                ],
                # The row is restricted to width 400
                width = 600
            ),
            # Another row containg other controls
            ft.Row(
                controls=[
                    # The download button we defined above
                    downloadButton,
                    # Back button and main menu button with functions "back" and "mainMenu" respectively
                    ft.ElevatedButton(text = "Back",on_click=back,width=187),
                    ft.ElevatedButton(text = "Main menu",on_click=mainMenu,width=187),
                ]
            )
        ]
        )
        # Cleans the page
        page.clean()
        # Adds the result page above
        page.add(resultPage)
        # Edits the link variable to the link we got
        global link
        link = results[e.control.text][0]
        # Updates the page
        page.update()

    # Function to places the results
    def placeResults(resultKeys):
        # Sets variables as global
        global resultsPage

        # List of results
        resultsList : list = []
        # Results page column
        resultsPage = ft.Column(
            controls= resultsList
        )
        searchquery = searchField.value
        searchquery = searchquery.capitalize()
        resultsPage.controls.append(
            ft.Container(
                content= ft.Text(
                    value=f"Search : {searchquery}",
                    weight= ft.FontWeight.BOLD,
                    size = 23,
                ),
                alignment= ft.alignment.top_center
            )
        )
        # The index variable we use to know the placement of the button
        i : int = 1

        # Loops through the results on page
        for result in resultKeys:
            # If i is 1 then we add a new row
            if i == 1:
                # Creates a new row list
                resultsRow : list = []
                # Creates a new Row with the list
                thisrow = ft.Row(
                    controls=resultsRow
                )
            # Appends a button to the result row list
            resultsRow.append(
                ft.Container(
                    content = ft.Column(
                        controls = [
                            
                            ft.Image(
                                src = results[result][1],
                                width= 140,
                                height = 198,
                                fit=ft.ImageFit.FILL,
                                repeat=ft.ImageRepeat.NO_REPEAT,
                                border_radius=ft.border_radius.all(10)
                            ),
                            ft.TextButton(
                                text= f"{result}",
                                on_click= selectResult
                            )
                    ]),
                    width =  200
                ) 
            )
            # Increments the i
            i += 1
            # If i is 4
            if i == 4:
                # We append the row to the list
                resultsList.append(thisrow)
                # Returns the i to 1
                i = 1
        # At the end if i isn't 1 then there are results that aren't placed 
        if i != 1:
            # Adds the result list
            resultsList.append(thisrow)
        resultsPage.controls.append(
            ft.Container(
                content = ft.ElevatedButton(text ="Back", on_click=loadMainPage),
            )
        )
        # Cleans the page
        page.clean()
        # Adds the results page
        page.add(resultsPage)

    def placeResultsHome(resultKeys):
        # Sets variables as global
        global resultsPage

        # List of results
        resultsList : list = []
        # Results page column
        resultsPage = ft.Column(
            controls= resultsList
        )
        resultsPage.controls.append(
            ft.Container(
                content= ft.Text(
                    value="Home Page",
                    weight= ft.FontWeight.BOLD,
                    size = 23,
                ),
                alignment= ft.alignment.top_center
            )
        )
        # The index variable we use to know the placement of the button
        i : int = 1

        # Loops through the results on page
        for result in resultKeys:
            # If i is 1 then we add a new row
            if i == 1:
                # Creates a new row list
                resultsRow : list = []
                # Creates a new Row with the list
                thisrow = ft.Row(
                    controls=resultsRow
                )
            # Appends a button to the result row list
            resultsRow.append(
                ft.Container(
                    content = ft.Column(
                        controls = [
                            ft.Image(
                                src = results[result][2],
                                width= 140,
                                height = 198,
                                fit=ft.ImageFit.FILL,
                                repeat=ft.ImageRepeat.NO_REPEAT,
                                border_radius=ft.border_radius.all(10)
                            ),
                            ft.TextButton(
                                text= f"{result}",
                                on_click= selectHomePageResult
                            ),ft.Text(results[result][1])
                    ]),
                    width =  200
                ) 
            )
            # Increments the i
            i += 1
            # If i is 4
            if i == 4:
                # We append the row to the list
                resultsList.append(thisrow)
                # Returns the i to 1
                i = 1
        # At the end if i isn't 1 then there are results that aren't placed 
        if i != 1:
            # Adds the result list
            resultsList.append(thisrow)
        resultsPage.controls.append(
            ft.Container(
                content = ft.ElevatedButton(text ="Back", on_click=loadMainPage),
            )
        )
        # Cleans the page
        page.clean()
        # Adds the results page
        page.add(resultsPage)
        
    # Text field for the new domain
    newDomainField = ft.TextField(
        label = "New domain"
    )

    # Function for the change domain button
    def changeDomainPressed(e):
        # If the domain field isn't empty
        if newDomainField.value:
            # Runs the "changeDomain" function
            changeDomain(newDomainField.value)
            # Edits the domain variable to the new domain
            global domain
            domain = newDomainField.value
    
    # Text with the old domain name for reference when changing the domain
    oldDomainText = ft.Text(
                value = f"Old domain: {domain}"
    )

    # Change domain page column
    changeDomainPage = ft.Column(
        controls=[
            # Bold text of size 18
            ft.Text(
                value = "Change Domain"
                ,size=18
                ,weight=ft.FontWeight.BOLD
            ),
            # The old domain text we created above
            oldDomainText,
            # New domain text field we creatde above
            newDomainField,
            # Row with the button controls
            ft.Row(
                controls=[
                    # Button to change the domain with the "changeDomainPressed" function
                    ft.ElevatedButton(text="Change", on_click=changeDomainPressed),
                    # Button to go back to the main menu with the "mainMenu" function
                    ft.ElevatedButton(text="Back", on_click=mainMenu),
                ]
            )
        ]
    )
    def modeDropDownChange(e):
        if e.control.value == 'Dark':
            page.theme_mode = "Dark"
        else:
            page.theme_mode = "Light"
        page.update()
    # Color mode dropdown menu
    modeDropDown = ft.Dropdown(
        options=[
            # Options of "Dark" and "Light"
            ft.dropdown.Option("Dark"),
            ft.dropdown.Option("Light")
        ],
        # The hint text is the current mode
        hint_text= data["Mode"],
        # The actual value is also the current mode
        value=data["Mode"],
        on_change= modeDropDownChange
    )
    # Email field with the loaded value from the data file
    emailPField = ft.TextField(
        label="Email",
        value=data["Email"]
    )
    # Password field with the loaded value from the data file
    passwordPField = ft.TextField(
        label="Password",
        value=data["Password"],
        can_reveal_password = True,
        password = True
    )
    # Directory field with the loaded value from the data file
    defaultDirectory = ft.TextField(
        label="Download Directory",
        value=data["Directory"]
    )   
    cvlcPathFeild = ft.TextField(
        label="CVLC path, Windows only",
        value=data["Player"]
    )  
    defaultMangaDirectory = ft.TextField(
        label="Manga Directory",
        value=data["Manga_Directory"]
    )
    # Color theme field with the loaded value from the data file
    colorTheme = ft.TextField(
        label="Color code",
        value=data["Color"]
    )
    # Function to save the new preferences
    def savePreferences(e):
        # Runs if all the fields aren't empty
        if emailPField.value and passwordPField.value and defaultDirectory.value and colorTheme.value:
            # Sets the data from the email field value
            data["Email"] = emailPField.value
            # Sets the data from the password field value

            data["Password"] = passwordPField.value
            # Sets the data from the direcotiry field value
            data["Directory"] = defaultDirectory.value
            try:
                os.mkdir(defaultDirectory.value)
            except: pass
            data["Manga_Directory"] = defaultMangaDirectory.value
            try:
                os.mkdir(defaultMangaDirectory.value)
            except: pass
            data["Player"] = cvlcPathFeild.value
            # Sets the data from the mode dropdown value
            data["Mode"] = modeDropDown.value
            # Sets the data from the color theme value
            data["Color"] = newColorCode if radioGP.value == "Slider" else "random"
            # Saves the data to the json file
            with open("./preferences.json",'w') as f:
                json.dump(data,f,indent=4)
            
            # Cleans the page
            page.clean()
            # Sets the page theme to the mode from the dropdown menu
            page.theme_mode = modeDropDown.value
            colorCode = ""
            cvlcPath = cvlcPathFeild.value
            # If the color theme prefernces is random
            if radioGP.value == "Random":
                randomColorCode = generate_hex_color_code()
            # We generate a random color code for the theme
                colorCode = randomColorCode
            else:
                # Otherwise we use the one provided
                colorCode = newColorCode
            # Sets up the thene with the color code from above
            page.theme = ft.Theme(
                color_scheme=ft.ColorScheme(
                    primary= colorCode
                )
            )
            # Updates the page
            page.update()
            # Adds the main page
            page.add(mainPage)
    
    def onSlide(e):
        redHex = hex(int(redSlider.value*255)).replace('0x','')
        if len(redHex) == 1:
            redHex = f"0{redHex}"
        blueHex = hex(int(blueSlider.value*255)).replace('0x','')
        if len(blueHex) == 1:
            blueHex = f"0{blueHex}"
        greenHex = hex(int(greenSlider.value*255)).replace('0x','')
        if len(greenHex) == 1:
            greenHex = f"0{greenHex}"
        global newColorCode
        newColorCode = f"#{redHex}{greenHex}{blueHex}"
        page.theme = ft.Theme(
            color_scheme=ft.ColorScheme(
            primary= newColorCode
            )
        )
        page.update()

    redSlider = ft.Slider(
        min=0,max=1,
        value =1,
        on_change=onSlide
    )
    blueSlider = ft.Slider(
        min=0,max=1,
        value =1,
        on_change=onSlide
    )
    greenSlider = ft.Slider(
        min=0,max=1,
        value =1,
        on_change=onSlide
    )
    def radioPress(e):
        value = e.control.value
        global colorValue
        if value == "Random":
            redSlider.disabled = True
            greenSlider.disabled = True
            blueSlider.disabled = True
        else:
            redSlider.disabled = False
            greenSlider.disabled = False
            blueSlider.disabled = False
        page.update()

    radioGP = ft.RadioGroup(content=ft.Column([
        ft.Radio(value="Random", label="Random"),
        ft.Radio(value="Slider", label="Slider")]), on_change=radioPress)
    
    if data["Color"] != "random":
        redSlider.value = int(data["Color"][1:3],16) / 255
        greenSlider.value = int(data["Color"][3:5],16) / 255
        blueSlider.value = int(data["Color"][5:],16) / 255
        radioGP.value = "Slider"
    else:
        redSlider.value = int(randomColorCode[1:3],16) / 255
        greenSlider.value = int(randomColorCode[3:5],16) / 255
        blueSlider.value = int(randomColorCode[5:],16) / 255
        radioGP.value = "Random"
        redSlider.disabled = True
        greenSlider.disabled = True
        blueSlider.disabled = True

    # Preferences control page
    preferencesPage = ft.Column(
        controls=[
            # Row with the mode drop down menu and text
            ft.Row(
                controls=[
                    # Container of the text viewing the dropdown menu purpose
                    ft.Container(
                        content=ft.Text(
                            "Color Mode"
                        ),
                        width = 370
                    ),
                    # Container with the dropdown menu
                    ft.Container(
                        content = modeDropDown,
                        width = 200
                    )
                ]
            ),
            # Email and password fields we created earlier
            emailPField,passwordPField,
            # Text acting as a tool tip and the default directory field we created earlier
            ft.Text("Directory name must end with a slash /"),defaultDirectory,defaultMangaDirectory,cvlcPathFeild,
            ft.Text("Color theme: "),radioGP,ft.Text("Red: "),redSlider,ft.Text("Green: "),greenSlider,ft.Text("Blue: "),blueSlider,
            # Container with the save button
            ft.Container(
                # Save button with the "savePreferences" function 
                content = ft.ElevatedButton(text="Save",on_click=savePreferences),
                # Alligned to centre
                alignment=ft.alignment.center
            )
        ]
    )

    # Function that loads the change domain page
    def loadChangeDomainPage(e):
        # CLeans the page
        page.clean()
        # Adds the change domain page
        page.add(changeDomainPage)
        # Changes the value of the old domain text in case of multiple changes in a single run
        oldDomainText.value = f"Old domain: {domain}"
        # Updates the change domain page
        changeDomainPage.update()

    # Function to load the home page
    def loadHomePage(e):
        global results
        # Gets the results from the "getHomePage" function
        results = getHomePage()
        # Places the results
        placeResultsHome(results.keys())

    # Function that loads the preferences page
    def loadMenu(e):
        # Cleans the page
        page.clean()
        global newColorCode
        newColorCode = data["Color"]
        # Adds the preferences page
        page.add(preferencesPage)

    # Button to load settings page
    settingsButton = ft.ElevatedButton(text="Settings", on_click=loadMenu)
    def loadManga(e):
        page.clean()
        page.add(mangaSearchPage)
    # Main page column
    mainPage = ft.Column(
        controls= [
            # Container with the title
            ft.Container(
                # Text with Bold weight and size of 32
                content=ft.Text(
                    value = "NeoBatcher"
                    ,size=32
                    ,weight=ft.FontWeight.BOLD
                    ),
                # Padding around the container of 45 pixels
                padding= 45
            ),
            # Row with the button controls
            ft.Row(
                controls=[
                    # Button to load the home page that runs the "loadHomePage" function
                    ft.ElevatedButton(text="Home Page", on_click=loadHomePage,width = 170),
                    # Button to load the search page that runs the "loadSearchPage" function
                    ft.ElevatedButton(text="Download Anime", on_click=loadSearchPage,width = 170)
                ],
            # Row allignment is centre
            alignment= ft.MainAxisAlignment.CENTER
            ),
            ft.ElevatedButton(text="Download Manga", on_click=loadManga),
            # A button that loads the change domain page with the "loadChangeDomainPage" function
            ft.ElevatedButton(text="Change Domain", on_click=loadChangeDomainPage),
            # Settings button
            settingsButton,
            # Container with the version number
            ft.Container(
                # Text of size 12
                content = ft.Text(
                    value="V3.5",
                    size = 12
                ),
                # Container padding of size 30
                padding = 30
            ),
        ],
        # Main page horizontal alignment is centre
        horizontal_alignment= ft.CrossAxisAlignment.CENTER
    )
    
    # If the email or password aren't useable 
    if len(data["Email"]) < 1 or len(data["Password"]) < 1:
        # Adds the login page
        page.add(loginScreen)
    else:
        page.add(mainPage)


# If the app is ran as a file not as a library
if __name__ == "__main__":
    # We run the flet app with the target as the main function
    ft.app(target=main)
    