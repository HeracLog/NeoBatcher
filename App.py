import time
import requests
import os
import flet as ft
import json 
import subprocess
from assets.utils.gogo import GogoanimeBatcher
from assets.utils.manga import MangaDex
from assets.ui.ResultWindow import ResultWindow
from assets.ui.Dropdowns import Dropdowns
from assets.ui.Toolbar import ToolBar
from assets.ui.MangaPage import MangaPage 

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
nameM : str = ""
results : dict = {}
resultsM : dict = {}
episodesNumber : int = 0
resultsList : list = []
toolbar = ToolBar()
# Results page intialization 
resultsPage = ft.Column(
)
drop = Dropdowns()
# Loads the data
data = loadData()
direc = data["Directory"]
mangaDirec = data["Manga_Directory"]
cvlcPath = data['Player']
gogobatcher = GogoanimeBatcher(data['Email'],data['Password'],direc,data["Domain"])
mangadex = MangaDex(mangaDirec)
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
selectedChapter = 0
query = ""
language = ""

currentPage = None
ring = ft.Row(controls=[ft.ProgressRing()],alignment=ft.MainAxisAlignment.CENTER)
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
    controls=[
        ft.Text('Download Page', size=12,weight=ft.FontWeight.BOLD)
    ]
)
newColorCode : str = ""
randomColorCode : str = ""
mangaPages = []

# Main function where all the magic happens
# This is mostly flet stuff and GUI
def main(page : ft.Page):
    global currentPage
    def ceil(x):
        if x == 0: return 0
        return int(x)+1
    
    def resizeImages():
        ims = []
        if isinstance(currentPage,MangaPage):
            for i in currentPage.controls:
                if isinstance(i,ft.Row) and i.key == 'imgRow':
                    ims.append(i.controls[0])
            for i in ims:
                i.width  = page.window_width - int(page.window_width*0.2)
        page.update()
    def resize(e):
        items = []
        if isinstance(currentPage,MangaPage):
            resizeImages()
            return
        if resultsPage in page.controls:
            ind = page.controls.index(resultsPage)
            for control in page.controls[ind].controls[1:]:
                if isinstance(control,ft.Row):
                    for res in control.controls:
                        items.append(res)

            itemCount = int(page.window_width // 160)
            if itemCount == 0: itemCount =1
            text = page.controls[ind].controls[0]
            resultsPage.controls.clear()
            resultsPage.controls.append(text)
            colCount = ceil(len(items)/itemCount)
            for _ in range(colCount):
                r = ft.Row(controls=[],alignment=ft.MainAxisAlignment.SPACE_BETWEEN)
                for _ in range(itemCount):
                    if items:
                        r.controls.append(
                            items.pop(0)
                        )
                resultsPage.controls.append(r)
        page.update()

    page.on_resize = resize
    # Inializes email and password fields 
    emailField = ft.TextField(
        label="Email",
        icon=ft.icons.MAIL
    )
    passwordField = ft.TextField(
        label="Password",
        password = True,
        can_reveal_password= True,
        icon = ft.icons.LOCK
    )
    # Login action function
    def login(e):
        # If the fields aren't empty
        if emailField.value and passwordField.value:
            # Chanegs email in the data dict
            data["Email"] = emailField.value
            # Chanegs password in the data dict
            data["Password"] = passwordField.value
            gogobatcher.email = emailField.value
            gogobatcher.password = passwordField.value
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
        randomColorCode = mangadex.generate_hex_color_code()
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
    page.window_height = 600
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
        keyboard_type= ft.KeyboardType.NUMBER,
        input_filter=ft.InputFilter(allow=True, regex_string=r"[0-9]", replacement_string="")
    )
    # Defines the episode we stop at
    epNumField = ft.TextField(
        label = "Till episode",
        width = 187,
        keyboard_type= ft.KeyboardType.NUMBER,
        input_filter=ft.InputFilter(allow=True, regex_string=r"[0-9]", replacement_string="")
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

    
    # Function to load the search page
    def loadSearchPage(e):
        global currentPage
        # Removes everything from the page
        page.remove(currentPage)
        # Adds the search page
        page.add(searchPage)
        currentPage = searchPage

    # Function to place results
    def tempSearch(e):
        options = {}
        # If the search field isn't empty
        if searchField.value:   
            currentPage.controls.append(ring)
            page.update()
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
                results = gogobatcher.searchWithFilter(searchField.value,options)
            else:    
                # Fetches the search results
                results = gogobatcher.search(searchField.value)
            # Places all the buttons containing the anime names
            placeResults(results.keys(),'a')
            clear()
    # Search field contains the anime to be searched for
    searchField = ft.TextField(
        label= "Enter anime name",
        on_submit= tempSearch,
        icon = ft.icons.SEARCH
    )
    def tempMangaSearch(e):
        # If the search field isn't empty
        if searchMangaField.value:
            currentPage.controls.append(ring)
            page.update()
            # Sets the results dict as global
            global results
            # Fetches the search results
            global query
            query = searchMangaField.value
            results = mangadex.searchForManga(searchMangaField.value)
            # Places all the buttons containing the anime names
            placeResults(results,'m')
            clear()
    # Search field contains the anime to be searched for
    searchMangaField = ft.TextField(
        label= "Enter manga name",
        on_submit= tempMangaSearch,
        icon = ft.icons.SEARCH
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

    def loadReadManga(e): 
        text = e.control.tooltip
        global nameM
        global resultsM
        nameM = text
        print(text, "selected")
        mangaImg = results[text][1]
        mangaID = results[text][0]
        mangaDesc = mangadex.getAbout(mangaID)
        resultsM = mangadex.getChapters(mangaID)
        for i in resultsM.keys():
            if i != None:
                mangaLangDropdown.options.append(ft.dropdown.Option(i))
        global optionsRes

        descSection = ft.Text(
            value='',
        )
        if mangaDesc != None:
            descSection.value = mangaDesc
        saveButton = ft.ElevatedButton(
            text = "Read",
            width = 190,
            on_click=readManga
            )
        backButton = ft.ElevatedButton(
                text = "Back",
                width = 190,
                on_click=selectMangaResult,
                tooltip = nameM
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

                    ],
                    alignment=ft.MainAxisAlignment.SPACE_EVENLY
                ),
                startChapterDropdown,
                ft.Row(
                    controls=[
                        saveButton,backButton
                    ],
                alignment=ft.MainAxisAlignment.SPACE_AROUND
                )
            ]
        )
        global currentPage
        page.remove(currentPage)
        page.add(thisResultPage)
        currentPage = thisResultPage
    def onprev(e):
        global selectedChapter
        ind = list(resultsM[language].keys()).index(selectedChapter)-1
        selectedChapter = list(resultsM[language].keys())[ind]
        startChapterDropdown.value = selectedChapter
        readManga(e)

    def onnext(e):
        global selectedChapter
        ind = list(resultsM[language].keys()).index(selectedChapter)+1
        selectedChapter = list(resultsM[language].keys())[ind]
        startChapterDropdown.value = selectedChapter
        readManga(e)

    def readManga(e):
        global currentPage
        currentPage.controls.append(ring)
        page.update()

        global selectedChapter
        selectedChapter = startChapterDropdown.value
        startChapter = startChapterDropdown.value
        startChapterNum = list(resultsM[language].keys()).index(startChapter)
        chaptersList = list(resultsM[language].keys())
        chapterNumber = resultsM[language][chaptersList[startChapterNum]][0]
        pages = mangadex.getPages(resultsM[language][chaptersList[startChapterNum]][1],nameM,chapterNumber,nameM,None,page,True)
        global mangaPages
        mangaPages = []
        if not pages: pages = ['']
        if startChapterNum == 0:
            onp = None
        else:
            onp = onprev
        if startChapterNum == len(chaptersList)-1:
            onn = None
        else:
            onn = onnext
            
        mangaPages.append(
                MangaPage(
                    name=nameM,
                    src=pages[0],
                    imwid=page.window_width - int(page.window_width*0.2),
                    onback=loadReadManga,
                    onprev=onp,
                    onnext=onn
                )
            )
        currentPage.controls.remove(ring)
        page.remove(currentPage)
        page.add(mangaPages[0])
        currentPage = mangaPages[0]
        page.update()
        currentPage.onStart(e,pages[1:],page)

    def save(e):
        global currentPage
        currentPage.controls.append(ring)
        page.update()
        try:
            os.mkdir(f"{mangaDirec}{nameM}")
        except:
            print("Directory exists")
        clear()
        currentPage.controls.remove(ring)
        page.remove(currentPage)
        page.add(downloadPage)
        currentPage = downloadPage
        downloadPage.controls.append(
            ft.Container(content=ft.Text(value=f"{name}"),))
        container = ft.Column()
        downloadPage.controls.append(container)
        startChapter = startChapterDropdown.value
        endChapter = endChapterDropdown.value
        startChapterNum = list(resultsM[language].keys()).index(startChapter)
        endChapterNum = list(resultsM[language].keys()).index(endChapter)
        chaptersList = list(resultsM[language].keys())
        for i in range(startChapterNum,endChapterNum+1):
            chapterNumber = resultsM[language][chaptersList[i]][0]
            mangadex.getPages(resultsM[language][chaptersList[i]][1],nameM,chapterNumber,nameM,container,page)
            mangadex.pdfize(f"{mangaDirec}{nameM}/{nameM}-{chapterNumber}",nameM,chapterNumber,container,page)
        mangadex.mergePDFS(f"{mangaDirec}{nameM}",nameM,container,page)

    def changeValues(e):
        selectedLanguage = e.control.value
        if selectedLanguage != "None":
            global language
            language = selectedLanguage
            startChapterDropdown.disabled = False
            endChapterDropdown.disabled = False
            startChapterDropdown.options = [ft.dropdown.Option(l) for l in resultsM[selectedLanguage].keys() if l != None]
            endChapterDropdown.options = [ft.dropdown.Option(l) for l in resultsM[selectedLanguage].keys() if l != None]
        page.update()

    mangaLangDropdown = ft.Dropdown(
        label="Language",
        options= [ft.dropdown.Option('None')],
        value = "None",
        on_change=changeValues
    )
    def selectMangaResult(e : ft.ControlEvent):
        text = e.control.tooltip
        global currentPage
        global nameM
        global resultsM
        currentPage.controls.append(ring)
        page.update()
        nameM = text
        print(text, "selected")
        mangaImg = results[text][1]
        mangaID = results[text][0]
        mangaDesc = mangadex.getAbout(mangaID)
        resultsM = mangadex.getChapters(mangaID)
        for i in resultsM.keys():
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

                    ],
                    alignment=ft.MainAxisAlignment.SPACE_EVENLY
                ),
                startChapterDropdown,
                endChapterDropdown,
                ft.Row(
                    controls=[
                        ft.ElevatedButton(text='Read',on_click=loadReadManga,tooltip=nameM,width=190),saveButton,backButton
                    ],
                alignment=ft.MainAxisAlignment.SPACE_AROUND
                )
            ]
        )
        currentPage.controls.remove(ring)
        page.remove(currentPage)
        page.add(thisResultPage)
        currentPage = thisResultPage

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
                ],
                # The row is restricted by width 400
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN                
            ),
            
        ]
    )
    # Back button function
    def back(e):
        clear()
        global currentPage
        # Removes everything from the page
        page.remove(currentPage)
        # Adds the result page
        page.add(resultsPage)
        currentPage = resultsPage


    # Actual function to download the videos
    def DownloadTheFilesFlet(Links,path,startEp,mainLink,quality,email,password,name):
        # Creates a new column for the download page
        pageColumn = ft.Column(
            controls = [ft.Text(value = name, weight=ft.FontWeight.BOLD)]
        )
        downloadPage.controls.append(pageColumn)
        # Adds the page column
        global currentPage
        page.add(downloadPage)
        currentPage = downloadPage
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
                        color= mangadex.generate_hex_color_code()
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
                        for data in response.iter_content(block_size):
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
                        workingQuality = gogobatcher.getNewQuality(tried)
                        # If the quality isn't None
                        if workingQuality != None:
                            # We get the new link and try again to download
                            link = gogobatcher.getDownloadLinks(list(range(name,name+1)),mainLink,workingQuality)[0]
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
                    workingQuality = gogobatcher.getNewQuality(tried)
                    # If the quality isn't None
                    if workingQuality != None:
                        # We get the new link and try again to download
                        link = gogobatcher.getDownloadLinks(list(range(name,name+1)),mainLink,workingQuality)[0]
                        print("Attempt failed, retrying....")
                        time.sleep(3)
                    else:
                        # Otherwise the episode is unable to be gotten
                        print("Unable to get this episode")
            # Increments name
            name+=1

    genreDropDown = drop.genres
    yearDropdown = drop.years
    languageDropDown = drop.language
    seasonDropDown = drop.season
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
                alignment=ft.MainAxisAlignment.START
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
                    )
                ],
                # The row is restricted by width 400
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN
            ),
            
        ]
    )

    # Download Button function 
    def download(e):
        global currentPage
        # Prints the download settings
        currentPage.controls.append(ring)
        page.update()
        print("From",epFromField.value)
        print("To",epNumField.value)
        print("Quality", quaityDropDown.value)
        # Adds a text till the links are fetched
        currentPage.controls.append(ft.Text("Fetching videos......"))
        # Defines the episodes range
        eps = list(range(int(epFromField.value),1+int(epNumField.value)))
        # Fetches the links using the "LoginAndGoToLink" function
        videosLinks = gogobatcher.getDownloadLinks(eps,link,quaityDropDown.value)
        # Cleans the page 
        currentPage.controls.remove(ring)
        page.remove(currentPage)
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
    
    def changeValue(e, episode):
        global selectedEpisode
        selectedEpisode = episode
    def loadPlayPage(e):
        global currentPage
        currentPage.controls.append(ring)
        page.update()
        episodesNumber = gogobatcher.getNumberOfEpisodes(results[e.control.tooltip][0])
        animeData = gogobatcher.getAnimeData(results[e.control.tooltip][0])
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
            ft.Text(e.control.tooltip),

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
                ],
                alignment=ft.MainAxisAlignment.SPACE_EVENLY
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
                alignment= ft.MainAxisAlignment.CENTER
            ),
            # Another row containg other controls
            ft.Row(
                controls=[
                    # Back button and main menu button with functions "back" and "mainMenu" respectively
                    ft.ElevatedButton(text = "Back",tooltip=name,on_click=selectResult,width=187),
                ],
                alignment=ft.MainAxisAlignment.SPACE_EVENLY
            )
        ]
        )
        currentPage.controls.remove(ring)
        page.remove(currentPage)
        page.add(playPage)
        currentPage = playPage
        page.update()
    def play(e,num :int, path ):
        eps = list(range(num,num+1))
        videosLinks = gogobatcher.getDownloadLinks(eps,link,quaityDropDown.value)
        print('Got video link')
        if os.name == 'posix':
            print('Playing')
            if os.path.exists(f'{path}vlc.pid'):
                stop(e,path)
            os.system(f'cvlc {videosLinks[0]} & echo $! -> {path}vlc.pid')
        elif os.name == 'nt':
            try: stop(e,path)
            except : pass
            playerPath = os.path.normpath(f'{cvlcPath}vlc.exe')
            command = [playerPath,videosLinks[0]]
            subprocess.Popen(command,shell=True)
    def stop(e,path):
        if os.name == 'posix':
            if os.path.exists(f'{path}vlc.pid'):
                os.system(f'kill -9 $(cat {path}vlc.pid)')
                os.remove(f'{path}vlc.pid')
        elif os.name == 'nt':
             os.system(f'taskkill /im vlc.exe /f')

    # Function that runs when you select a search result
    def selectResult(e : ft.ControlEvent):
        # Prints the anime name selected
        print(e.control.tooltip, "selected")
        global currentPage
        currentPage.controls.insert(0,ring)
        page.update()
        # Edits the variable episodesNumber as the number of episodes availabe for this anime
        global episodesNumber
        episodesNumber = gogobatcher.getNumberOfEpisodes(results[e.control.tooltip][0])
        animeData = gogobatcher.getAnimeData(results[e.control.tooltip][0])
        # Edits the linkRaw variable to the link before formatting
        global linkRaw
        linkRaw = results[e.control.tooltip][0]
        # Edits the name variable to the anime name
        global name
        name = e.control.tooltip
        # Creates a download button with the click event as the "download" function 
        downloadButton = ft.ElevatedButton(text = "Download",on_click=download,width=187)
        # Creates a result page for the selected anime
        resultPage = ft.Column(
        controls=[
            # A text containing the anime name
            ft.Text(e.control.tooltip),

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
                        ]
                    )
                ],
                alignment=ft.MainAxisAlignment.SPACE_EVENLY
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
                alignment=ft.MainAxisAlignment.CENTER
            ),
            # Another row containg other controls
            ft.Row(
                controls=[
                    ft.ElevatedButton(text='Play',tooltip=name,on_click=loadPlayPage,width=187),
                    # The download button we defined above
                    downloadButton,
                    # Back button and main menu button with functions "back" and "mainMenu" respectively
                    ft.ElevatedButton(text = "Back",on_click=back,width=187),
                ],
                alignment=ft.MainAxisAlignment.SPACE_AROUND
            )
        ]
        )
        # Cleans the page
        currentPage.controls.remove(ring)
        page.remove(currentPage)
        # Disables the download button
        downloadButton.disabled = True
        # Adds the result page above
        page.add(resultPage)
        currentPage = resultPage
        # Adds a text to have the user wait until the link is made
        resultPage.controls.append(ft.Text("Making link....."))
        # Edits the link variable to the link "makeLink" function return value
        global link
        link = gogobatcher.makeLink(results[e.control.tooltip][0])
        # We enable the download button
        downloadButton.disabled = False
        # Updates the items
        downloadButton.update()
        resultPage.controls.pop(-1)
        resultPage.update()
        page.update()
        # Prints got link
        print("Got link")
        # Removes the text saying "Making link"

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
        print(e.control.tooltip, "selected")
        global currentPage

        currentPage.controls.insert(0,ring)
        page.update()
        # Edits the variable episodesNumber as the number of episodes availabe for this anime
        global episodesNumber
        quaityDropDown.disabled = False
        episodesNumber = getNumeric(results[e.control.tooltip][1])
        animeData = gogobatcher.getAnimeData(gogobatcher.getAnimeLink(f'{results[e.control.tooltip][0]}-{episodesNumber}'))
        # Edits the linkRaw variable to the link before formatting
        global linkRaw
        linkRaw = gogobatcher.formatHomePageLink(results[e.control.tooltip][0])
        # Edits the name variable to the anime name
        global name
        name = e.control.tooltip
        # Creates a download button with the click event as the "download" function 
        downloadButton = ft.ElevatedButton(text = "Download",on_click=download,width=187)
        # Creates a result page for the selected anime
        resultPage = ft.Column(
        controls=[
            # A text containing the anime name
            ft.Text(e.control.tooltip),
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
                ],
                alignment=ft.MainAxisAlignment.SPACE_EVENLY
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
                alignment=ft.MainAxisAlignment.CENTER
            ),
            # Another row containg other controls
            ft.Row(
                controls=[
                    # The download button we defined above
                    ft.ElevatedButton(text='Play',tooltip=name,on_click=loadPlayPage,width=187),
                    downloadButton,
                    # Back button and main menu button with functions "back" and "mainMenu" respectively
                    ft.ElevatedButton(text = "Back",on_click=back,width=187),
                ],
                alignment=ft.MainAxisAlignment.SPACE_AROUND
            )
        ]
        )
        # Cleans the page
        currentPage.controls.remove(ring)
        page.remove(currentPage)
        # Adds the result page above
        page.add(resultPage)
        currentPage = resultPage
        # Edits the link variable to the link we got
        global link
        link = results[e.control.tooltip][0]
        results.update({name:[gogobatcher.getAnimeLink(f'{results[e.control.tooltip][0]}-{episodesNumber}')]})
        # Updates the page
        page.update()

    # Function to places the results
    def placeResults(resultKeys,t):
            if t == 'm':
                searchquery = searchMangaField.value
                searchquery = searchquery.capitalize()
                func = selectMangaResult
                text = f"Search : {searchquery}"
                imgI = 1
            elif t == 'a':
                searchquery = searchField.value
                searchquery = searchquery.capitalize()
                func = selectResult
                text = f"Search : {searchquery}"
                imgI = 1
            else:
                func = selectHomePageResult
                text = 'NeoBatcher \t\t\t\t\t\t\t V3.8' 
                imgI = 2
            # Sets variables as global
            global resultsPage

            # List of results
            resultsPage.controls.clear()
            resultsPage.controls.append(
                ft.Row(
                    controls= [
                        ft.Text(
                            value=text,
                            weight= ft.FontWeight.BOLD,
                            size = 23,
                        )
                ],alignment=ft.MainAxisAlignment.SPACE_EVENLY
                )
            )
            if resultKeys:
                itemCount = int(page.window_width // 160)
                print(page.window_width,itemCount)
                if itemCount == 0: itemCount =1
                colCount = ceil(len(results)/itemCount)
                i = 0
                values = list(resultKeys)
                for _ in range(colCount):
                    r = ft.Row(controls=[],alignment=ft.MainAxisAlignment.SPACE_BETWEEN)
                    for k in range(itemCount):
                        if i < len(values):

                            r.controls.append(
                                ResultWindow(
                                    src=results[values[i]][imgI],
                                    name=f"{values[i]}",
                                    text=f"{values[i]}",
                                    textSize=12,    
                                    imHigh=226,
                                    imWid=160,
                                    width=160,
                                    on_click=func
                                )
                            )
                            i+=1
                    resultsPage.controls.append(r)
            global currentPage
            if currentPage:
                # Cleans the page
                currentPage.controls.remove(ring)
                page.remove(currentPage)
                # Adds the results page
            page.add(resultsPage)
            currentPage = resultsPage

        
    # Text field for the new domain
    newDomainField = ft.TextField(
        label = "New domain",
        value = data['Domain'],
        icon=ft.icons.WEB
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
        value=data["Email"],
        icon=ft.icons.MAIL
    )
    # Password field with the loaded value from the data file
    passwordPField = ft.TextField(
        label="Password",
        value=data["Password"],
        can_reveal_password = True,
        password = True,
        icon=ft.icons.LOCK
    )
    # Directory field with the loaded value from the data file
    defaultDirectory = ft.TextField(
        label="Download Directory",
        value=data["Directory"],
        icon = ft.icons.TV
    )   
    cvlcPathFeild = ft.TextField(
        label="CVLC path, Windows only",
        value=data["Player"],
        icon = ft.icons.VIDEO_FILE
    )  
    defaultMangaDirectory = ft.TextField(
        label="Manga Directory",
        value=data["Manga_Directory"],
        icon = ft.icons.BOOK
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
            data["Domain"] = newDomainField.value
            gogobatcher.domain = newDomainField.value
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
            
            gogobatcher.email = emailField.value
            gogobatcher.password = passwordField.value
            gogobatcher.path = defaultDirectory.value
            mangadex.path = defaultMangaDirectory.value
            # Cleans the page
            global currentPage
            page.remove(currentPage)
            # Sets the page theme to the mode from the dropdown menu
            page.theme_mode = modeDropDown.value
            colorCode = ""
            global cvlcPath
            cvlcPath = cvlcPathFeild.value
            # If the color theme prefernces is random
            if radioGP.value == "Random":
                randomColorCode = mangadex.generate_hex_color_code()
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
            currentPage = mainPage
    
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
                    ),
                    # Container with the dropdown menu
                    ft.Container(
                        content = modeDropDown,
                    )
                ],
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN
            ),
            # Email and password fields we created earlier
            emailPField,passwordPField,newDomainField,
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


    # Function to load the home page
    def loadHomePage(e):
        global results
        try: currentPage.controls.append(ring)
        except:pass
        page.update()
        # Gets the results from the "getHomePage" function
        results = gogobatcher.getHomePage()
        # Places the results
        placeResults(results.keys(),'h')

    # Function that loads the preferences page
    def loadMenu(e):
        # Cleans the page
        global currentPage
        page.remove(currentPage)
        global newColorCode
        newColorCode = data["Color"]
        # Adds the preferences page
        page.add(preferencesPage)
        currentPage = preferencesPage

    # Button to load settings page
    settingsButton = ft.ElevatedButton(text="Settings", on_click=loadMenu)
    def loadManga(e):
        global currentPage
        page.remove(currentPage)
        page.add(mangaSearchPage)
        currentPage = mangaSearchPage
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
                ],
            # Row allignment is centre
            alignment= ft.MainAxisAlignment.CENTER
            ),
            # Container with the version number
            ft.Container(
                # Text of size 12
                content = ft.Text(
                    value="V3.8",
                    size = 12
                ),
                # Container padding of size 30
                padding = 30
            ),
        ],
        # Main page horizontal alignment is centre
        horizontal_alignment= ft.CrossAxisAlignment.CENTER
    )
    def changeToolBar(e):
        global currentPage
        i = e.control.selected_index
        if i == 0:
            page.remove(currentPage)
            page.add(downloadPage)
            currentPage = downloadPage
            page.update()
        if i == 1: 
            loadManga(e)
        if i == 2:
            page.remove(currentPage)
            page.add(mainPage)
            currentPage = mainPage
        if i == 3: 
            loadSearchPage(e)
        if i == 4:
            loadMenu(e)
    toolbar.toolbar.on_change = changeToolBar
    # If the email or password aren't useable 
    if len(data["Email"]) < 1 or len(data["Password"]) < 1:
        # Adds the login page
        page.add(toolbar.toolbar)
        page.add(loginScreen)
        currentPage = loginScreen
    else:
        # page.add(mainPage)

        page.add(toolbar.toolbar)
        loadHomePage('as')

# If the app is ran as a file not as a library
if __name__ == "__main__":
    # We run the flet app with the target as the main function
    ft.app(target=main)
    
