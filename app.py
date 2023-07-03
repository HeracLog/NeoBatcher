import random
import string
import requests
from bs4 import BeautifulSoup as bs
import os
from tqdm import tqdm

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
# Takes link input
print("Example : https://gogoanime.hu//k-on-2-episode")
try:
    link = input("Enter the link: ")
    name = input("Enter anime name: ")
    try:
        os.mkdir(f"./{name}")
    except:
        print("Directory exists")
    name = f"./{name}"
except:
    # Default value
    print("Error occured, link is now default value.")
    link = "https://gogoanime.hu//k-on-2-episode"
    name = "Generic"
# Takes email input
email = input("Enter your email: ")
# Takes password input
password = input("Enter your password: ")

# This function logs in and fetches each download link indiviually
def LoginAndGoToLink(eps,Email,Password,LinkofPath):
    # Array of links to be downloaded
    Links = []
    # Login page link
    
    linkLogin = "https://gogoanime.hu/login.html"

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
    login_data = dict(email=Email, password=Password, _csrf=csrftoken, next='/')

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
            if "480" in format(link.text):
                x = link.get("href")
                Links.append(x) 
    # Returns Links array to other functions
    return Links

# Not used anymore
# Downloading function, takes Links array as a parameter
def WGetTheFiles(Links):
    name = startEp
    for Link in Links:
        # Downloads each file
        os.system(f"wget -O EP{name}.mp4 {Link}")
        name+=1
# Generates random color code for progress bar
def generate_hex_color_code():
    # Generate a random 6-digit hex number
    hex_num = ''.join(random.choices(string.hexdigits, k=6))
    # Prepend '#' to the hex number to get a valid color code
    color_code = '#' + hex_num
    return color_code

# Used to download the file and is multiplatform
def DownloadTheFiles(Links,path):
    name = startEp
    for link in Links:
        # Get the file in chunks
        response = requests.get(link, stream=True)
        # Calculate size in Bytes
        total_size_in_bytes = int(response.headers.get('content-length', 0))
        # Block size of progress bar
        block_size = 1024  # 1 Kibibyte
        # Actual progress bar
        progress_bar = tqdm(total=total_size_in_bytes, unit='iB', unit_scale=True,colour=generate_hex_color_code(),desc=f"EP{name}.mp4 ")
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
        # Increments name
        name+=1

# WGetTheFiles(LoginAndGoToLink(eps,link),name)
DownloadTheFiles(LoginAndGoToLink(eps,email,password,link),name)


# ENJOY
