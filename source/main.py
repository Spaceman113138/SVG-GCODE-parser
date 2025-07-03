import SVGparser
import pyperclip
import tkinter as tk
import customtkinter as ctk
from tkinter.filedialog import askopenfilename, askdirectory
import threading
import util
import math

# path = "testSVG\\test.svg"
# pyperclip.copy(SVGparser.parseSVG(path, 300, [0,0]))

printBedSize = 200
drawingScale = 1.0
lines = []
translate = [0,0]
rotate = 0
prevCenter = (0,0)
redraw = False
fileName = ""
filePath = ""

def openSVG(textbox: ctk.CTkTextbox, image: ctk.CTkCanvas, saveButton: ctk.CTkButton):
    global lines, fileName, filePath
    file = askopenfilename(filetypes=[("svg", "svg")])
    if file == "":
        return
    fileName = file.split("\\")[-1].split("/")[-1]
    result = SVGparser.parseSVG(file, printBedSize, [0,0])
    filePath = file

    textbox.configure(state=tk.NORMAL)
    textbox.delete("0.0", "end")
    textbox.insert("0.0", result[0])  # insert at line 0 character 0
    textbox.configure(state=tk.DISABLED)

    saveButton.configure(state=tk.NORMAL)

    lines = []
    for line in result[1]:
        points = []
        for i in range(len(line)):
            if str(line[i][0]).isalpha():
                pass
            else:
                points.append(line[i])
        lines.append(points)

    redrawCanvas(image, True)


def saveGcode(textbox: ctk.CTkTextbox):
    directory = askdirectory()
    file = open(directory + "/" + fileName + ".gcode", "w")
    result = SVGparser.parseSVG(filePath, 100, [printBedSize/2 + translate[0], printBedSize/2 + translate[1]], math.radians(rotate), drawingScale, True)
    file.write(result[0])
    file.close()

    textbox.configure(state=tk.NORMAL)
    textbox.delete("0.0", "end")
    textbox.insert("0.0", result[0])  # insert at line 0 character 0
    textbox.configure(state=tk.DISABLED)


def getCanvasCenter(canvas: ctk.CTkCanvas) -> tuple:
    app.update()
    width: float = canvas.winfo_width()
    height: float= canvas.winfo_height()

    #print(width, height)
    return (width/2, height/2)


def redrawCanvas(canvas: ctk.CTkCanvas, force: bool):
    center = getCanvasCenter(canvas)
    global redraw,drawingScale,rotate

    if not redraw and not force:
        return
    
    redraw = False

    smallest = min(center[0] * 2, center[1] * 2)
    desiredSize = smallest - 100
    scale = desiredSize / 200

    canvas.delete("all")
    p1 = (center[0] - desiredSize/2, center[1] - desiredSize/2)
    p2 = (center[0] + desiredSize/2, center[1] + desiredSize/2)
    canvas.create_rectangle(p1[0], p1[1], p2[0], p2[1], width = 4, outline="#2400c5")

    print(translate)

    for line in lines:
        for i in range(len(line) - 1):
            transform = [translate[0] * scale, -translate[1] * scale]
            point = [line[i][0] * scale, line[i][1]]
            point2 = [line[i+1][1] * scale, line[i][1] * scale]
            point = util.transform(line[i], transform, drawingScale, math.radians(rotate))
            point2 = util.transform(line[i + 1], transform, drawingScale, math.radians(rotate))
            canvas.create_line(point[0] + center[0], point[1] + center[1], point2[0] + center[0], point2[1] + center[1], fill="#ffffff")


def addTempScreen(canvas: ctk.CTkCanvas):
    global prevCenter
    center = getCanvasCenter(canvas)
    
    if lines == []:
        redrawCanvas(canvas, True)
    elif prevCenter != center:
        center = getCanvasCenter(canvas)
        canvas.delete("all")
        canvas.create_text(center[0],center[1], text="click to redraw",width=200)
        global redraw
        redraw = True


    prevCenter = center

def updateXtranslate(x):
    translate[0] = x

def updateYtranslate(y):
    translate[1] = y

def updateScale(scale):
    global drawingScale
    drawingScale = scale

def updateRotation(rot):
    global rotate
    rotate = rot


class NumInput(ctk.CTkFrame):

    def __init__(self, parent, name: str, amount: float, update, redraw, **kwargs):
        super().__init__(parent, **kwargs)

        self.updateFunc = update
        self.redrawFunc = redraw

        self.grid_columnconfigure((0,2), weight=0)
        self.grid_columnconfigure(1, weight=1000)
        self.grid_rowconfigure((0,1), weight=0)

        self.label = ctk.CTkLabel(self, width=10, corner_radius=10, text=name)
        self.label.grid(row=0, column=0, padx=(10,0), pady=10, sticky="EW", rowspan=2)

        self.inputValue: tk.StringVar = tk.StringVar()
        self.inputValue.set("0")
        self.lastGoodValue = 0
        self.input = ctk.CTkEntry(self, width=50, corner_radius=10, textvariable=self.inputValue, placeholder_text="0")
        self.input.grid(row=0, column=1, padx=(0,10), pady=10, sticky="EW", rowspan=2)
        self.input.bind("<FocusOut>", lambda event:self.validateNum())

        self.upButton = ctk.CTkButton(self, width=50, corner_radius=5, text="˄", height=20, command=lambda: self.adjustInput(amount))
        self.upButton.grid(row=0, column=2, padx=5, pady=5, sticky = "N")

        self.downButton = ctk.CTkButton(self, width=50, corner_radius=5, text="˅", height=20, command=lambda: self.adjustInput(-amount))
        self.downButton.grid(row=1, column=2, padx=5, pady=5, sticky = "S")


    def validateNum(self):
        if not util.isNum(self.inputValue.get()):
            self.inputValue.set(str(self.lastGoodValue))
        else:
            self.lastGoodValue = float(self.inputValue.get())
            self.updateFunc(self.lastGoodValue)
            self.redrawFunc()
            

    def adjustInput(self, value:float):
        self.lastGoodValue += value
        self.inputValue.set(str(self.lastGoodValue))
        self.validateNum()




ctk.set_appearance_mode("dark")
app = ctk.CTk()
app.title("SVG Conversion")
app.geometry("1000x500")
app.grid_columnconfigure((0,1), weight=0)
app.grid_columnconfigure((2), weight=1000)
app.grid_rowconfigure((0,1,2,3), weight=0)
app.grid_rowconfigure(4, weight=1000)


openButton = ctk.CTkButton(app, corner_radius=10, text="Open SVG", width = 50)
openButton.grid(row = 0, column = 0, padx = 30, pady = 10, sticky = "EW", columnspan = 2)


drawFrame = ctk.CTkCanvas(app)
drawFrame.configure(bg="#323232", background="#323232", highlightcolor="#323232")
drawFrame.grid(row = 0, column = 2, padx = 50, pady = 20, rowspan = 5, sticky = "NSEW")
redrawCanvas(drawFrame, True)


xAdjFrame = NumInput(app, "Translate X: ", 10, lambda newValue: updateXtranslate(newValue), lambda: redrawCanvas(drawFrame, True))
xAdjFrame.grid(row = 1, column = 0, padx = 30, pady = 10, sticky = "EW")

yAdjFrame = NumInput(app, "Translate Y: ", 10, lambda newValue: updateYtranslate(newValue), lambda: redrawCanvas(drawFrame, True))
yAdjFrame.grid(row = 1, column = 1, padx = 30, pady = 10, sticky = "EW")

scaleFrame = NumInput(app, "Scale: ", 0.25, lambda newValue: updateScale(newValue), lambda: redrawCanvas(drawFrame, True))
scaleFrame.grid(row = 2, column = 0, padx = 30, pady = 10, sticky = "EW")

rotateFrame = NumInput(app, "Rotate: ", 15, lambda newValue: updateRotation(newValue), lambda: redrawCanvas(drawFrame, True))
rotateFrame.grid(row = 2, column = 1, padx = 30, pady = 10, sticky = "WE")


saveButton = ctk.CTkButton(app, corner_radius = 10, text = "Save Gcode", command = lambda: saveGcode(textFrame), width = 50, state=tk.DISABLED)
saveButton.grid(row = 3, column = 0, columnspan = 2, padx = 30, pady = 10, sticky = "EW")

textFrame = ctk.CTkTextbox(app, wrap = "none", width = 50, text_color="#ffffff", state=tk.DISABLED)
textFrame.grid(row = 4, column = 0, columnspan = 2, padx = 30, pady = 10, sticky = "NSEW")

openButton.configure(command = lambda : openSVG(textFrame, drawFrame, saveButton))
app.bind("<ButtonRelease-1>", lambda event: threading.Thread(target=redrawCanvas, args=(drawFrame, False)).start())
app.bind("<Configure>", lambda event: addTempScreen(drawFrame))


app.mainloop()