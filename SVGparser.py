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


def aproxLenCubic(s, c1, c2, e):
    lastPoint = s
    length = 0.0
    t = 0.01
    while t <= 1:
        x = (1-t)*(1-t)*(1-t)*s[0] + 3*(1-t)*(1-t)*t*c1[0] + 3*(1-t)*t*t*c2[0] + t*t*t*e[0]
        y = (1-t)*(1-t)*(1-t)*s[1] + 3*(1-t)*(1-t)*t*c1[1] + 3*(1-t)*t*t*c2[1] + t*t*t*e[1]
        nextPoint = [x,y]
        length += math.dist(nextPoint, lastPoint)
        lastPoint = nextPoint.copy()
        t += .01

    return length


def aproxLenElipse(startAngle, deltaAngle, xRotate, radii, centers):
    length = 0
    initX = radii[0] * math.cos(startAngle) * math.cos(xRotate) - radii[1] * math.sin(startAngle) * math.sin(xRotate) + centers[0]
    initY = radii[0] * math.cos(startAngle) * math.sin(xRotate) + radii[1] * math.sin(startAngle) * math.cos(xRotate) + centers[1]
    lastPoint = [initX, initY]
    t = 0
    while t <= 1:
        angle = lerp(clamp(0, 1.0, t), 0, deltaAngle) + startAngle
        x = radii[0] * math.cos(angle) * math.cos(xRotate) - radii[1] * math.sin(angle) * math.sin(xRotate) + centers[0]
        y = radii[0] * math.cos(angle) * math.sin(xRotate) + radii[1] * math.sin(angle) * math.cos(xRotate) + centers[1]
        newPoint = [x,y]
        length += math.dist(lastPoint, newPoint)
        lastPoint = newPoint.copy()
        t = round(t + 0.05, 5)
    
    return length



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
        if not str(point[0]).isalpha():
            x = round(point[0] * scaleFactor + shift[0], 5)
            y = round(point[1] * scaleFactor + shift[1], 5)
            scaledLine.append([x,y])
        else:
            scaledLine.append(point)

    return scaledLine

def fixElipseValues(value: list):
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
    return fixedValues


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

def parseSVG(pathToFile: str, desiredSize:float, desiredCenter: list[float]):
    rawString = open(pathToFile, "r").read()

    groups = []

    try:
        while True:
            startIndex = rawString.index("<g")
            endIndex = rawString.index("</g>")
            groups.append(rawString[0:startIndex])
            groups.append(rawString[startIndex: endIndex])
            rawString = rawString[endIndex:]
    except:
        pass

    groups.append(rawString)

    lines = []

    for group in groups:
        transform = [0,0]
        rotation = 0
        #Grab Only useful lines
        paths = group.split("<")
        #Parse Usefull Groups
        for path in paths:
            try:
                firstWord = path.split()[0]
            except:
                continue
            match firstWord:
                case "g":
                    try:
                        index = path.index("translate")
                        sub = path[index:]
                        sub = re.split("[()]", sub)[1]
                        transform = sub.split()
                        transform = [float(transform[0]), float(transform[1])]
                    except:
                        pass
                    try:
                        index = path.index("rotate")
                        sub = path[index:]
                        sub = re.split("[()]", sub)[1]
                        rotation = float(sub)
                    except:
                        pass
                case "path":
                    rawLines = parsePath(pathStringToCommands(path))
                    lines.extend(adjustGroups(rawLines, transform, rotation))
                case "polygon":
                    rawLines = parsePolygon(path)
                    lines.extend(adjustGroups(rawLines, transform, rotation))
                case "rect":
                    rawLines = parseRectangle(path)
                    lines.extend(adjustGroups(rawLines, transform, rotation))

    #adjustScalePosition(desiredSize, desiredCenter, lines)
    gcode = parseLinesIntoGcode(lines)
    print(gcode)
    return gcode


def pathStringToCommands(pathString: str):
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

    return commands


def parsePath(commands: list):
    currentCommand = ""

    lines = [] #Holds all lines to be drawn
    currentLine = [] #A list of points that makes up a line to be drawn

    currentStartPoint = []
    currentPoint = [0,0]
    lastCtrlPoint = []
    lastCommand = ""
    for command in commands:
        print(command)
        if command[1] == '':
            command[1] = []
        currentLine.append([command[0], command[1].copy()])
        value:list = command[1]
        match command[0]:
            case "M":
                currentLine = []
                currentLine.append([command[0], command[1].copy()])
                firstPoint = [float(value.pop(0)), float(value.pop(0))]
                currentLine.append(firstPoint)
                currentStartPoint = firstPoint.copy()
                currentPoint = firstPoint.copy()

                while len(value) > 0:
                    nextPoint = [float(value.pop(0)), float(value.pop(0))]
                    currentLine.append(nextPoint)
                    currentPoint = nextPoint.copy()

            case "m":
                currentLine = []
                currentLine.append([command[0], command[1].copy()])
                firstPoint = [float(value.pop(0)) + currentPoint[0], float(value.pop(0)) + currentPoint[1]]
                currentLine.append(firstPoint)
                currentStartPoint = firstPoint.copy()
                currentPoint = firstPoint.copy()

                while len(value) > 0:
                    nextPoint = [float(value.pop(0)), float(value.pop(0))]
                    nextPoint = addPoints(currentPoint, nextPoint)
                    currentLine.append(nextPoint)
                    currentPoint = nextPoint.copy()

            case "H":
                while len(value) > 0:
                    nextPoint = [float(value.pop(0)), currentPoint[1]]
                    currentLine.append(nextPoint)
                    currentPoint = nextPoint.copy()

            case "h":
                while len(value) > 0:
                    nextPoint = [float(value.pop(0)) + currentPoint[0], currentPoint[1]]
                    currentLine.append(nextPoint)
                    currentPoint = nextPoint.copy()

            case "V":
                while len(value) > 0:
                    nextPoint = [currentPoint[0], float(value.pop(0))]
                    currentLine.append(nextPoint)
                    currentPoint = nextPoint.copy()

            case "v":
                while len(value) > 0:
                    nextPoint = [currentPoint[0], float(value.pop(0)) + currentPoint[1]]
                    currentLine.append(nextPoint)
                    currentPoint = nextPoint.copy()

            case "C":
                while len(value) > 0:
                    s = currentPoint.copy()
                    c1 = [float(value.pop(0)), float(value.pop(0))]
                    c2 = [float(value.pop(0)), float(value.pop(0))]
                    e = [float(value.pop(0)), float(value.pop(0))]
                    currentPoint = e.copy()
                    lastCtrlPoint = c2.copy()

                    currentLine.extend(parseCubicBezie(s, c1, c2, e))

            case "c":
                while len(value) > 0:
                    s = currentPoint
                    c1 = addPoints(currentPoint, [float(value.pop(0)), float(value.pop(0))])
                    c2 = addPoints(currentPoint, [float(value.pop(0)), float(value.pop(0))])
                    e = addPoints(currentPoint, [float(value.pop(0)), float(value.pop(0))])
                    currentPoint = e.copy()
                    lastCtrlPoint = c2.copy()

                    currentLine.extend(parseCubicBezie(s, c1, c2, e))

            case "A":
                value = fixElipseValues(value)
                print(value)

                while len(value) > 0:
                    s = currentPoint
                    radii = [float(value.pop(0)), float(value.pop(0))]
                    xRotate = math.radians(float(value.pop(0)))
                    fA = bool(int(value.pop(0)))
                    fS = bool(int(value.pop(0)))
                    e = [float(value.pop(0)), float(value.pop(0))]
                    currentPoint = e.copy()

                    currentLine.extend(parseElipse(s, radii, xRotate, fA, fS, e))

            case "a":
                value = fixElipseValues(value)
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

                    currentLine.extend(parseElipse(s, radii, xRotate, fA, fS, e))

            case "L":
                while len(value) > 0:
                    newPoint = [float(value.pop(0)), float(value.pop(0))]
                    currentLine.append(newPoint)
                    currentPoint = newPoint.copy()

            case "l":
                while len(value) > 0:
                    newPoint = [float(value.pop(0)) + currentPoint[0], float(value.pop(0)) + currentPoint[1]]
                    currentLine.append(newPoint)
                    currentPoint = newPoint.copy()

            case "Z" | "z":
                currentPoint = currentStartPoint.copy()
                currentLine.append(currentStartPoint)
                lines.append(currentLine)

            case "S":
                if lastCommand.capitalize() == "C" or lastCommand.capitalize() == "S":
                    lastCtrlPoint = currentPoint
                while len(value) > 0:
                    s = currentPoint
                    delta = [currentPoint[0] - lastCtrlPoint[0], currentPoint[1] - lastCtrlPoint[1]]
                    c1 = addPoints(delta, s)
                    c2 = [float(value.pop(0)), float(value.pop(0))]
                    e = [float(value.pop(0)), float(value.pop(0))]
                    currentPoint = e.copy()
                    lastCtrlPoint = c2.copy()

                    currentLine.extend(parseCubicBezie(s, c1, c2, e))

            case "s":
                if not (lastCommand.capitalize() == "C" or lastCommand.capitalize() == "S"):
                    lastCtrlPoint = currentPoint
                while len(value) > 0:
                    s = currentPoint
                    delta = [currentPoint[0] - lastCtrlPoint[0], currentPoint[1] - lastCtrlPoint[1]]
                    c1 = addPoints(delta, s)
                    c2 = addPoints(currentPoint, [float(value.pop(0)), float(value.pop(0))])
                    e = addPoints(currentPoint, [float(value.pop(0)), float(value.pop(0))])
                    currentPoint = e.copy()
                    lastCtrlPoint = c2.copy()

                    currentLine.extend(parseCubicBezie(s, c1, c2, e))



            case _:
                print(f"Implement {command[0]}")
                i = 1/0
                pass
        lastCommand = command[0]

    return lines


def parseCubicBezie(s, c1, c2, e):
    points = []
    length = aproxLenCubic(s, c1, c2, e)
    t = 0
    while t <= 1:
        t = clamp(0, 1, t)
        x = (1-t)*(1-t)*(1-t)*s[0] + 3*(1-t)*(1-t)*t*c1[0] + 3*(1-t)*t*t*c2[0] + t*t*t*e[0]
        y = (1-t)*(1-t)*(1-t)*s[1] + 3*(1-t)*(1-t)*t*c1[1] + 3*(1-t)*t*t*c2[1] + t*t*t*e[1]
        nextPoint = [x,y]
        points.append(nextPoint)
        t += 1/(length * 10)

    return points


def parseElipse(s, radii, xRotate, fA, fS, e):
    points = []
    array = centerParameterization(s, radii, xRotate, fA, fS, e)
    centers = array[0]
    startAngle = array[1]
    deltaAngle = array[2]

    #Get points to draw
    length = aproxLenElipse(startAngle, deltaAngle, xRotate, radii, centers)
    t = 0
    while t <= 1:
        angle = lerp(clamp(0, 1.0, t), 0, deltaAngle) + startAngle
        x = radii[0] * math.cos(angle) * math.cos(xRotate) - radii[1] * math.sin(angle) * math.sin(xRotate) + centers[0]
        y = radii[0] * math.cos(angle) * math.sin(xRotate) + radii[1] * math.sin(angle) * math.cos(xRotate) + centers[1]
        points.append([x,y])
        t += 1/(length * 10)
    
    return points


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


def parseRectangle(pathString: str):
    print(pathString)
    x = 0
    y = 0
    width = 0
    height = 0
    rx = -1
    ry = -1

    splitString = pathString.split()
    for param in splitString:
        try:
            index = param.index("=")
            key = param[0:index]
            match key:
                case "x":
                    x = float(param.split('"')[1])
                case "y":
                    y = float(param.split('"')[1])
                case "width":
                    width = float(param.split('"')[1])
                case "height":
                    height = float(param.split('"')[1])
                case "rx":
                    rx = float(param.split('"')[1])
                case "ry":
                    ry = float(param.split('"')[1])
        except:
            pass

    #Handle rx or ry not being provided or being not possible
    if rx == -1 and ry == -1:
        rx,ry = 0,0
    elif ry == -1:
        ry = rx
    elif rx == -1:
        rx = ry

    if rx > width/2:
        rx = width/2
    if ry > height/2:
        ry = height/2

    #convert to path because it makes it easier
    commandList = [
        ["M", [x+rx, y]],
        ["H", [x+width-rx]],
        ["V", [y+height-ry]],
        ["H", [x+rx]],
        ["V", [y+ry]],
        ["Z", ""]
    ]

    if rx > 0 and ry > 0:
        commandList.insert(2, ["A", [rx, ry, "0", "0", "1", x+width, y+ry]])
        commandList.insert(4, ["A", [rx, ry, "0", "0", "1", x+width-rx, y+height]])
        commandList.insert(6, ["A", [rx, ry, "0", "0", "1", x, y+height-ry]])
        commandList.insert(8, ["A", [rx, ry, "0", "0", "1", x+rx, y]])

    print(x,y,width,height)
    line = parsePath(commandList)
    return line


def parseLinesIntoGcode(lines: list[list[list]]):
    finalGcode = ""
    finalGcode += "G28 \n"
    finalGcode += "G90 \n"
    finalGcode += f"G0 f{travelSpeed} \n"
    finalGcode += f"G1 f{drawSpeed} \n"

    for line in lines:
        line = scaleLine(line)
        finalGcode += "G0 Z10 \n"
        finalGcode += f"G0 X{line[1][0]} Y{line[1][1]} \n"
        finalGcode += "G1 Z0 \n"
        for point in line:
            if str(point[0]).isalpha():
                finalGcode += f";{point} \n"
            else:
                finalGcode += f"G1 X{point[0]} Y{point[1]} \n"
        finalGcode += "G0 Z10 \n"

    return finalGcode


def adjustScalePosition(desiredMaxSize, desiredCenter, lines):
    global scaleFactor
    global shift

    minX = math.inf
    minY = math.inf
    maxX = -math.inf
    maxY = -math.inf

    for line in lines:
        for point in line:
            if not str(point[0]).isalpha():
                if point[0] < minX:
                    minX = point[0]
                if point[0] > maxX:
                    maxX = point[0]
                if point[1] < minY:
                    minY = point[1]
                if point[1] > maxY:
                    maxY = point[1]

    print(minX, maxX)
    print(minY, maxY)
    xSize = maxX - minX
    ySize = maxY - minY
    largest = 0
    if xSize > ySize:
        largest = xSize
    else:
        largest = ySize
    scaleFactor = desiredMaxSize/largest

    center = [(minX + maxX) / 2, (minY + maxY) / 2]
    shift = [-center[0] * scaleFactor + desiredCenter[0], -center[1] * scaleFactor + desiredCenter[0]]


def adjustGroups(lines, translation, rotation):
    rotation = math.radians(rotation)
    newLines = []
    for line in lines:
        newLine = []
        for point in line:
            if str(point[0]).isalpha():
                newLine.append(point)
            else:
                rotatedPoint = [point[0] * math.cos(rotation) + point[1] * -math.sin(rotation),
                                point[0] * math.sin(rotation) + point[1] * math.cos(rotation)]
                translatedPoint = addPoints(rotatedPoint, translation)
                newLine.append(translatedPoint)
        newLines.append(newLine)
    return newLines