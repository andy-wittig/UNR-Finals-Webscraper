from re import I
from pypdf import PdfReader
import requests
from bs4 import BeautifulSoup

def getFinalsSchedule(finalsSchedulePath):
    finalsSchedule = {
        "Monday": [],
        "Tuesday": [],
        "Wednesday": [],
        "Thursday": [],
        "Friday": [],
        "Saturday": [],
        "Sunday": []
    }

    try:
        response = requests.get(finalsSchedulePath)
    except requests.exceptions as error:
        print ("Error when attepting to get finals schedule:", error)
        return {}


    if (response.status_code == 200):
        soup = BeautifulSoup(response.content, "html.parser")
        #print (soup.prettify())

        contentDiv = soup.find("div", class_="body-copy-wrapper")
        if (contentDiv):
            currentFinalsDay = ""

            for table in contentDiv.find_all("tbody"):
                tableHeader = table.find_previous("h2")
                finalExamDay = (tableHeader.text.strip())

                tableContent = table.text.strip()
                lines = tableContent.splitlines()
                print (tableContent)

                dayKeyWords = ["(M)", "(T)", "(W)", "(R)", "(F)", "(MW)", "(MWF)", "(TR)"]
                scheduleArray = []

                for i in range(0, len(lines)):
                    if (i == 0): #Class Start Time
                        scheduleArray.append(lines[i])
                    elif (i == 1): #Days Class is Held On
                        classDays = []
                        words = lines[i].split()

                        for word in words:
                            if (word in dayKeyWords):
                                classDays.append(word)

                        scheduleArray.append(classDays)
                    else: #Final Meeting Time
                        scheduleArray.append(lines[i])

                finalsSchedule[finalExamDay].append(scheduleArray)
        else:
            print ("No content was found.")
            return {}
        
        return finalsSchedule
    else:
        print ("Could not retrieve the finals schedule, status code:", response.status_code)
        return {}

def getClassSchedule(schedulePath):
    pdfPath = schedulePath

    try:
        reader = PdfReader(pdfPath)
    except FileNotFoundError as error:
        print ("File path not found:", error)
        return {}

    page = reader.pages[0]
    pageText = page.extract_text()
    pageLines = pageText.splitlines()

    classSchedule = {
        "Monday": [],
        "Tuesday": [],
        "Wednesday": [],
        "Thursday": [],
        "Friday": [],
        "Saturday": [],
        "Sunday": []
    }
    
    days = []
    times = []

    for line in pageLines:
        words = line.split()
        if (not words): continue
        if (words[0] == "Days:" or words[0] == "Times:"):
            for i in range(1, len(words)):
                currentWord = words[i]
                prevWord = words[i - 1]
                #print(currentWord)

                if (currentWord in classSchedule.keys()):
                    days.append(currentWord)

                if ("AM" in currentWord or "PM" in currentWord):
                    times.append(currentWord)

                if (prevWord):
                    if (prevWord == "to"):
                        for day in days:
                            classSchedule[day].append(times)
                        days = []
                        times = []

    return classSchedule

def main():
    pdfFilePath = input("Please provide the file path to the .pdf of your UNR class schedule: \n")
    while (getClassSchedule(pdfFilePath) == {}):
        pdfFilePath = input("Please provide the file path to the .pdf of your UNR class schedule: \n")

    print ("Class Schedule:\n", getClassSchedule(pdfFilePath))

    finalsSchedulePath = "https://www.unr.edu/admissions/records/academic-calendar/finals-schedule"
    print ("\nFinals Schedule:\n", getFinalsSchedule(finalsSchedulePath))

if __name__ == "__main__":
    main()
