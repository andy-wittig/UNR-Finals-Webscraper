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
    except requests.exceptions.RequestException as error:
        print ("Error when attepting to get finals schedule:", error)
        return {}


    if (response.status_code == 200):
        soup = BeautifulSoup(response.content, "html.parser")
        #print (soup.prettify())

        contentDiv = soup.find("div", class_="body-copy-wrapper")
        if (not contentDiv):
            print ("No content was found.")
            return {}

        for table in contentDiv.find_all("tbody"):
            tableHeader = table.find_previous("h2")
            if (not tableHeader):
                continue

            finalExamDay = (tableHeader.text.strip())

            tableContent = table.text.strip()
            #print (tableContent)

            dayKeyWords = ["(M)", "(T)", "(W)", "(R)", "(F)", "(MW)", "(MWF)", "(TR)", "Varies"]

            for row in table.find_all("tr"):
                scheduleArray = []
                columns = []

                for column in row.find_all("td"):
                    columnContent = column.text.strip()
                    if (not columnContent): continue
                    #print (columnContent)
                    columns.append(columnContent)

                if (len(columns) >= 1): #Class Start Time
                    scheduleArray.append(columns[0])

                if (len(columns) >= 2): #Days Class is Held On
                    classDays = []
                    words = columns[1].split()

                    for word in words:
                        if (word in dayKeyWords):
                            classDays.append(word)

                    scheduleArray.append(classDays)

                if (len(columns) >= 3): #Final Meeting Time
                    scheduleArray.append(columns[2])

            finalsSchedule[finalExamDay].append(scheduleArray)
        
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

    pageText = ""
    for i in range(0, len(reader.pages)):
        page = reader.pages[i]
        pageText += page.extract_text()

    pageLines = pageText.splitlines()

    #print (pageText)

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
                            classSchedule[day].append(times[0])
                        days = []
                        times = []

    return classSchedule

def generateCompleteSchedule(classDict, finalsDict):
    pass

def main():
    pdfFilePath = input("Please provide the file path to the .pdf of your UNR class schedule: \n")
    while (getClassSchedule(pdfFilePath) == {}):
        pdfFilePath = input("Please provide the file path to the .pdf of your UNR class schedule: \n")

    classSchedule = getClassSchedule(pdfFilePath)
    print ("Class Schedule:\n", classSchedule)

    finalsSchedulePath = "https://www.unr.edu/admissions/records/academic-calendar/finals-schedule"
    finalsSchedule = getFinalsSchedule(finalsSchedulePath)
    print ("\nFinals Schedule:\n", finalsSchedule)

    completedSchedule = generateCompleteSchedule(classSchedule, finalsSchedule)
    print (completedSchedule)

if __name__ == "__main__":
    main()
