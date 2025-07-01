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
    plt.imshow(np.array(pixleData).reshape((height, width, 4)))
    plt.show()





def parseData(data: bytes, channels, bytesPerLine: int, depth, colortype):
    reconstructedLines = reconstructData(data, int(channels), int(depth), int(bytesPerLine))
    combinedData: bytearray = bytearray.fromhex("")
    for line in reconstructedLines:
        combinedData += line # type: ignore
    
    depth = depth / 8

    pixleData = []
    match channels:
        case 4:
            formatString = "BBBB" if depth == 8 else "HHHH"
            while len(combinedData) > 0:
                r,g,b,a = struct.unpack(formatString, combinedData[0:4 * depth])
                combinedData = combinedData = combinedData[4 * depth:]
                pixleData.append([r,g,b,a])
        case 3:
            formatString = "BBB" if depth == 8 else "HHH"
            while len(combinedData) > 0:
                r,g,b = struct.unpack(formatString, combinedData[0:3 * depth])
                combinedData = combinedData[3 * depth:]
                pixleData.append([r,g,b,255])
        case 2:
            formatString = "BB" if depth == 8 else "HH"
            while len(combinedData) > 0:
                w,a = struct.unpack(formatString, combinedData[0:2 * depth])
                combinedData = combinedData[2 * depth:]
                pixleData.append([w,w,w,a])
        case _:
            raise Exception("I should really implement this")
        
    return pixleData

    


def reconstructData(data, channels: int, depth, bytesPerLine:int):
    if depth < 8:
        raise Exception("CRY cuz bits hard to deal with :(")
    if depth > 8:
        raise Exception("Cry less cuz easier :)")
    
    depthOffset: int = int(depth / 8) #use to control offset because depth 16 uses 2 bytes
    step = channels * depthOffset

    #split into lines to make easier to deal with
    lines: list[bytearray] = []
    while len(data) > 0:
        lines.append(bytearray(data[0:int(bytesPerLine)]))
        data = data[int(bytesPerLine):]

    reconstructedLines: list[bytearray] = []

    for line in lines:
        filter = line.pop(0)
        newLine: bytearray = bytearray.fromhex("")
        match filter:
            case 0:
                reconstructedLines.append(line)
            case 1:
                i: int = 0
                while i < len(line):
                    x = line[i]
                    a = 0 if i < step else newLine[i - step]
                    newLine.append((x + a) % 256)
                    i += depthOffset
                reconstructedLines.append(newLine)
            case 2:
                i = 0
                while i < len(line):
                    x = line[i]
                    b = 0 if len(reconstructedLines) == 0 else reconstructedLines[-1][i]
                    newLine.append((x + b) % 256)
                    i += depthOffset
                reconstructedLines.append(newLine)
            case 3:
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
                while i < len(line):
                    x = line[i]
                    a = 0 if i < step else newLine[i-step]
                    b = 0 if len(reconstructedLines) == 0 else reconstructedLines[-1][i]
                    c = 0 if len(reconstructedLines) == 0 or i < step else reconstructedLines[-1][i-step]
                    newLine.append((x + PaethReconstruction(a,b,c)) % 256)
                    i += depthOffset
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
















readPNG("testPNG\\basn4a08.png")