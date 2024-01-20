import random
import string
import requests
import json
from PIL import Image
from pypdf import PdfMerger
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from io import BytesIO
import os
import flet as ft

class MangaDex:
    def __init__(self,path:str) -> None:
        self.path = path
        self.session = requests.session()

    # Function that searches for managa
    def searchForManga(self,query : str) -> dict:
        link = f'https://api.mangadex.org/manga?title={query}&limit=25&contentRating[]=safe&includes[]=cover_art&order[relevance]=desc'
        data = self.session.get(link).content.decode("utf-8")
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
    
    def getAbout(self,mangaID : str) :
        link = f"https://api.mangadex.org/manga/{mangaID}?includes[]=artist&includes[]=author&includes[]=cover_art"
        data = self.session.get(link).content.decode('utf-8')
        data = json.loads(data)
        attributes = data['data']['attributes']
        description = attributes['description']
        return description['en']
    
    def getChapters(self,managaID : str) -> dict:
        startAmmount = 200
        link : str = f"https://api.mangadex.org/manga/{managaID}/feed?limit=200&includes[]=scanlation_group&includes[]=user&order[volume]=asc&order[chapter]=asc&offset=0&contentRating[]=safe&contentRating[]=suggestive&contentRating[]=erotica&contentRating[]=pornographic"
        data = self.session.get(link).content.decode('utf-8')
        data = json.loads(data)
        allData = list()
        allData.extend(data['data'])
        total = data["total"]
        chapterData : dict = {}
        if total > startAmmount:
            while total > startAmmount:
                newLink = f"https://api.mangadex.org/manga/{managaID}/feed?limit={200}&includes[]=scanlation_group&includes[]=user&order[volume]=asc&order[chapter]=asc&offset={startAmmount}&contentRating[]=safe&contentRating[]=suggestive&contentRating[]=erotica&contentRating[]=pornographic"
                newData = self.session.get(newLink).content.decode('utf-8')
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
    
    def getPageNumber(self,pageHash : str) -> int:
        return "".join(i for i in pageHash.split("-")[0] if i.isnumeric())


    # Function to generate random color codes
    def generate_hex_color_code(self):
        # Generate a random 6-digit hex number
        hex_num = ''.join(random.choices(string.hexdigits, k=6))
        # Prepend '#' to the hex number to get a valid color code
        color_code = '#' + hex_num
        return color_code

    def getPages(self,chapterID : str,mangaName : str, chapterNumber : str,name:str ,cont,page,view = False): 
        link = f"https://api.mangadex.org/at-home/server/{chapterID}?forcePort443=false"
        data = self.session.get(link).content.decode('utf-8')
        data = json.loads(data)
        chapterData = data["chapter"]
        chapterHash = chapterData["hash"]
        imgs = chapterData["data"]
        baseUrl = "https://uploads.mangadex.org/data"
        try:
            os.mkdir(f"{self.path}{name}/{name}-{chapterNumber}")
        except:
            print("Directory exists")
        if not view:
            progress_bar = ft.ProgressBar(
                width=600,
                color= self.generate_hex_color_code()
            )
            labelText = ft.Text(f"Saving chapter {chapterNumber}:     0/{len(imgs)}")
            cont.controls.append(labelText)
            cont.controls.append(progress_bar)
            page.update()
        res = []
        for img in imgs:
            i = imgs.index(img)
            imgurl = f"{baseUrl}/{chapterHash}/{img}"
            pageNumber = self.getPageNumber(img)
            res.append(imgurl)
            if not view :
                response = self.session.get(imgurl)

                if response.status_code == 200:
                    image_content = BytesIO(response.content)
                    image = Image.open(image_content)
                    image = image.convert('RGB')
                    image.save(f"{self.path}{mangaName}/{mangaName}-{chapterNumber}/{pageNumber}.jpg")
                    progress_bar.value = (i+1)/len(imgs)
                    labelText.value = f"Saving chapter {chapterNumber}:     {i+1}/{len(imgs)}"
                    page.update()
                else:
                    print(f"Couldn't get page {pageNumber}")
        return res
    # Function that makes pdfs of the manga chapter 
    def pdfize(self,_dir,name,chapter,cont,page:ft.Page):
            # Alert of pdfing the chapter initialization
            print(f"Started pdfiziing chapter {chapter}")
            # Selects all image files in a directory acoording to certain parameters
            image_files = [f for f in os.listdir(_dir) if f.endswith('.jpg') or f.endswith('.jpeg') or f.endswith('.png')]

            # Creates a pdf canvas of letter size and name of the manga and its chapter
            pdf = canvas.Canvas(f'{_dir}/{name}-{chapter}.pdf', pagesize=letter)
            progress_bar = ft.ProgressBar(
                width=600,
                color= self.generate_hex_color_code()
                )
            labelText = ft.Text(f"Pdfizing chapter {chapter}:     0/{len(image_files)}")
            cont.controls.append(labelText)
            cont.controls.append(progress_bar)
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
    def mergePDFS(self,direc,name,cont,page : ft.Page):
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
            color= self.generate_hex_color_code()
        )
        labelText = ft.Text(value=f"Merging all PDFs....     0/{len(pdfFiles)}")
        cont.controls.append(labelText)
        cont.controls.append(progressBar)
        page.update()
        # Loops through all files append them while displaying the progress in a progress bar
        for i in range(len(pdfFiles)):
            file = pdfFiles[i]
            merger.append(file)
            labelText.value = f"Merging all PDFs....     {i+1}/{len(pdfFiles)}"
            progressBar.value = (i+1)/len(pdfFiles)
            page.update()
        # Creates the file and closes the megrger object
        merger.write(f"{direc}{name}.pdf")
        merger.close()
