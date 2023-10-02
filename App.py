import random
import string
import time
import requests
from bs4 import BeautifulSoup as bs, Tag
import os
import flet as ft
import json 
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

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
# Finds theme for the app
defaultMode = data["Mode"]
# Loads the domain from the file
domain : str = data["Domain"]

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
    container = soupedData.find("ul",{"class": "items"})

    # Creates an empty dicitionary and an index variable
    shows : dict = {}
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

# Function that fetches homepage
def getHomePage() -> dict:
    # Link is simply just the domain
    link : str = f"https://{domain}"
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
    return removeExtraParts(f"https://{domain}{aTag.get('href')[:-2][1:]}")

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
    for quality in ["360","480","720","1080"]:
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
        label="Password"
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
                value="GogoBatcherDio",
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
        colorCode = generate_hex_color_code()
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
    page.window_width = 400
    page.window_height = 400
    page.window_resizeable = False
    # Sets scroll mode to auto
    # Meaning if there is something on page that is beyond bounds it enables the scrolling feature
    page.scroll = ft.ScrollMode.AUTO
    # Sets page title
    page.title = "GogoBatcherDio"
    # Setting up allignment
    page.vertical_alignment=ft.MainAxisAlignment.CENTER,
    page.horizontal_alignment=ft.CrossAxisAlignment.CENTER
    
    # Intializes fields to be used in download menu
    # Search field contains the anime to be searched for
    searchField = ft.TextField(
        label= "Enter anime name"
    )
    # Defines the episode we start from
    epFromField = ft.TextField(
        label = "Start from episode",
        width = 120
    )
    # Defines the episode we stop at
    epNumField = ft.TextField(
        label = "Till episode",
        width = 120
    )
    # Dropdown menu for download qualities
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
        # If the search field isn't empty
        if searchField.value:
            # Sets the results dict as global
            global results
            # Fetches the search results
            results = search(searchField.value)
            # Places all the buttons containing the anime names
            placeResults(results.keys())
            
    # Back button function
    def back(e):
        # Removes everything from the page
        page.clean()
        # Adds the result page
        page.add(resultsPage)

    # Function to load the main menu
    def mainMenu(e):
        # Removes everything from the page
        page.clean()
        # Adds the main menu
        page.add(mainPage)

    # Actual function to download the videos
    def DownloadTheFilesFlet(Links,path,startEp,mainLink,quality,email,password):
        # Creates a new column for the download page
        pageColumn = ft.Column(
            controls = []
        )
        # Adds the page column
        page.add(pageColumn)
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
                        width=400,
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
                        # Loops through response as it write it in chunks
                        for data in response.iter_content(block_size):
                            totalGotten += len(data)
                            # Updates progress bar
                            progress_bar.value = totalGotten/total_size_in_bytes
                            # Writes data
                            file.write(data)
                            # Updates the download text
                            textF.value = f"{round(totalGotten/(1024*1024),2)} / {round(total_size_in_bytes/(1024*1024),2)} MBs"
                            # Updates the whole page
                            page.update()
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

        
    # Search page column
    searchPage = ft.Column(
        controls=[
            # Bold text of size 23
            ft.Text(
                value= "Search for anime",
                weight=ft.FontWeight.BOLD,
                size = 23
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
                        width =190
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
                width = 400,
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
        page.add(
            ft.Text(value = name, weight=ft.FontWeight.BOLD)
        )
        # Defines path of the anime directory, the name will be derived from the link
        path = f"{data['Directory']}{linkRaw.split('/')[-1]}"
        try:
            # Tries to create the folder
            os.mkdir(path)
        except:
            ...
        # Downloads the episodes
        DownloadTheFilesFlet(videosLinks,path,int(epFromField.value),link,quaityDropDown.value,data["Email"],data["Password"])
    
    # Function that runs when you select a search result
    def selectResult(e : ft.ControlEvent):
        # Prints the anime name selected
        print(e.control.text, "selected")
        # Edits the variable episodesNumber as the number of episodes availabe for this anime
        global episodesNumber
        episodesNumber = getNumberOfEpisodes(results[e.control.text][0])
        # Edits the linkRaw variable to the link before formatting
        global linkRaw
        linkRaw = results[e.control.text][0]
        # Edits the name variable to the anime name
        global name
        name = e.control.text
        # Creates a download button with the click event as the "download" function 
        downloadButton = ft.ElevatedButton(text = "Download",on_click=download,width=120)
        # Creates a result page for the selected anime
        resultPage = ft.Column(
        controls=[
            # A text containing the anime name
            ft.Text(e.control.text),
            # A text containinf the latest episode number
            ft.Text(f"{episodesNumber} episodes"),
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
                width = 400
            ),
            # Another row containg other controls
            ft.Row(
                controls=[
                    # The download button we defined above
                    downloadButton,
                    # Back button and main menu button with functions "back" and "mainMenu" respectively
                    ft.ElevatedButton(text = "Back",on_click=back,width=120),
                    ft.ElevatedButton(text = "Main menu",on_click=mainMenu,width=120),
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
        episodesNumber = getNumeric(results[e.control.text][1])
        # Edits the linkRaw variable to the link before formatting
        global linkRaw
        linkRaw = formatHomePageLink(results[e.control.text][0])
        # Edits the name variable to the anime name
        global name
        name = e.control.text
        # Creates a download button with the click event as the "download" function 
        downloadButton = ft.ElevatedButton(text = "Download",on_click=download,width=120)
        # Creates a result page for the selected anime
        resultPage = ft.Column(
        controls=[
            # A text containing the anime name
            ft.Text(e.control.text),
            # A text containinf the latest episode number
            ft.Text(f"{episodesNumber} episodes"),
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
                width = 400
            ),
            # Another row containg other controls
            ft.Row(
                controls=[
                    # The download button we defined above
                    downloadButton,
                    # Back button and main menu button with functions "back" and "mainMenu" respectively
                    ft.ElevatedButton(text = "Back",on_click=back,width=120),
                    ft.ElevatedButton(text = "Main menu",on_click=mainMenu,width=120),
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
            if i == 3:
                # We append the row to the list
                resultsList.append(thisrow)
                # Returns the i to 1
                i = 1
        # At the end if i isn't 1 then there are results that aren't placed 
        if i != 1:
            # Adds the result list
            resultsList.append(thisrow)
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
                            )
                    ]),
                    width =  200
                ) 
            )
            # Increments the i
            i += 1
            # If i is 4
            if i == 3:
                # We append the row to the list
                resultsList.append(thisrow)
                # Returns the i to 1
                i = 1
        # At the end if i isn't 1 then there are results that aren't placed 
        if i != 1:
            # Adds the result list
            resultsList.append(thisrow)
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
        value=data["Mode"]
    )
    # Email field with the loaded value from the data file
    emailPField = ft.TextField(
        label="Email",
        value=data["Email"]
    )
    # Password field with the loaded value from the data file
    passwordPField = ft.TextField(
        label="Password",
        value=data["Password"]
    )
    # Directory field with the loaded value from the data file
    defaultDirectory = ft.TextField(
        label="Download Directory",
        value=data["Directory"]
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
            # Sets the data from the mode dropdown value
            data["Mode"] = modeDropDown.value
            # Sets the data from the color theme value
            data["Color"] = colorTheme.value
            # Saves the data to the json file
            with open("./preferences.json",'w') as f:
                json.dump(data,f,indent=4)
            
            # Cleans the page
            page.clean()
            # Sets the page theme to the mode from the dropdown menu
            page.theme_mode = modeDropDown.value
            colorCode = ""
            # If the color theme prefernces is random
            if data["Color"] == "random":
            # We generate a random color code for the theme
                colorCode = generate_hex_color_code()
            else:
                # Otherwise we use the one provided
                colorCode = data["Color"]
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
                        width = 220
                    ),
                    # Container with the dropdown menu
                    ft.Container(
                        content = modeDropDown,
                        width = 150
                    )
                ]
            ),
            # Email and password fields we created earlier
            emailPField,passwordPField,
            # Text acting as a tool tip and the default directory field we created earlier
            ft.Text("Directory name must end with a slash /"),defaultDirectory,
            # Text acting as a tool tip and the color theme field we created earlier
            ft.Text("Put a color code or the word \"random\""),colorTheme,
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
        # Adds the preferences page
        page.add(preferencesPage)

    # Button to load settings page
    settingsButton = ft.ElevatedButton(text="Settings", on_click=loadMenu)
    # Main page column
    mainPage = ft.Column(
        controls= [
            # Container with the title
            ft.Container(
                # Text with Bold weight and size of 32
                content=ft.Text(
                    value = "GogoBatcherDio"
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
            # A button that loads the change domain page with the "loadChangeDomainPage" function
            ft.ElevatedButton(text="Change Domain", on_click=loadChangeDomainPage),
            # Settings button
            settingsButton,
            # Container with the version number
            ft.Container(
                # Text of size 12
                content = ft.Text(
                    value="V3.1.1",
                    size = 12
                ),
                # Container padding of size 30
                padding = 30
            )
        ],
        # Main page horizontal alignment is centre
        horizontal_alignment= ft.CrossAxisAlignment.CENTER
    )
    
    # If the email or password aren't useable 
    if len(data["Email"]) < 1 or len(data["Password"]) < 1:
        # Adds the login page
        page.add(loginScreen)
    else:
        # Otherwise we add the main page
        page.add(mainPage)

# If the app is ran as a file not as a library
if __name__ == "__main__":
    # We run the flet app with the target as the main function
    ft.app(target=main)
