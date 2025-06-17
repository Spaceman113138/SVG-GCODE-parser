import SVGparser
import pyperclip

path = "testSVG\\microscope-2-svgrepo-com.svg"

pyperclip.copy(SVGparser.parseSVG(path))
