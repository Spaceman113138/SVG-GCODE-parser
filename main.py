import SVGparser
import pyperclip

path = "testSVG/python-16-svgrepo-com.svg"

pyperclip.copy(SVGparser.parseSVG(path, 300, [0,0]))
