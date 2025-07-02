import struct
from zlib_ng import zlib_ng
import math
import matplotlib.pyplot as plt
import numpy as np

def readPNG(path: str):
    file = open(path, "rb")
    text = file.read()

    validHeader = text.startswith(b"\x89\x50\x4e\x47\x0d\x0a\x1a\x0a")
    if not validHeader:
        raise Exception("invalid header")
    else:
        text = text.removeprefix(b"\x89\x50\x4e\x47\x0d\x0a\x1a\x0a")

    chunks = []
    while len(text) > 0:
        chunk = {}
        chunk["length"] = int.from_bytes(text[0:4], "big")
        chunk["type"] = text[4:8].decode("ascii")
        chunk["data"] = text[8:8 + chunk["length"]]
        chunk["crc"] = text[8 + chunk["length"]: 8 + chunk["length"] + 4]
        chunks.append(chunk)
        text = text[8 + chunk["length"] + 4:]

    if chunks[0]["type"] != "IHDR":
        raise Exception("IDHR must be first chunk")
    
    width, height, bitDepth, colorType = parseIDHR(chunks[0])

    allData = b''

    for chunk in chunks:
        if chunk["type"] == "IDAT":
            allData += chunk["data"]

    allData = zlib_ng.decompress(allData)
    expectedDataSize, perRow, channels = getExpectedDataSize(width, height, colorType, bitDepth)
    if expectedDataSize != len(allData):
        print(len(allData))
        raise Exception("Data is not of expepcted size")
    
    pixleData = parseData(allData, channels, perRow, bitDepth, colorType)

    #print(reconstructedData)
    fig, ax = plt.subplots()
    ax.imshow(np.array(pixleData).reshape((height, width, 4)))
    ax.set_facecolor("black")
    plt.show()


def parseBytesToInts(line:bytes, depth: int) -> list[int]:
    values: list[int] = []

    match depth:
        case 8:
            for byte in line:
                values.append(int(byte))
        case 16:
            for i in range(int(len(line) / 2)):
                thing = struct.unpack(">H", line[i*2:(i+1)*2])
                values.append(int(thing[0]))
        case _:
            raise Exception("Not implemented or valid")

    return values 


def parseData(data: bytes, channels, bytesPerLine: int, depth, colortype):
    reconstructedLines: list[bytes] = reconstructData(data, int(channels), int(depth), int(bytesPerLine))

    combinedData: list[int] = []

    for line in reconstructedLines:
        combinedData.extend(parseBytesToInts(line, depth))
    
    depthByte = int(depth / 8)
    adjustment = 255 / ((2 ** depth) - 1)

    pixleData = []
    match channels:
        case 4:
            while len(combinedData) > 0:
                r,g,b,a = combinedData[0: 4]
                combinedData = combinedData[4:]
                r = int(r / adjustment)
                g = int(g / adjustment)
                b = int(b / adjustment)
                a = int(a / adjustment)

                pixleData.append([r,g,b,a])

        case 3:
            while len(combinedData) > 0:
                r,g,b, = combinedData[0: 3]
                combinedData = combinedData[3:]
                r = int(r * adjustment)
                g = int(g * adjustment)
                b = int(b * adjustment)

                pixleData.append([r,g,b,255])
        case 2:
            while len(combinedData) > 0:
                w,a = combinedData[0:2]
                combinedData = combinedData[2:]
                w = int(w * adjustment)
                a = int(a * adjustment)
                
                pixleData.append([w,w,w,a])
        case 1 if colortype == 0:
            while len(combinedData) > 0:
                w = combinedData.pop(0)
                w = int(w * adjustment)

                pixleData.append([w,w,w,255])
        case _:
            raise Exception("I should really implement this")

        
    return pixleData


def reconstructData(data, channels: int, depth, bytesPerLine:int):
    
    depthOffset: int = int(depth / 8) #use to control offset because depth 16 uses 2 bytes
    bpp = math.ceil(channels * depthOffset)

    #split into lines to make easier to deal with
    values:list[bytes] = []
    while len(data) > 0:
        line = data[0: bytesPerLine]
        data = data[bytesPerLine:]
        values.append(line)
        #values.append(parseBytesToInts(line, depth))

    reconstructedLines: list[bytes] = []

    for line in values:
        filter = line[0]
        line = line[1:]
        newLine: bytes = b""
        print(filter)
        match filter:
            case 0:
                reconstructedLines.append(line)
            case 1:
                for i in range(len(line)):
                    x = line[i]
                    a = 0 if i < bpp else newLine[i-bpp]
                    newValue = (x + a) % 256
                    newLine += newValue.to_bytes(1)
                reconstructedLines.append(newLine)
            case 2:
                for i in range(len(line)):
                    x = line[i]
                    b = 0 if len(reconstructedLines) == 0 else reconstructedLines[-1][i]
                    newValue = (x + b) % 256
                    newLine += newValue.to_bytes(1)
                reconstructedLines.append(newLine)
            case 3:
                raise Exception("All wrong")
                i = 0
                while i < len(line):
                    x = line[i]
                    a = 0 if i < step else newLine[i - step]
                    b = 0 if len(reconstructedLines) == 0 else reconstructedLines[-1][i]
                    newValue = x + math.floor((a + b) / 2) % 256
                    newLine.append(newValue)
                    i += depthOffset
                reconstructedLines.append(newLine)
            case 4:
                i = 0
                print(line)
                while i < len(line):
                    x = line[i]
                    a = 0 if i < bpp else newLine[i-bpp]
                    b = 0 if len(reconstructedLines) == 0 else reconstructedLines[-1][i]
                    c = 0 if i < bpp or len(reconstructedLines) == 0 else reconstructedLines[-1][i-bpp]
                    value = (x + PaethReconstruction(a, b, c)) % 256
                    newLine += value.to_bytes(1)
                    i += 1
                reconstructedLines.append(newLine)
            case _:
                raise Exception("Invalid Filter")

    return reconstructedLines




def PaethReconstruction(a, b, c):
    p = a + b - c
    pa = abs(p-a)
    pb = abs(p-b)
    pc = abs(p-c)
    
    if pa <= pb and pa <= pc:
        pr = a
    elif pb <= pc:
        pr = b
    else:
        pr = c
    return pr

def getExpectedDataSize(width, height, colorType, bitDepth):
    bitsPerPix = bitDepth
    channels = 0
    match colorType:
        case 0 | 3:
            channels = 1
            bitsPerPix *= 1
        case 4:
            channels = 2
            bitsPerPix *= 2
        case 2:
            channels = 3
            bitsPerPix *= 3
        case 6:
            channels = 4
            bitsPerPix *= 4
        case _:
            raise Exception("Invalid Color Type")
    
    bytesPerPixel = bitsPerPix / 8

    return height * (1 + width * bytesPerPixel), (1 + width * bytesPerPixel), channels


def parseIDHR(idhrChunk: dict):
    data: bytes = idhrChunk["data"]

    width, height, bitDepth, colorType, compressionMethod, filterMethod, interlace = struct.unpack(">IIBBBBB", data)

    if filterMethod != 0:
        raise Exception("Filter method must be 0")
    if interlace != 0:
        raise Exception("interlace not supported")
    if compressionMethod != 0:
        raise Exception("Compression type must be 0")
    
    match colorType:
        case 0:
            pass
        case 2 | 4 | 6:
            try:
                [8,16].index(bitDepth)
            except:
                raise Exception("Invalid bit depth")
        case 3:
            try:
                [1,2,4,8].index(bitDepth)
            except:
                raise Exception("Invalid bit depth")
        case _:
            raise Exception("Invalid Color Type")

    return (width, height, bitDepth, colorType)









readPNG("testPNG\\basn0g16.png")