import SVGparser
import pyperclip

path = "testSVG\\test.svg"

pyperclip.copy(SVGparser.parseSVG(path, 300, [0,0]))
