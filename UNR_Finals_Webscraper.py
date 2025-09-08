from ast import For
from re import I
from pypdf import PdfReader
import requests
from bs4 import BeautifulSoup
import csv

def toMilitary(time):
    if not ("AM" in time or "PM" in time):
        return time

    if ("AM" in time):
        newTime = int(time.replace("AM", ""))
        if (newTime < 100):
            newTime = f"{newTime:02d}00"
        elif (newTime < 1000):
            newTime = f"0{newTime:02d}"
        return str(newTime)
    else:
        newTime = int(time.replace("PM", ""))
        if (newTime < 100):
            newTime = f"{newTime:02d}00"
        elif (newTime < 1000):
            newTime = f"0{newTime:02d}"
        newTime = int(newTime) + 1200
        return str(newTime)

def getFinalsSchedule(finalsSchedulePath):
    finalsSchedule = {
        "Monday": [],
        "Tuesday": [],
        "Wednesday": [],
        "Thursday": [],
        "Friday": [],
        "Saturday": []
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
                    startTime = columns[0]
                    #Format Time
                    startTime = startTime.replace("a.m.", "AM")
                    startTime = startTime.replace("p.m.", "PM")
                    startTime = startTime.replace(":", "")
                    startTime = startTime.replace(" ", "")

                    startTime = toMilitary(startTime)

                    scheduleArray.append(startTime)

                if (len(columns) >= 2): #Days Class is Held On
                    classDays = []
                    words = columns[1].split()

                    for word in words:
                        if (word in dayKeyWords):
                            dayKey = word.replace("(", "")
                            dayKey = dayKey.replace(")", "")
                            classDays.append(dayKey)

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
        "M": [],
        "T": [],
        "W": [],
        "R": [],
        "F": [],
        "S": []
    }

    dayAbreviationMap = {
        "Monday": "M",
        "Tuesday": "T",
        "Wednesday": "W",
        "Thursday": "R",
        "Friday": "F",
        "Saturday": "S"
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

                if (currentWord in dayAbreviationMap.keys()):
                    days.append(dayAbreviationMap[currentWord])

                if ("AM" in currentWord or "PM" in currentWord):
                    time = currentWord.replace(":", "")
                    time = time.replace(" ", "")
                    times.append(toMilitary(time))

                if (prevWord):
                    if (prevWord == "to"):
                        for day in days:
                            classSchedule[day].append(times[0])
                        days = []
                        times = []

    #Invert Class Schedule Mapping
    invertedClassSchedule = {}
    for day, times in classSchedule.items():
        for time in times:
            if time not in invertedClassSchedule:
                invertedClassSchedule[time] = []
            invertedClassSchedule[time].append(day)

    for key in invertedClassSchedule:
        invertedClassSchedule[key] = "".join(invertedClassSchedule[key])

    return invertedClassSchedule

def generateCompleteSchedule(classDict, finalsDict):
    finalDays = []
    for day in finalsDict:
        for entry in finalsDict[day]:
            startTime = entry[0]
            if (startTime in classDict.keys()):
                if (classDict[startTime] in entry[1]):
                    finalDays.append([str(day), entry[2]])

    return finalDays

def generateCSV(completeSchedule):
    with open('StudentFinalsSchedule.csv', 'w', newline='') as csvfile:
        scheduleWriter = csv.writer(csvfile, delimiter=' ', quotechar='|', quoting=csv.QUOTE_MINIMAL)
        for entry in completeSchedule:
            scheduleWriter.writerow(entry)

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
    print ("\nCombined Schedule:\n", completedSchedule)

    generateCSV(completedSchedule)

if __name__ == "__main__":
    main()
