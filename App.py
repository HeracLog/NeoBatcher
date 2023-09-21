import random
import string
import time
import requests
from bs4 import BeautifulSoup as bs
import os
import flet as ft
import json 
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# Function to change domain name
# Search function
def search(search : str) -> str | dict:
    link : str = f"https://gogoanimehd.io/search.html?keyword={search.replace(' ','%20')}"

    # Creates a new session
    session : requests.Session = requests.session()
    # Gets the page's source
    htnlData = session.get(link).text
    # Parses the data
    soupedData = bs(htnlData, "lxml")
    # Gets the search results container
    container = soupedData.find("ul",{"class": "items"})

    # Creates an empty dicitionary and an index variable
    shows : dict = {}
    i : int = 0
    # Loops through all results
    for show in container.find_all("li"):
        # Gets the p tag containing the name and link
        paragraph = show.find("p", {"class":"name"})
        # Gets the a tag within it
        aTag = paragraph.find("a")
        # Gets showname and link
        showName : str = aTag.getText()
        showLink : str = aTag.get("href")
        # Updates the dicitionary and increments i
        shows.update({showName:showLink})
        i+=1
    return shows        

# Function to get the number of episodes
def getNumberOfEpisodes(link : str) -> int:
    # Creates link to get data
    link = f"https://gogoanimehd.io{link}"
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
def removeExtraParts(link:str) -> str:
    for i in range(len(link)-1,0,-1):
        if link[i].isdigit() or link[i] == "-":
            link = link[0:i]
        else:
            break
    return link

# Function to make link to be used in getting episodes links
def makeLink(linkCate : str) -> str:
    # Makes the link
    link : str =f"https://gogoanimehd.io{linkCate}"
    chromeOptions = Options()
    chromeOptions.add_argument("--headless")
    driver = webdriver.Firefox(options=chromeOptions)
    driver.get(link)
    WebDriverWait(driver,10).until(
        EC.presence_of_element_located((By.ID,"episode_related"))
    )
    htmlData = driver.page_source
    # Parses the html data
    soupedData = bs(htmlData,"lxml")
    # Finds the episodes container
    container = soupedData.find("ul",{"id":"episode_related"})
    # Gets any episode tag
    li = container.find("li")
    # Gets any episode link
    aTag = li.find("a")
    driver.quit()
    # Returns link in proper format
    return removeExtraParts(f"https://gogoanimehd.io{aTag.get('href')[:-2][1:]}")

# This function logs in and fetches each download link indiviually
def LoginAndGoToLink(eps,LinkofPath,quality,email,password):
    # Array of links to be downloaded
    Links = []
    # Login page link
    
    linkLogin = "https://gogoanimehd.io/login.html"

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
    for ep in eps:
        # Episode link can be changed
        link = f"{format(LinkofPath)}-{ep}"
        
        # Gets html data of the episode page
        html_page= s.get(link).text
        # Sorts html data
        soup = bs(html_page, "lxml")
        sizeBefore : int = len(Links)
        # Finds download links
        for link in soup.find_all("a"):
            # You can set the resloution from '360, 480, 720, 1080'
            if quality in format(link.text):
                x = link.get("href")
                Links.append(x) 
        if sizeBefore == len(Links):
            print(f"Couldn't get episode {ep} at quality {quality}")
            Links.append("")
    # Returns Links array to other functions
    return Links

def generate_hex_color_code():
    # Generate a random 6-digit hex number
    hex_num = ''.join(random.choices(string.hexdigits, k=6))
    # Prepend '#' to the hex number to get a valid color code
    color_code = '#' + hex_num
    return color_code

def getNewQuality(tried : list) -> str:
    for quality in ["360","480","720","1080"]:
        if quality not in tried:
            return quality
    return None


results = {}
episodesNumber = 0
resultsList = []
resultsPage = ft.Column(
    controls= resultsList
)

def loadData() -> dict:
    jsonData = open("./preferences.json","r")
    dataDict = json.load(jsonData)
    return dataDict
link = ""
linkRaw = ""
name = ""
data = loadData()
defaultMode = data["Mode"]
domain : str = data["Domain"]
def main(page : ft.Page):
    emailField = ft.TextField(
        label="Email"
    )
    passwordField = ft.TextField(
        label="Password"
    )
    def login(e):
        if emailField.value and passwordField.value:
            data["Email"] = emailField.value
            data["Password"] = passwordField.value
            with open("./preferences.json",'w') as f:
                json.dump(data,f,indent=4)
            page.clean()
            page.add(mainPage)
    loginScreen = ft.Column(
        controls=[
            ft.Container(
                content=ft.Text(
                value="GogoBatcherDio",
                weight= ft.FontWeight.BOLD,
                size= 32,
                ),
                alignment=ft.alignment.center
            )
            ,
            emailField,passwordField,
            ft.ElevatedButton(text="Login",on_click=login)
        ]
    )
    # Setting up screen size
    colorCode = ""
    if data["Color"] == "random":
        colorCode = generate_hex_color_code()
    else:
        colorCode = data["Color"]
    page.theme_mode = defaultMode
    page.theme = ft.Theme(
        color_scheme=ft.ColorScheme(
            primary= colorCode
        ))
    page.window_width = 400
    page.window_height = 400
    page.scroll = ft.ScrollMode.AUTO
    page.window_resizeable = False
    page.title = "GogoBatcherDio"
    # Setting up allignment
    page.vertical_alignment=ft.MainAxisAlignment.CENTER,
    page.horizontal_alignment=ft.CrossAxisAlignment.CENTER
    

    searchField = ft.TextField(
        label= "Enter anime name"
    )
    epFromField = ft.TextField(
        label = "Start from episode",
        width = 120
    )
    epNumField = ft.TextField(
        label = "How many episodes",
        width = 120
    )
    quaityDropDown = ft.Dropdown(
        width=120,
        options=[
            ft.dropdown.Option("360"),
            ft.dropdown.Option("480"),
            ft.dropdown.Option("720"),
            ft.dropdown.Option("1080")
        ],
        hint_text="Quality"
    )
    def changeDomain(newDomain : str) -> None:
        # Reads script from within itself
        data["Domain"] = newDomain
        with open("./preferences.json","w") as f:
            json.dump(data,f,indent=4)
        
    def loadSearchPage(e):
        page.clean()
        page.add(searchPage)

    def loadMainPage(e):
        page.clean()
        page.add(mainPage)

    def tempSearch(e):
        if searchField.value:
            # page.add(ft.Text(f"{searchField.value}"))
            global results
            results = search(searchField.value)
            placeResults(results.keys())
    def back(e):
        page.clean()
        page.add(resultsPage)

    def mainMenu(e):
        page.clean()
        page.add(mainPage)
    def DownloadTheFilesFlet(Links,path,startEp,mainLink,quality,email,password):
        pageColumn = ft.Column(
            controls = []
        )
        page.add(pageColumn)
        page.add(
            ft.Row(

                controls=[
                    ft.ElevatedButton(text = "Back",on_click=back,width=120),
                    ft.ElevatedButton(text = "Main menu",on_click=mainMenu,width=120),
                ]
            )
        )
        name = startEp
        for link in Links:
            workingQuality : str = quality
            tried : list = []
            max_attempts = 3
            for attempt in range(max_attempts+1):
                # Get the file in chunks
                response = requests.get(link, stream=True)
                if response.status_code == 200:
                    # Calculate size in Bytes
                    total_size_in_bytes = int(response.headers.get('content-length', 0))
                    # Block size of progress bar
                    block_size = 1024  # 1 Kibibyte
                    # Actual progress bar
                    progress_bar = ft.ProgressBar(
                        width=400,
                        color= generate_hex_color_code()
                    )
                    totalGotten = 0
                    textF = ft.Text(f"{round(totalGotten/(1024*1024),2)} / {round(total_size_in_bytes/(1024*1024),2)} MBs")
                    pageColumn.controls.append(
                        ft.Text(f"EP{name}"))
                    pageColumn.controls.append(
                        ft.Column([textF, progress_bar]))
                    
                    # Opens file in binary write mode
                    with open(f"{path}/EP{name}.mp4", "wb") as file:
                        # Loops through response as it write it in chunks
                        for data in response.iter_content(block_size):
                            totalGotten += len(data)
                            # Updates progress bar
                            progress_bar.value = totalGotten/total_size_in_bytes
                            # Writes data
                            file.write(data)
                            textF.value = f"{round(totalGotten/(1024*1024),2)} / {round(total_size_in_bytes/(1024*1024),2)} MBs"
                            page.update()
                    break
                else:
                    tried.append(workingQuality)
                    workingQuality = getNewQuality(tried)
                    if workingQuality != None:
                        link = LoginAndGoToLink(list(range(name,name+1)),mainLink,workingQuality,email,password)[0]
                        print("Attempt failed, retrying....")
                        time.sleep(3)
                    else:
                        print("Unable to get this episode")
            # Increments name
            name+=1

        
    searchPage = ft.Column(
        controls=[
            ft.Text(
                value= "Search for anime",
                weight=ft.FontWeight.BOLD,
                size = 23
            ),
            searchField,
            ft.Row(
                controls=
                [
                    ft.Container(
                        content = ft.ElevatedButton(text = "Search",on_click=tempSearch),
                        alignment= ft.alignment.top_left
                    ),
                    ft.Container(
                        visible=True,
                        width =190
                    ),
                    ft.Container(
                        content = ft.ElevatedButton(text = "Back", on_click=loadMainPage),
                        alignment= ft.alignment.top_right,
                    )
                ],
                width = 400,
            ),
            
        ]
    )

    def download(e):
        print(epFromField.value)
        print(epNumField.value)
        print(quaityDropDown.value)
        page.add(ft.Text("Fetching videos......"))
        eps = list(range(int(epFromField.value),int(epFromField.value)+int(epNumField.value)))
        videosLinks = LoginAndGoToLink(eps,link,quaityDropDown.value,data["Email"],data["Password"])
        page.clean()
        page.add(
            ft.Text(value = name, weight=ft.FontWeight.BOLD)
        )
        path = f"{data['Directory']}{linkRaw.split('/')[-1]}"
        try:
            os.mkdir(path)
        except:
            ...
        DownloadTheFilesFlet(videosLinks,path,int(epFromField.value),link,quaityDropDown.value,data["Email"],data["Password"])
    def selectResult(e : ft.ControlEvent):
        print(e.control.text, "selected")
        

        global episodesNumber
        episodesNumber = getNumberOfEpisodes(results[e.control.text])
        global linkRaw
        linkRaw = results[e.control.text]
        global name
        name = e.control.text
        downloadButton = ft.ElevatedButton(text = "Download",on_click=download,width=120)
        resultPage = ft.Column(
        controls=[
            ft.Text(e.control.text),
            ft.Text(f"{episodesNumber} episodes"),
            ft.Container(
                height=13
            ),
            ft.Row(
                controls=[
                    epFromField,epNumField,quaityDropDown
                ],
                width = 400
            ),
            ft.Row(

                controls=[
                    downloadButton,
                    ft.ElevatedButton(text = "Back",on_click=back,width=120),
                    ft.ElevatedButton(text = "Main menu",on_click=mainMenu,width=120),
                ]
            )
        ]
        )
        page.clean()
        downloadButton.disabled = True
        page.add(resultPage)
        page.add(ft.Text("Making link....."))
        global link
        link = makeLink(results[e.control.text])
        downloadButton.disabled = False
        downloadButton.update()
        resultPage.update()
        page.update()
        print("Got link")
        page.remove_at(-1)

    def placeResults(results):
        global resultsList
        global resultsPage

        resultsList = []
        resultsPage = ft.Column(
        controls= resultsList
        )
        i = 1
        for result in results:
            if i == 1:
                resultsRow = []
                thisrow = ft.Row(
                    controls=resultsRow
                )
            resultsRow.append(ft.ElevatedButton(
                text=f"{result}",
                width=119,
                height=119,
                on_click= selectResult
                ))
            i += 1
            if i == 4:
                resultsList.append(thisrow)
                i = 1
        if i != 1:
            resultsList.append(thisrow)
        page.clean()
        page.add(resultsPage)

    newDomainField = ft.TextField(
        label = "New domain"
    )
    def changeDomainPressed(e):
        if newDomainField.value:
            changeDomain(newDomainField.value)
            global domain
            domain = newDomainField.value
    oldDomainText = ft.Text(
                value = f"Old domain: {domain}"
            )
    changeDomainPage = ft.Column(
        controls=[
            ft.Text(
                value = "Change Domain"
                ,size=18
                ,weight=ft.FontWeight.BOLD
            ),oldDomainText
            ,
            newDomainField,
            ft.Row(
                controls=[
                    ft.ElevatedButton(text="Change", on_click=changeDomainPressed),
                    ft.ElevatedButton(text="Back", on_click=mainMenu),
                ]
            )
        ]
    )
    modeDropDown = ft.Dropdown(
        options=[
            ft.dropdown.Option("Dark"),
            ft.dropdown.Option("Light")
        ],
        hint_text= data["Mode"],
        value=data["Mode"]
    )
    emailPField = ft.TextField(
        label="Email",
        value=data["Email"]
    )
    passwordPField = ft.TextField(
        label="Password",
        value=data["Password"]
    )
    defaultDirectory = ft.TextField(
        label="Download Directory",
        value=data["Directory"]
    )
    colorTheme = ft.TextField(
        label="Color code",
        value=data["Color"]
    )
    
    def savePreferences(e):
        if emailPField.value and passwordPField.value and defaultDirectory.value and colorTheme.value:
            data["Email"] = emailPField.value
            data["Password"] = passwordPField.value
            data["Directory"] = defaultDirectory.value
            data["Mode"] = modeDropDown.value
            data["Color"] = colorTheme.value
            with open("./preferences.json",'w') as f:
                json.dump(data,f,indent=4)
            page.clean()
            page.theme_mode = modeDropDown.value
            colorCode = ""
            if data["Color"] == "random":
                colorCode = generate_hex_color_code()
            else:
                colorCode = data["Color"]
            page.theme = ft.Theme(
                color_scheme=ft.ColorScheme(
                    primary= colorCode
                ))
            page.update()
            page.add(mainPage)

    preferencesPage = ft.Column(
        controls=[
            ft.Row(
                controls=[
                    ft.Container(
                        content=ft.Text(
                            "Mode"
                        ),
                        width = 220
                    ),
                    ft.Container(
                        content = modeDropDown,
                        width = 150
                    )
                ]
            ),
            emailPField,passwordPField,
            ft.Text("Directory name must end with a slash /"),defaultDirectory,
            ft.Text("Put a color code or the word \"random\""),colorTheme,
            ft.Container(
                content = ft.ElevatedButton(text="Save",on_click=savePreferences),
                alignment=ft.alignment.center
            )
        ]
    )
    def loadChangeDomainPage(e):
        page.clean()
        page.add(changeDomainPage)
        oldDomainText.value = f"Old domain: {domain}"
        changeDomainPage.update()

    def loadMenu(e):
        page.clean()
        page.add(preferencesPage)

    modeToggle = ft.ElevatedButton(text="Settings", on_click=loadMenu)
    mainPage = ft.Column(
    controls= [
        ft.Container(
            content=ft.Text(
                value = "GogoBatcherDio"
                ,size=32
                ,weight=ft.FontWeight.BOLD),
            padding= 45
            ),
        
        ft.ElevatedButton(text="Download Anime", on_click=loadSearchPage),
        ft.ElevatedButton(text="Change Domain", on_click=loadChangeDomainPage),
        modeToggle,
        ft.Container(
            content = ft.Text(
                value="V3.0",
                size = 12
            ),
            padding = 30
        )
    ],
    horizontal_alignment= ft.CrossAxisAlignment.CENTER
    )
    
    if len(data["Email"]) < 1 or len(data["Password"]) < 1:
        page.add(loginScreen)
    else:
        page.add(mainPage)

if __name__ == "__main__":
    ft.app(target=main)

