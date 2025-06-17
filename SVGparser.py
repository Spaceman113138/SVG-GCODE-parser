import re
import math

scaleFactor = 1.0
shift = [0,0]
travelSpeed = 40
drawSpeed = 20





#Utilish Functions
def clamp(min, max, val):
    if max < val:
        return max
    elif min > val:
        return min
    else:
        return val

def angleVectors(vec1, vec2):
    sign = 1
    if vec1[0] * vec2[1] - vec1[1]*vec2[0] < 0:
        sign = -1

    dotProduct = vec1[0] * vec2[0] + vec1[1] * vec2[1]
    magProduct = math.dist([0,0], vec1) * math.dist([0,0], vec2)
    return sign * math.acos(clamp(-1, 1, dotProduct/magProduct))

def addPoints(p1, p2):
    return [p1[0] + p2[0], p1[1] + p2[1]]


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
        if char == "0" and string[i+1].isnumeric() and not inNum:
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


def centerParameterization(s, radii, xRotate, fA, fS, e):
    subAvg = [(s[0] - e[0]) / 2, (s[1] - e[1]) / 2]
    pointsAvg = [(s[0] + e[0]) / 2, (s[1] + e[1]) / 2]

    pointsPrime = [subAvg[0] * math.cos(xRotate) + subAvg[1] * math.sin(xRotate),
                    subAvg[0] * -math.sin(xRotate) + subAvg[1] * math.cos(xRotate)]
    
    A = ((pointsPrime[0] ** 2) / (radii[0] ** 2)) + ((pointsPrime[1] ** 2) / (radii[1] ** 2))

    if (A > 1):
        radii[0] = radii[0] * math.sqrt(A)
        radii[1] = radii[1] * math.sqrt(A)

    
    sign = 1
    if fA == fS:
        sign = -1

    topHalf = ((radii[0] ** 2) * (radii[1] ** 2)) - ((radii[0] ** 2) * (pointsPrime[1] ** 2)) - ((radii[1] ** 2) * (pointsPrime[0] ** 2))
    if topHalf < 0.0 and topHalf > -0.001:
        topHalf = 0.0
    bottomHalf = ((radii[0] ** 2) * (pointsPrime[1] ** 2) + (radii[1] ** 2) * (pointsPrime[0] ** 2))

    constant = sign * math.sqrt(topHalf/bottomHalf)
    radiiThing = [radii[0] * pointsPrime[1] / radii[1], -radii[1] * pointsPrime[0] / radii[0]]
    centerPrime = [radiiThing[0] * constant, radiiThing[1] * constant]

    cPrimeRotated = [centerPrime[0] * math.cos(xRotate) + centerPrime[1] * -math.sin(xRotate),
                     centerPrime[0] * math.sin(xRotate) + centerPrime[1] * math.cos(xRotate)]
    centers = [cPrimeRotated[0] + pointsAvg[0], cPrimeRotated[1] + pointsAvg[1]]

    vec1 = [1,0]
    startVec = [(pointsPrime[0] - centerPrime[0])/radii[0], (pointsPrime[1] - centerPrime[1])/radii[1]]
    endVec = [(-pointsPrime[0] - centerPrime[0])/radii[0], (-pointsPrime[1] - centerPrime[1])/radii[1]]

    #Angles in radians
    startAngle = angleVectors(vec1, startVec)
    deltaAngle = angleVectors(startVec, endVec) % (2 * math.pi)

    if fS == False and deltaAngle > 0:
        deltaAngle -= 2 * math.pi
    elif fS == True and deltaAngle < 0:
        deltaAngle += 2 * math.pi

    return [centers, startAngle, deltaAngle]






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
            case "polygon":
                lines.extend(parsePolygon(group))

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
    currentPoint = [0,0]
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
                firstPoint = [float(value.pop(0)) + currentPoint[0], float(value.pop(0)) + currentPoint[1]]
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
                    lastCtrlPoint = c2.copy()

                    t = 0
                    while t <= 1:
                        x = (1-t)*(1-t)*(1-t)*s[0] + 3*(1-t)*(1-t)*t*c1[0] + 3*(1-t)*t*t*c2[0] + t*t*t*e[0]
                        y = (1-t)*(1-t)*(1-t)*s[1] + 3*(1-t)*(1-t)*t*c1[1] + 3*(1-t)*t*t*c2[1] + t*t*t*e[1]
                        nextPoint = [x,y]
                        currentLine.append(nextPoint)
                        t += .1

            case "c":
                while len(value) > 0:
                    s = currentPoint
                    c1 = addPoints(currentPoint, [float(value.pop(0)), float(value.pop(0))])
                    c2 = addPoints(currentPoint, [float(value.pop(0)), float(value.pop(0))])
                    e = addPoints(currentPoint, [float(value.pop(0)), float(value.pop(0))])
                    currentPoint = e.copy()
                    lastCtrlPoint = c2.copy()

                    t = 0
                    while t <= 1:
                        x = (1-t)*(1-t)*(1-t)*s[0] + 3*(1-t)*(1-t)*t*c1[0] + 3*(1-t)*t*t*c2[0] + t*t*t*e[0]
                        y = (1-t)*(1-t)*(1-t)*s[1] + 3*(1-t)*(1-t)*t*c1[1] + 3*(1-t)*t*t*c2[1] + t*t*t*e[1]
                        nextPoint = [x,y]
                        currentLine.append(nextPoint)
                        t += .1

            case "A":
                fixedValues = []
                while len(value) > 0:
                    fixedValues.append(value.pop(0))
                    fixedValues.append(value.pop(0))
                    
                    i = 0
                    while i < 3:
                        if len(value[0]) == 1:
                            fixedValues.append(value.pop(0))
                        else:
                            fixedValues.append(value[0][0])
                            value[0] = value[0][1:]
                        i += 1
                    
                    fixedValues.append(value.pop(0))
                    fixedValues.append(value.pop(0))
                
                value = fixedValues
                print(value)

                while len(value) > 0:
                    s = currentPoint
                    radii = [float(value.pop(0)), float(value.pop(0))]
                    xRotate = math.radians(float(value.pop(0)))
                    fA = bool(int(value.pop(0)))
                    fS = bool(int(value.pop(0)))
                    e = [float(value.pop(0)), float(value.pop(0))]
                    currentPoint = e.copy()

                    array = centerParameterization(s, radii, xRotate, fA, fS, e)
                    centers = array[0]
                    startAngle = array[1]
                    deltaAngle = array[2]

                    #Get points to draw
                    t = 0
                    while t <= 1:
                        angle = lerp(clamp(0, 1.0, t), 0, deltaAngle) + startAngle
                        x = radii[0] * math.cos(angle) * math.cos(xRotate) - radii[1] * math.sin(angle) * math.sin(xRotate) + centers[0]
                        y = radii[0] * math.cos(angle) * math.sin(xRotate) + radii[1] * math.sin(angle) * math.cos(xRotate) + centers[1]
                        currentLine.append([x,y])
                        t = round(t + 0.05, 5)

            case "a":
                fixedValues = []
                while len(value) > 0:
                    fixedValues.append(value.pop(0))
                    fixedValues.append(value.pop(0))
                    
                    i = 0
                    while i < 3:
                        if len(value[0]) == 1:
                            fixedValues.append(value.pop(0))
                        else:
                            fixedValues.append(value[0][0])
                            value[0] = value[0][1:]
                        i += 1
                    
                    fixedValues.append(value.pop(0))
                    fixedValues.append(value.pop(0))
                
                value = fixedValues
                print(value)


                while len(value) > 0:
                    subset = []
                    s = currentPoint
                    radii = [float(value.pop(0)), float(value.pop(0))]
                    xRotate = math.radians(float(value.pop(0)))
                    fA = bool(int(value.pop(0)))
                    fS = bool(int(value.pop(0)))
                    e = addPoints(currentPoint, [float(value.pop(0)), float(value.pop(0))])
                    currentPoint = e.copy()

                    array = centerParameterization(s, radii, xRotate, fA, fS, e)
                    centers = array[0]
                    startAngle = array[1]
                    deltaAngle = array[2]

                    #Get points to draw
                    t = 0
                    while t <= 1:
                        angle = lerp(clamp(0, 1.0, t), 0, deltaAngle) + startAngle
                        x = radii[0] * math.cos(angle) * math.cos(xRotate) - radii[1] * math.sin(angle) * math.sin(xRotate) + centers[0]
                        y = radii[0] * math.cos(angle) * math.sin(xRotate) + radii[1] * math.sin(angle) * math.cos(xRotate) + centers[1]
                        currentLine.append([x,y])
                        t = round(t + 0.05, 5)

            case "L":
                newPoint = [float(value.pop(0)), float(value.pop(0))]
                currentLine.append(newPoint)
                currentPoint = newPoint

            case "l":
                newPoint = [float(value.pop(0)) + currentPoint[0], float(value.pop(0)) + currentPoint[1]]
                currentLine.append(newPoint)
                currentPoint = newPoint

            case "Z" | "z":
                currentLine.append(currentStartPoint)
                lines.append(currentLine)

            case "S":
                while len(value) > 0:
                    s = currentPoint
                    delta = [currentPoint[0] - lastCtrlPoint[0], currentPoint[1] - lastCtrlPoint[1]]
                    c1 = addPoints(delta, s)
                    c2 = [float(value.pop(0)), float(value.pop(0))]
                    e = [float(value.pop(0)), float(value.pop(0))]
                    currentPoint = e.copy()
                    lastCtrlPoint = c2.copy()

                    t = 0
                    while t <= 1:
                        x = (1-t)*(1-t)*(1-t)*s[0] + 3*(1-t)*(1-t)*t*c1[0] + 3*(1-t)*t*t*c2[0] + t*t*t*e[0]
                        y = (1-t)*(1-t)*(1-t)*s[1] + 3*(1-t)*(1-t)*t*c1[1] + 3*(1-t)*t*t*c2[1] + t*t*t*e[1]
                        nextPoint = [x,y]
                        currentLine.append(nextPoint)
                        t += .1

            case "s":
                while len(value) > 0:
                    s = currentPoint
                    delta = [currentPoint[0] - lastCtrlPoint[0], currentPoint[1] - lastCtrlPoint[1]]
                    c1 = addPoints(delta, s)
                    c2 = addPoints(currentPoint, [float(value.pop(0)), float(value.pop(0))])
                    e = addPoints(currentPoint, [float(value.pop(0)), float(value.pop(0))])
                    currentPoint = e.copy()
                    lastCtrlPoint = c2.copy()

                    t = 0
                    while t <= 1:
                        x = (1-t)*(1-t)*(1-t)*s[0] + 3*(1-t)*(1-t)*t*c1[0] + 3*(1-t)*t*t*c2[0] + t*t*t*e[0]
                        y = (1-t)*(1-t)*(1-t)*s[1] + 3*(1-t)*(1-t)*t*c1[1] + 3*(1-t)*t*t*c2[1] + t*t*t*e[1]
                        nextPoint = [x,y]
                        currentLine.append(nextPoint)
                        t += .1



            case _:
                print(f"Implement {command[0]}")
                pass

    return lines


def parsePolygon(pathString: str):
    onlyPoints = pathString.split("points=\"")[1]
    onlyPoints = onlyPoints.strip().removesuffix('"/>').strip()
    finalPoints = fixWeirdSVGrules(onlyPoints).split()
    print(["Polygon", finalPoints])

    line = []
    line.append([float(finalPoints[-2]), float(finalPoints[-1])])
    while len(finalPoints) > 0:
        line.append([float(finalPoints.pop(0)), float(finalPoints.pop(0))])
    print(line)
    return [line]


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