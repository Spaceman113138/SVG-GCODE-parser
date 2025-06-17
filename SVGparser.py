import re

scaleFactor = 1.0
shift = [0,0]
travelSpeed = 40
drawSpeed = 20





#Utilish Functions

def addPoints(p1, p2):
    return [p1[0] + p2[0]. p1[1] + p2[1]]


def lerp(t, v1, v2):
    return (1 - t) * v1 + t * v2


def fixWeirdSVGrules(string: str):
    string = string.replace(",", " ")

    #Turn #A# -> # A #
    i = 0
    while i < len(string):
        char = string[i]
        if char.isalpha():
            half = string[0:i]
            half2 = string[i+1:]
            string = f"{half} {char} {half2}"
            i += 1
        i += 1
    string = string.replace("  ", " ")

    #Turn #-1# -> # -1#
    i = 0
    while i < len(string):
        char = string[i]
        if char == "-":
            half = string[0:i]
            half2 = string[i:]
            string = f"{half} {half2}"
            i += 1
        i += 1
    string = string.replace("  ", " ")

    #Turn #00# -> #0 0#
    i = 0
    inNum = False
    while i < len(string):
        char = string[i]
        if char == "0" and string[i+1] == "0" and not inNum:
            half = string[0:i+1]
            half2 = string[i+1:]
            string = f"{half} {half2}"
            i += 1
        
        inNum = char.isnumeric() or char == "."
        i += 1

    #Turn #.12.12# -> #.12 .12#

    i = 0
    hasMetPeriod = False
    while i < len(string):
        char = string[i]
        if char == ".":
            if hasMetPeriod:
                half = string[0:i]
                half2 = string[i:]
                string = f"{half} {half2}"
                i += 1
            hasMetPeriod = True
        elif char == " ":
            hasMetPeriod = False
        
        i += 1

    return string


def scaleLine(line: list[list]):
    scaledLine = []
    for point in line:
        x = round(point[0] * scaleFactor + shift[0], 5)
        y = round(point[1] * scaleFactor + shift[1], 5)
        scaledLine.append([x,y])

    return scaledLine



#Main part of code

def parseSVG(pathToFile: str):
    rawString = open(pathToFile, "r").read()
    
    #Grab Only useful lines
    groups = rawString.split("<")
    lines = []
    #Parse Usefull Groups
    for group in groups:
        try:
            firstWord = group.split()[0]
        except:
            continue
        match firstWord:
            case "path":
                lines.extend(parsePath(group))

    gcode = parseLinesIntoGcode(lines)
    print(gcode)
    return gcode


def parsePath(pathString: str):
    #Grab the actual path data and turn it into a format that is easy to parse
    index = pathString.index("d=") + 2
    newString = pathString[index:]
    finalString = newString.split('"')[1]
    finalString = fixWeirdSVGrules(finalString).strip()

    #Split on command chars 
    finalString = re.split("( )", finalString)
    commands = []
    currentCommand = []
    while len(finalString) > 0:
        thing = finalString.pop(0)
        if thing.isalpha():
            if currentCommand != []:
                currentCommand[1] = currentCommand[1].split()
                commands.append(currentCommand)
            currentCommand: list = [thing, ""]
        else:
            currentCommand[1] = currentCommand[1] + thing

    commands.append(currentCommand)

    lines = [] #Holds all lines to be drawn
    currentLine = [] #A list of points that makes up a line to be drawn

    currentStartPoint = []
    currentPoint = []
    lastCtrlPoint = []
    for command in commands:
        print(command)
        value:list = command[1]
        match command[0]:
            case "M":
                currentLine = []
                firstPoint = [float(value.pop(0)), float(value.pop(0))]
                currentLine.append(firstPoint)
                currentStartPoint = firstPoint
                currentPoint = firstPoint

                while len(value) > 0:
                    nextPoint = [float(value.pop(0)), float(value.pop(0))]
                    currentLine.append(nextPoint)
                    currentPoint = nextPoint

            case "m":
                currentLine = []
                firstPoint = [float(value.pop(0)), float(value.pop(0))]
                currentLine.append(firstPoint)
                currentStartPoint = firstPoint
                currentPoint = firstPoint

                while len(value) > 0:
                    nextPoint = [float(value.pop(0)), float(value.pop(0))]
                    nextPoint = addPoints(currentPoint, nextPoint)
                    currentLine.append(nextPoint)
                    currentPoint = nextPoint

            case "H":
                while len(value) > 0:
                    nextPoint = [float(value.pop(0)), currentPoint[1]]
                    currentLine.append(nextPoint)
                    currentPoint = nextPoint

            case "h":
                while len(value) > 0:
                    nextPoint = [float(value.pop(0)) + currentPoint[0], currentPoint[1]]
                    currentLine.append(nextPoint)
                    currentPoint = nextPoint

            case "V":
                while len(value) > 0:
                    nextPoint = [currentPoint[0], float(value.pop(0))]
                    currentLine.append(nextPoint)
                    currentPoint = nextPoint

            case "v":
                while len(value) > 0:
                    nextPoint = [currentPoint[0], float(value.pop(0)) + currentPoint[1]]
                    currentLine.append(nextPoint)
                    currentPoint = nextPoint

            case "C":
                while len(value) > 0:
                    s = currentPoint.copy()
                    c1 = [float(value.pop(0)), float(value.pop(0))]
                    c2 = [float(value.pop(0)), float(value.pop(0))]
                    e = [float(value.pop(0)), float(value.pop(0))]
                    currentPoint = e.copy()

                    t = 0
                    while t <= 1:
                        x = (1-t)*(1-t)*(1-t)*s[0] + 3*(1-t)*(1-t)*t*c1[0] + 3*(1-t)*t*t*c2[0] + t*t*t*e[0]
                        y = (1-t)*(1-t)*(1-t)*s[1] + 3*(1-t)*(1-t)*t*c1[1] + 3*(1-t)*t*t*c2[1] + t*t*t*e[1]
                        nextPoint = [x,y]
                        currentLine.append(nextPoint)
                        t += .1

            case "c":
                s = currentPoint
                c1 = addPoints(currentPoint, [float(value.pop(0)), float(value.pop(0))])
                c2 = addPoints(currentPoint, [float(value.pop(0)), float(value.pop(0))])
                e = addPoints(currentPoint, [float(value.pop(0)), float(value.pop(0))])

                t = 0
                while t <= 1:
                    x = (pow(1-t, 3) * s[0]) + (3 * pow(1-t, 2) * c1[0]) + (3 * pow(1-t, 2) * c2[0]) + pow(t, 3) * e[0]
                    y = (pow(1-t, 3) * s[1]) + (3 * pow(1-t, 2) * c1[1]) + (3 * pow(1-t, 2) * c2[1]) + pow(t, 3) * e[1]
                    nextPoint = [x,y]
                    currentLine.append(nextPoint)
                    currentPoint = nextPoint
                    t += .1

            case "Z" | "z":
                currentLine.append(currentStartPoint)
                lines.append(currentLine)

            case _:
                print(f"Implement {command[0]}")
                pass

    return lines


def parseLinesIntoGcode(lines: list[list[list]]):
    finalGcode = ""
    finalGcode += "G28 \n"
    finalGcode += "G90 \n"
    finalGcode += f"G0 f{travelSpeed} \n"
    finalGcode += f"G1 f{drawSpeed} \n"

    for line in lines:
        line = scaleLine(line)
        finalGcode += "G0 Z10 \n"
        finalGcode += f"G0 X{line[0][0]} Y{line[0][1]} \n"
        finalGcode += "G1 Z0 \n"
        for point in line:
            finalGcode += f"G1 X{point[0]} Y{point[1]} \n"
        finalGcode += "G0 Z10 \n"

    return finalGcode