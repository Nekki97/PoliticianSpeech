import requests
import os
from pdfminer.pdfinterp import PDFResourceManager, PDFPageInterpreter
from pdfminer.converter import TextConverter
from pdfminer.layout import LAParams
from pdfminer.pdfpage import PDFPage
import pdfminer
from io import StringIO
from PyPDF2 import PdfFileReader, PdfFileWriter

Parteien = ("SPD", "CDU/CSU", "FDP", "DP", "FU", "BP", "KPD", "WAV", "FRAKTIONSLOS", "GB/BHE", "ZENTRUM", "DIE GRÜNEN", "BÜNDNIS 90/DIE GRÜNEN", "PDS", "DIE LINKE.", "DIE LINKE", "UNABHÄNGIG", "AFD", "GRÜNE")


def load_protocol(wahlperiode, sitzung, verbose):
    # Enter wahlperiode and sitzung to be downloaded AS STRINGS --> into protokolle folder as PDFs
    # Available Wahlperioden (start with 01) with Sitzungen (start with 001):
    # 01: 282
    # 02: 227
    # 03: 168
    # 04: 198
    # 05: 247
    # 06: 199
    # 07: 259
    # 08: 230
    # 09: 142
    # 10: 256
    # 11: 236
    # 12: 243
    # 13: 248
    # 14: 253
    # 15: 187
    # 16: 233
    # 17: 253
    # 18: 245
    # 19: 109
    id = wahlperiode + sitzung
    for root, dirnames, filenames in os.walk("D:/Pycharm_dir/MachineLearningTesting/protokolle"):
        for filename in filenames:
            if filename == id + ".pdf":
                print(id, "already downloaded")
                return
    url = 'http://dipbt.bundestag.de/doc/btp/' + wahlperiode + '/' + wahlperiode + sitzung + '.pdf'
    id = wahlperiode + sitzung
    myfile = requests.get(url)
    open(os.path.join("D:/Pycharm_dir/MachineLearningTesting/protokolle/", id + ".pdf"), 'wb').write(myfile.content)
    myfile.close()
    if verbose: print("Protokoll", id, "wurde heruntergeladen")


def crop_merge_pdf(id, verbose):
    for root, dirnames, filenames in os.walk("D:/Pycharm_dir/MachineLearningTesting/protokolle"):
        for filename in filenames:
            if filename == id + "-cropped.pdf":
                print(id, "already cropped")
                return
    pdffile = open("D:/Pycharm_dir/MachineLearningTesting/protokolle/"+id+".pdf", "rb")
    rightfilereader = PdfFileReader(pdffile, False)
    leftfilereader = PdfFileReader(pdffile, False)

    all_pages = PdfFileWriter()

    numPages = rightfilereader.getNumPages()
    if verbose: print(id, "has", numPages, "pages")

    counter = 0

    for i in range(numPages): # ca. 595 x 841

        left_page = leftfilereader.getPage(i)
        right_page = rightfilereader.getPage(i)

        left_page.cropBox.lowerLeft = (50, 50)
        left_page.cropBox.upperRight = (310, 775)

        right_page.cropBox.lowerLeft = (290, 50)
        right_page.cropBox.upperRight = (550, 775)

        all_pages.insertPage(left_page, counter)
        counter += 1
        all_pages.insertPage(right_page, counter)
        counter += 1

    all_pages_file = open("D:/Pycharm_dir/MachineLearningTesting/protokolle/" + id + "-cropped.pdf", "wb")
    all_pages.write(all_pages_file)
    all_pages_file.close()
    if verbose: print("Finished cropping and merging pages")


def convert_pdf_to_txt(id, verbose):
    pdffile = open("D:/Pycharm_dir/MachineLearningTesting/protokolle/" + id + "-cropped.pdf", 'rb')
    text = ""
    read_pdf = PdfFileReader(pdffile)
    numPages = read_pdf.numPages
    for i in range(numPages):
        page = read_pdf.getPage(i)
        text += page.extractText()

    textfile = open("D:/Pycharm_dir/MachineLearningTesting/protokolle/" + id + ".txt", "w", encoding="utf_16")
    textfile.write(text)
    textfile.close()

    if verbose: print("Finished converting", id, "to text")


def remove_brackets(id, verbose):
    textfile = open("D:/Pycharm_dir/MachineLearningTesting/protokolle/" + id + ".txt", "r")
    text = textfile.read()
    start = 0

    while text.find("(", start) > 0:

        index = text.find("(", start)
        index2 = text.find(")", start)

        if index > index2:  # e.g. "a)" überspringen
            start = index2 + 1
            continue

        if text[index+1:index2:].upper() in Parteien and (text[index2+2] == ":" or text[index2+1] == ":"): # If text between brackets = Party
            start = index2+1 # start after the bracket
            continue
        else:
            if verbose == 2: print(text[index + 1:index2:] + "\n") # print what is removed
            text = text[:index:] + text[index2+1::] # remove text between brackets

    textfile = open("D:/Pycharm_dir/MachineLearningTesting/protokolle/"+ id +"-nobrackets.txt", "w+")
    textfile.write(text)
    textfile.close()
    if verbose: print("Brackets removed")


def get_speech_indices(id, verbose): # get list of all speeches (start of name of speaker)
    # start of name: after single letter, number, period (without preceding "Dr")
    # or exclamation mark, whichever comes first
    textfile = open("D:/Pycharm_dir/MachineLearningTesting/protokolle/" + id + "-nobrackets.txt", "r")
    text = textfile.read()
    punctuation = [".", "!", "?"]
    start = 0
    indices = []
    while text.find("(", start) > 0:
        index = text.find("(", start)
        index2 = text.find(")", start)

        if index > index2:
            start = index2 + 1 # skip the "a)"
            continue

        #print(text[index-3:index+3:])
        #print(text[index2 - 3:index2 + 3:])

        for i in range(30):
            punc_index = 0
            dig_index = 0
            letter_index = 0
            if text[index-i] in punctuation and "Dr" not in text[index-3-i:index-i]:
                x = 2
                while text[index - i + x].isspace():
                    x += 1
                index = index - i + x  # start of name
                print("Punctuation found!")
                break
            if text[index-i].isdigit():
                x = 2
                while text[index - i + x].isspace():
                    x += 1
                index = index - i + x  # start of name
                print("Digit found!")
                break
            if text[index-i].isupper() and text[index-i-1].isspace() and text[index-i+1].isspace():
                x = 2
                while text[index - i + x].isspace():
                    x += 1
                index = index - i + x  # start of name
                print("Single Letter found!")
                break
        print(text[index:index2+1])
        indices.append(index)
        print("\n")
        start = index2 + 1
    return indices