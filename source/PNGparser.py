import struct
from zlib_ng import zlib_ng
import math
import matplotlib.pyplot as plt
import numpy as np
import cv2 as cv

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
    
    pallet = []

    if colorType == 3:
        for chunk in chunks:
            if chunk["type"] == "PLTE":
                pallet = parsePallet(chunk["data"])

    pixleData = parseData(allData, channels, perRow, bitDepth, colorType, pallet, (width, height))

    #cv.imshow("image.png", arrayForm)
    dst =  cv.Canny(pixleData, 100, 200) # type: ignore
    
    cst, hierarchy = cv.findContours(dst, cv.RETR_FLOODFILL, cv.CHAIN_APPROX_SIMPLE)

    final = cv.drawContours(dst, cst, -1, (0, 255, 0), 3)
    
    cv.imshow("Source", pixleData) #type: ignore
    cv.imshow("Contours", final)
    
    cv.waitKey()


    # plt.subplot(121),plt.imshow(pixleData,cmap = 'gray') # type: ignore
    # plt.title('Original Image'), plt.xticks([]), plt.yticks([]) # type: ignore
    # plt.subplot(122),plt.imshow(edges,cmap = 'gray') # type: ignore
    # plt.title('Edge Image'), plt.xticks([]), plt.yticks([]) # type: ignore

    # plt.show()

    # #print(reconstructedData)
    # fig, ax = plt.subplots()
    # ax.imshow(arrayForm)
    # ax.set_facecolor("black")
    # plt.show()


def parseBytesToInts(line:bytes, depth: int) -> list[int]:
    values: list[int] = []

    match depth:
        case 1:
            for byte in line:
                byte = int(byte)
                values.append(byte >> 7 & 0b1) #grab left most bit
                values.append(byte >> 6 & 0b1) #grab next leftmost bit
                values.append(byte >> 5 & 0b1)
                values.append(byte >> 4 & 0b1)
                values.append(byte >> 3 & 0b1)
                values.append(byte >> 2 & 0b1)
                values.append(byte >> 1 & 0b1)
                values.append(byte & 0b1)
        case 2:
            for byte in line:
                byte = int(byte)
                values.append(byte >> 6 & 0b11) #grab left 2 bits
                values.append(byte >> 4 & 0b11) #grab next 2 bits
                values.append(byte >> 2 & 0b11)
                values.append(byte & 0b11)
        case 4:
            for byte in line:
                byte = int(byte)
                values.append(byte >> 4 & 0b1111) #grab left 4 bits
                values.append(byte & 0b1111)#grab right 4 bits
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


def parseData(data: bytes, channels, bytesPerLine: int, depth, colortype, pallet, size):
    reconstructedLines: list[bytes] = reconstructData(data, int(channels), int(depth), int(bytesPerLine))

    combinedData: list[int] = []

    for line in reconstructedLines:
        combinedData.extend(parseBytesToInts(line, depth))
    
    depthByte = int(depth / 8)
    adjustment = 255 / ((2 ** depth) - 1)

    pixleData = []
    match channels:
        case 4:
            return np.array(combinedData, np.uint8).reshape((size[1], size[0], 4))
            while len(combinedData) > 0:
                print(len(combinedData))
                pixleData.append(combinedData.pop(0))

                # r,g,b,a = combinedData[0: 4]
                # combinedData = combinedData[4:]
                # r = int(r / adjustment)
                # g = int(g / adjustment)
                # b = int(b / adjustment)
                # a = int(a / adjustment)

                # pixleData.append([r,g,b,a])

        case 3:
            return np.array(combinedData, np.uint8).reshape((size[1], size[0], 3))
        case 2:
            return np.array(combinedData, np.uint8).reshape((size[1], size[0], 2))
        case 1 if colortype == 0:
            while len(combinedData) > 0:
                return np.array(combinedData, np.uint8).reshape((size[1], size[0], 1))
        case 1 if colortype == 3:
            while len(combinedData) > 0:
                index = combinedData.pop(0)
                pixleData.append(pallet[index])
            return np.array(pixleData, np.uint8).reshape((size[1], size[0], 4))
        case _:
            raise Exception("I should really implement this")

        
    return pixleData


def parsePallet(data: bytes):
    data = bytearray(data)

    pallet = []

    if len(data) % 3 != 0:
        raise Exception("Must be a multiple of 3")

    while len(data) != 0:
        r = int(data.pop(0))
        g = int(data.pop(0))
        b = int(data.pop(0))
        a = 255
        pallet.append([r,g,b,a])

    return pallet


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
                for i in range(len(line)):
                    x = line[i]
                    a = 0 if i < bpp else newLine[i - bpp]
                    b = 0 if len(reconstructedLines) == 0 else reconstructedLines[-1][i]
                    newValue = (x + math.floor((a + b) / 2)) % 256
                    newLine += newValue.to_bytes(1)
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




readPNG("testPNG\\defiltered.png")