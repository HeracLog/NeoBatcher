import random
import string
import time
import requests
from bs4 import BeautifulSoup as bs
import os
import datetime
from tqdm import tqdm

# Fucntion that prints search results
def displaySeachResults(results : dict) -> None:
    # Loops through keys and values in the dictionary
    for id,result in results.items():
        # Prints ID and Name
        print(f"The ID is {id}")
        print(f"The name is {result['Name']}")
        print("\n")

# Search function
def search() -> str:
    # Loops until valid inputt is given
    while True:
        try:
            search : str = input("Enter the anime you want to search for: ")
            break
        except:
            print("Invlaid input, try again")

    # Creates search link 
    link : str = f"https://gogoanimehd.to/search.html?keyword={search.replace(' ','%20')}"

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
        shows.update({i: {"Name" : showName,"Link" :showLink}})
        i+=1
    # Displays search results
    displaySeachResults(shows)
    # Loops until a valid id is given
    while True:
        try:
            showID : int = int(input("Enter ID of the correct result: "))
            break
        except:
            print("Invalid, try again") 
    # Returns the link
    return shows[showID]["Link"]

# Function to get the number of episodes
def getNumberOfEpisodes(link : str) -> int:
    # Creates link to get data
    link = f"https://gogoanimehd.to{link}"
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

# Function to make link to be used in getting episodes links
def makeLink(linkCate : str) -> str:
    # Gets the last part of the domain
    name : str = linkCate.split("/")[-1]
    # Returns the link
    return f"https://gogoanimehd.to/{name}-episode"
    
# Starting function
# Where all the magic happens
def start():
    # Gets the name from the user search
    name : str = search()
    # Gets the link
    link : str = makeLink(name)
    # Gets the number of episodes
    numOfEpisodes : int = getNumberOfEpisodes(name)
    print(f"There are {numOfEpisodes} episodes")
    # Defines Number of Episodes
    try:
        startEp = int(input("Start from episode?: "))
        numOfEps= int(input("How many episodes?: "))
    except:
        # Default values (1,1)
        print("Error occured, defaulted values to (1,1)")
        startEp = 1
        numOfEps = 1
    # Range of startEp to startEp and numOfEps exclusive
    eps = list(range(startEp,startEp+numOfEps))
    # Prompts the user to enter quality
    try:
        quality = input("Enter quality 360,480,720: ")
    except:
        # In case of exception we default it at 480
        print("Defaulted at quality 480")
        quality = 480
    # Make the folder for the videos
    try:
        os.mkdir(f"./{name.split('/')[-1]}")
    except:
        print("Directory exists")
    email = input("Enter your email: ")
    # Takes password input
    password = input("Enter your password: ")

    name = f"./{name.split('/')[-1]}"
    DownloadTheFiles(LoginAndGoToLink(eps,email,password,link,quality),name,startEp,link,quality)
    
# This function logs in and fetches each download link indiviually
def LoginAndGoToLink(eps,email,password,LinkofPath,quality):
    # Array of links to be downloaded
    Links = []
    # Login page link
    
    linkLogin = "https://gogoanimehd.to/login.html"

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

        # Finds download links
        for link in soup.find_all("a"):
            # You can set the resloution from '360, 480, 720, 1080'
            if quality in format(link.text):
                x = link.get("href")
                Links.append(x) 
    # Returns Links array to other functions
    return Links

def generate_hex_color_code():
    # Generate a random 6-digit hex number
    hex_num = ''.join(random.choices(string.hexdigits, k=6))
    # Prepend '#' to the hex number to get a valid color code
    color_code = '#' + hex_num
    return color_code

# Used to download the file and is multiplatform
def DownloadTheFiles(Links,path,startEp,mainLink,quality):
    name = startEp
    for link in Links:
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
                progress_bar = tqdm(total=total_size_in_bytes, unit='KB', unit_scale=True,colour=generate_hex_color_code(),desc=f"EP{name}.mp4 ")
                # Opens file in binary write mode
                with open(f"{path}/EP{name}.mp4", "wb") as file:
                    # Loops through response as it write it in chunks
                    for data in response.iter_content(block_size):
                        # Updates progress bar
                        progress_bar.update(len(data))
                        # Writes data
                        file.write(data)
                # Closes progress bar to avoid memory leaks
                progress_bar.close()
                break
            else:
                # If the second attempt fails we download it in another quality
                if attempt == 2:
                    if quality == "360":
                        otherQuality = "480"
                    else:
                        otherQuality = "360"
                    link = LoginAndGoToLink(list(range(name,name+1)),mainLink,otherQuality)[0]
                print("Attempt failed, retrying....")
                time.sleep(3)
        # Increments name
        name+=1

# WGetTheFiles(LoginAndGoToLink(eps,link),name)
if __name__ == '__main__':
    start()
# ENJOY
