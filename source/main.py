import SVGparser
import pyperclip
import tkinter as tk
import customtkinter as ctk
from tkinter.filedialog import askopenfilename, askdirectory

# path = "testSVG\\test.svg"
# pyperclip.copy(SVGparser.parseSVG(path, 300, [0,0]))

printBedSize = 200
drawingScale = 1.0
lines = []

def openSVG(textbox: ctk.CTkTextbox, image: ctk.CTkCanvas):
    global lines
    file = askopenfilename(filetypes=[("svg", "svg")])
    if file == "":
        return
    result = SVGparser.parseSVG(file, printBedSize, [printBedSize/2, printBedSize/2])
    pyperclip.copy(result[0])

    textbox.delete("0.0", "end")
    textbox.insert("0.0", result[0])  # insert at line 0 character 0

    lines = []
    for line in result[1]:
        points = []
        for i in range(len(line)):
            if str(line[i][0]).isalpha():
                pass
            else:
                points.append(line[i])
        lines.append(points)

    redrawCanvas(image)


def saveGcode():
    directory = askdirectory()


def getCanvasCenter(canvas: ctk.CTkCanvas) -> tuple:
    app.update()
    width: float = canvas.winfo_width()
    height: float= canvas.winfo_height()

    #print(width, height)
    return (width/2, height/2)


def redrawCanvas(canvas: ctk.CTkCanvas):
    center = getCanvasCenter(canvas)

    smallest = min(center[0] * 2, center[1] * 2)
    desiredSize = smallest - 100
    scale = desiredSize / 200

    canvas.delete("all")
    p1 = (center[0] - desiredSize/2, center[1] - desiredSize/2)
    p2 = (center[0] + desiredSize/2, center[1] + desiredSize/2)
    print(p1, p2)
    canvas.create_rectangle(p1[0], p1[1], p2[0], p2[1], width = 4, outline="#2400c5")

    for line in lines:
        for i in range(len(line) - 1):
            canvas.create_line(line[i][0] + center[0], line[i][1] + center[1], line[i+1][0] + center[0], line[i+1][1] + center[1], fill="#ffffff")


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


xAdjFrame = ctk.CTkFrame(app, corner_radius=10, width = 50)
xAdjFrame.grid_columnconfigure((0), weight=0)
xAdjFrame.grid_columnconfigure(1, weight=10)
xAdjFrame.grid(row = 1, column = 0, padx = 30, pady = 10, sticky = "EW")
xAdjLabel = ctk.CTkLabel(xAdjFrame, corner_radius = 10, text="Translate X: ", width = 10)
xAdjLabel.grid(row=0, column=0, padx = (10,0), pady = 10)
xAdj = ctk.CTkEntry(xAdjFrame, width = 50)
xAdj.grid(row = 0, column = 1, padx = (0,10), pady = 10, sticky = "EW")


yAdjFrame = ctk.CTkFrame(app, corner_radius=10, width = 50)
xAdjFrame.grid_columnconfigure((0), weight=0)
xAdjFrame.grid_columnconfigure(1, weight=10)
yAdjFrame.grid(row = 1, column = 1, padx = 30, pady = 10, sticky = "EW")
yAdjLabel = ctk.CTkLabel(yAdjFrame, corner_radius=10, text="Y Translate: ", width = 10)
yAdjLabel.grid(row=0, column=0, padx = (10,0), pady = 10)
yAdj = ctk.CTkEntry(yAdjFrame, width=50)
yAdj.grid(row = 0, column = 1, padx = (0,10), pady = 10, sticky = "EW")


scaleFrame = ctk.CTkFrame(app, corner_radius=10, width = 50)
scaleFrame.grid_columnconfigure((0), weight=0)
scaleFrame.grid_columnconfigure(1, weight=10)
scaleFrame.grid(row = 2, column = 0, padx = 30, pady = 10, sticky = "EW")
scaleLabel = ctk.CTkLabel(scaleFrame, corner_radius = 10, text="Scale: ", width = 10)
scaleLabel.grid(row=0, column=0, padx = (10,0), pady = 10, sticky = "EW")
scale = ctk.CTkEntry(scaleFrame, width = 50)
scale.grid(row = 0, column = 1, padx = (0,10), pady = 10, sticky = "EW")


rotateFrame = ctk.CTkFrame(app, corner_radius=10, width = 50)
rotateFrame.grid_columnconfigure((0), weight=0)
rotateFrame.grid_columnconfigure(1, weight=10)
rotateFrame.grid(row = 2, column = 1, padx = 30, pady = 10, sticky = "WE")
rotateLabel = ctk.CTkLabel(rotateFrame, corner_radius = 10, text="Rotate: ", width = 10)
rotateLabel.grid(row=0, column=0, padx = (10,0), pady = 10, sticky="EW")
rotate = ctk.CTkEntry(rotateFrame, width = 50)
rotate.grid(row = 0, column = 1, padx = (0,10), pady = 10, sticky = "EW")


saveButton = ctk.CTkButton(app, corner_radius = 10, text = "Save Gcode", command = saveGcode, width = 50)
saveButton.grid(row = 3, column = 0, columnspan = 2, padx = 30, pady = 10, sticky = "EW")

textFrame = ctk.CTkTextbox(app, wrap = "none", width = 50, text_color="#ffffff")
textFrame.grid(row = 4, column = 0, columnspan = 2, padx = 30, pady = 10, sticky = "NSEW")

drawFrame = ctk.CTkCanvas(app)
drawFrame.configure(bg="#323232", background="#323232", highlightcolor="#323232")
drawFrame.grid(row = 0, column = 2, padx = 50, pady = 20, rowspan = 5, sticky = "NSEW")
redrawCanvas(drawFrame)

app.bind("<Configure>", lambda event:redrawCanvas(drawFrame))
openButton.configure(command = openSVG(textFrame, drawFrame))

app.mainloop()