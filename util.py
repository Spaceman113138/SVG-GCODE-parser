import math

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


def splitIgnoreThing(delim: str, ignore: list, string: str):
    if len(delim) > 1 or delim == '"' or delim == '"':
        #invalid
        a = 1/0 #why doesn't python catch this stupid language

    result = []

    inDoubleQuotes = False

    i = 0
    while i != len(string):
        try:
            ignore.index(string[i])
            inDoubleQuotes = not inDoubleQuotes
        except:
            pass

        if string[i] == delim and not inDoubleQuotes:
            result.append(string[0:i].strip())
            string = string[i+1:].lstrip()
            i = 0
        else:
            i += 1
    
    result.append(string)
    return result