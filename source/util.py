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


def angleBetweenVectors(u, v):
    dot_product = sum(i*j for i, j in zip(u, v))
    norm_u = math.sqrt(sum(i**2 for i in u))
    norm_v = math.sqrt(sum(i**2 for i in v))
    cos_theta = dot_product / (norm_u * norm_v)
    angle_rad = math.acos(cos_theta)
    return angle_rad

class Vector2d():
    x = 0
    y = 0
    slope = 0
    angle = 0
    def __init__(self, x, y) -> None:
        self.x = x
        self.y = y
        self.slope = self.calcSlope()
        self.angle = self.getAngle()

    def __add__(self, vec2):
        return Vector2d(self.x + vec2.x, self.y + vec2.y)
    
    def __sub__(self, vec2):
        return Vector2d(self.x - vec2.x, self.y - vec2.y)
    
    def __mul__(self, scalar):
        return Vector2d(self.x * scalar, self.y * scalar)
    
    def __truediv__(self, scalar):
        return self * (1/scalar)
    
    def __neg__(self):
        return self * -1
    
    def magnitude(self):
        return math.sqrt(self.x ** 2 + self.y ** 2)
    
    def asUnitVector(self):
        return Vector2d(self.x / self.magnitude(), self.y / self.magnitude())
    
    def dotWith(self, vector2):
        return self.x * vector2.x + self.y * vector2.y
    
    def angleBetween(self, vector2):
        dot_product = self.dotWith(vector2)
        norm_u = self.magnitude()
        norm_v = vector2.magnitude()
        cos_theta = dot_product / (norm_u * norm_v)
        angle_rad = math.acos(cos_theta)
        return angle_rad
    
    def flip(self):
        return -self
    
    def perpendicularUnit(self):
        return Vector2d(-self.y, self.x).asUnitVector()
    
    def addToPoint(self, point:list):
        return [point[0] + self.x, point[1] + self.y]
    
    def calcSlope(self):
        try:
            return self.y/self.x
        except:
            return "undefined"
        
    def getAngle(self):
        return math.atan2(self.y, self.x)
    
    def toLine(self, point):
        p1 = point
        p2 = self.addToPoint(point)
        a = (p1[1] - p2[1])
        b = (p2[0] - p1[0])
        c = -(p1[0]*p2[1] - p2[0]*p1[1])

        return Line(a,b,c)
    


    @staticmethod
    def fromPoints(start: list, end: list):
        return Vector2d(end[0] - start[0], end[1] - start[1])
    @staticmethod
    def fromPolar(angle, magnitude = 1):
        return Vector2d(math.cos(angle) * magnitude, math.sin(angle) * magnitude)


class Line():
    a,b,c = 0,0,0

    def __init__(self, a, b, c):
        self.a = a
        self.b = b
        self.c = c

    def intersectionWith(self, line):
        Dx = self.c * line.b - self.b * line.c
        D  = self.a * line.b - self.b * line.a
        Dy = self.a * line.c - self.c * line.a
        if D != 0:
            x = Dx / D
            y = Dy / D
            return [x,y]
        else:
            return False


