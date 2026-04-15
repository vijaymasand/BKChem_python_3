# -*- coding: iso-8859-1 -*-
# piddle.py -- Plug In Drawing, Does Little Else
# Copyright (C) 1999  Joseph J. Strout
# 
# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 2 of the License, or (at your option) any later version.
# 
# This library is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# Lesser General Public License for more details.
# 
# You should have received a copy of the GNU Lesser General Public
# License along with this library; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA

"""
PIDDLE (Plug-In Drawing, Does Little Else)
2D Plug-In Drawing System

Magnus Lie Hetland
Andy Robinson
Joseph J. Strout
and others

February-March 1999

On coordinates: units are Big Points, approximately 1/72 inch.
The origin is at the top-left, and coordinates increase down (y)
and to the right (x).

Progress Reports...
JJS, 2/10/99: as discussed, I've removed the Shape classes and moved
        the drawing methods into the Canvas class.  Numerous other changes
        as discussed by email as well.

JJS, 2/11/99: removed Canvas default access functions; added fontHeight
        etc. functions; fixed numerous typos; added drawRect and drawRoundRect
        (how could I forget those?).  Added StateSaver utility class.
        
        2/11/99 (later): minor fixes.

JJS, 2/12/99: removed scaling/sizing references.  Changed event handler
        mechanism per Magnus's idea.  Changed drawCurve into a fillable
        drawing function (needs default implementation).  Removed edgeList
        from drawPolygon.  Added drawFigure.  Changed drawLines to draw
        a set of disconnected lines (of uniform color and width).
        
        2/12/99 (later): added HexColor function and WWW color constants.
        Fixed bug in StateSaver.  Changed params to drawArc.

JJS, 2/17/99: added operator methods to Color; added default implementation
        of drawRoundRect in terms of Line, Rect, and Arc.

JJS, 2/18/99: added isInteractive and canUpdate methods to Canvas.

JJS, 2/19/99: added drawImage method; added angle parameter to drawString.

JJS, 3/01/99: nailed down drawFigure interface (and added needed constants).

JJS, 3/08/99: added arcPoints and curvePoints methods; added default 
        implementations for drawRect, drawRoundRect, drawArc, drawCurve, 
        drawEllipse, and drawFigure (!), mostly thanks to Magnus.

JJS, 3/09/99: added 'closed' parameter to drawPolygon, drawCurve, and
        drawFigure.  Made use of this in several default implementations.

JJS, 3/11/99: added 'onKey' callback and associated constants; also added
        Canvas.setInfoLine(s) method.

JJS, 3/12/99: typo in drawFigure.__doc__ corrected (thanks to Magnus).

JJS, 3/19/99: fixed bug in drawArc (also thanks to Magnus).

JJS, 5/30/99: fixed bug in arcPoints.

JJS, 6/10/99: added __repr__ method to Font.

JJS, 6/22/99: added additional WWW colors thanks to Rafal Smotrzyk

JJS, 6/29/99: added inch and cm units

JJS, 6/30/99: added size & name parameters to Canvas.__init__

JJS, 9/21/99: fixed bug in arcPoints

JJS, 9/29/99: added drawMultiLineStrings, updated fontHeight with new definition

JJS, 10/21/99: made Color immutable; fixed bugs in default fontHeight,
                drawMultiLineString
"""

__version_maj_number__ = 1.0 
__version_min_number__ = 15  
__version__ = "%s.%s" % ( __version_maj_number__,  __version_min_number__) # c.f. "1.0.15"

pass  # types removed (use str), str, int, object
import string

inch = 72               # 1 PIDDLE drawing unit == 1/72 imperial inch
cm = inch/2.54  # more sensible measurement unit

#-------------------------------------------------------------------------
# StateSaver
#-------------------------------------------------------------------------
class StateSaver:
        """This is a little utility class for saving and restoring the
        default drawing parameters of a canvas.  To use it, add a line
        like this before changing any of the parameters:
        
                saver = StateSaver(myCanvas)
        
        then, when "saver" goes out of scope, it will automagically
        restore the drawing parameters of myCanvas."""

        def __init__(self, canvas):
                self.canvas = canvas
                self.defaultLineColor = canvas.defaultLineColor
                self.defaultFillColor = canvas.defaultFillColor
                self.defaultLineWidth = canvas.defaultLineWidth
                self.defaultFont = canvas.defaultFont
        
        def __del__(self):
                self.canvas.defaultLineColor = self.defaultLineColor
                self.canvas.defaultFillColor = self.defaultFillColor
                self.canvas.defaultLineWidth = self.defaultLineWidth
                self.canvas.defaultFont = self.defaultFont

#-------------------------------------------------------------------------
# Color
#-------------------------------------------------------------------------
class Color:
        """This class is used to represent color.  Components red, green, blue 
        are in the range 0 (dark) to 1 (full intensity)."""

        def __init__(self, red=0, green=0, blue=0):
                "Initialize with red, green, blue in range [0-1]."
                _float = float
                d = self.__dict__
                d["red"] = _float(red)
                d["green"] = _float(green)
                d["blue"] = _float(blue)

        def __setattr__(self, name, value):
                raise TypeError("piddle.Color has read-only attributes")

        def __mul__(self,x):
                return Color(self.red*x, self.green*x, self.blue*x)
        
        def __rmul__(self,x):
                return Color(self.red*x, self.green*x, self.blue*x)
        
        def __div__(self,x):
                return Color(self.red/x, self.green/x, self.blue/x)
        
        def __rdiv__(self,x):
                return Color(self.red/x, self.green/x, self.blue/x)
        
        def __add__(self,x):
                return Color(self.red+x.red, self.green+x.green, self.blue+x.blue)
                
        def __sub__(self,x):
                return Color(self.red-x.red, self.green-x.green, self.blue-x.blue)
                
        def __repr__(self):
                return "Color(%1.2f,%1.2f,%1.2f)" % (self.red, self.green, self.blue)

        def __hash__(self):
                return hash( (self.red, self.green, self.blue) )
                
        def __eq__(self, other):
                if not isinstance(other, Color):
                        return False
                return self.red == other.red and self.green == other.green and self.blue == other.blue

        def __lt__(self, other):
                if not isinstance(other, Color):
                        return NotImplemented
                dsum = 4*self.red-4*other.red + 2*self.green-2*other.green + self.blue-other.blue
                return dsum < 0
                
def HexColor(val):
        """This class converts a hex string, or an actual integer number,
        into the corresponding color.  E.g., in "AABBCC" or 0xAABBCC,
        AA is the red, BB is the green, and CC is the blue (00-FF)."""
        if isinstance(val, str):
                val = int(val, 16)
        factor = 1.0 / 255
        return Color(factor * ((val >> 16) & 0xFF), 
                          factor * ((val >> 8) & 0xFF),
                          factor * (val & 0xFF))
                
# color constants -- mostly from HTML standard
aliceblue =     HexColor(0xF0F8FF)
antiquewhite =  HexColor(0xFAEBD7)
aqua =  HexColor(0x00FFFF)
aquamarine =    HexColor(0x7FFFD4)
azure =         HexColor(0xF0FFFF)
beige =         HexColor(0xF5F5DC)
bisque =        HexColor(0xFFE4C4)
black =         HexColor(0x000000)
blanchedalmond =        HexColor(0xFFEBCD)
blue =  HexColor(0x0000FF)
blueviolet =    HexColor(0x8A2BE2)
brown =         HexColor(0xA52A2A)
burlywood =     HexColor(0xDEB887)
cadetblue =     HexColor(0x5F9EA0)
chartreuse =    HexColor(0x7FFF00)
chocolate =     HexColor(0xD2691E)
coral =         HexColor(0xFF7F50)
cornflower =    HexColor(0x6495ED)
cornsilk =      HexColor(0xFFF8DC)
crimson =       HexColor(0xDC143C)
cyan =  HexColor(0x00FFFF)
darkblue =      HexColor(0x00008B)
darkcyan =      HexColor(0x008B8B)
darkgoldenrod =         HexColor(0xB8860B)
darkgray =      HexColor(0xA9A9A9)
darkgreen =     HexColor(0x006400)
darkkhaki =     HexColor(0xBDB76B)
darkmagenta =   HexColor(0x8B008B)
darkolivegreen =        HexColor(0x556B2F)
darkorange =    HexColor(0xFF8C00)
darkorchid =    HexColor(0x9932CC)
darkred =       HexColor(0x8B0000)
darksalmon =    HexColor(0xE9967A)
darkseagreen =  HexColor(0x8FBC8B)
darkslateblue =         HexColor(0x483D8B)
darkslategray =         HexColor(0x2F4F4F)
darkturquoise =         HexColor(0x00CED1)
darkviolet =    HexColor(0x9400D3)
deeppink =      HexColor(0xFF1493)
deepskyblue =   HexColor(0x00BFFF)
dimgray =       HexColor(0x696969)
dodgerblue =    HexColor(0x1E90FF)
firebrick =     HexColor(0xB22222)
floralwhite =   HexColor(0xFFFAF0)
forestgreen =   HexColor(0x228B22)
fuchsia =       HexColor(0xFF00FF)
gainsboro =     HexColor(0xDCDCDC)
ghostwhite =    HexColor(0xF8F8FF)
gold =  HexColor(0xFFD700)
goldenrod =     HexColor(0xDAA520)
gray =  HexColor(0x808080)
grey = gray
green =         HexColor(0x008000)
greenyellow =   HexColor(0xADFF2F)
honeydew =      HexColor(0xF0FFF0)
hotpink =       HexColor(0xFF69B4)
indianred =     HexColor(0xCD5C5C)
indigo =        HexColor(0x4B0082)
ivory =         HexColor(0xFFFFF0)
khaki =         HexColor(0xF0E68C)
lavender =      HexColor(0xE6E6FA)
lavenderblush =         HexColor(0xFFF0F5)
lawngreen =     HexColor(0x7CFC00)
lemonchiffon =  HexColor(0xFFFACD)
lightblue =     HexColor(0xADD8E6)
lightcoral =    HexColor(0xF08080)
lightcyan =     HexColor(0xE0FFFF)
lightgoldenrodyellow =  HexColor(0xFAFAD2)
lightgreen =    HexColor(0x90EE90)
lightgrey =     HexColor(0xD3D3D3)
lightpink =     HexColor(0xFFB6C1)
lightsalmon =   HexColor(0xFFA07A)
lightseagreen =         HexColor(0x20B2AA)
lightskyblue =  HexColor(0x87CEFA)
lightslategray =        HexColor(0x778899)
lightsteelblue =        HexColor(0xB0C4DE)
lightyellow =   HexColor(0xFFFFE0)
lime =  HexColor(0x00FF00)
limegreen =     HexColor(0x32CD32)
linen =         HexColor(0xFAF0E6)
magenta =       HexColor(0xFF00FF)
maroon =        HexColor(0x800000)
mediumaquamarine =      HexColor(0x66CDAA)
mediumblue =    HexColor(0x0000CD)
mediumorchid =  HexColor(0xBA55D3)
mediumpurple =  HexColor(0x9370DB)
mediumseagreen =        HexColor(0x3CB371)
mediumslateblue =       HexColor(0x7B68EE)
mediumspringgreen =     HexColor(0x00FA9A)
mediumturquoise =       HexColor(0x48D1CC)
mediumvioletred =       HexColor(0xC71585)
midnightblue =  HexColor(0x191970)
mintcream =     HexColor(0xF5FFFA)
mistyrose =     HexColor(0xFFE4E1)
moccasin =      HexColor(0xFFE4B5)
navajowhite =   HexColor(0xFFDEAD)
navy =  HexColor(0x000080)
oldlace =       HexColor(0xFDF5E6)
olive =         HexColor(0x808000)
olivedrab =     HexColor(0x6B8E23)
orange =        HexColor(0xFFA500)
orangered =     HexColor(0xFF4500)
orchid =        HexColor(0xDA70D6)
palegoldenrod =         HexColor(0xEEE8AA)
palegreen =     HexColor(0x98FB98)
paleturquoise =         HexColor(0xAFEEEE)
palevioletred =         HexColor(0xDB7093)
papayawhip =    HexColor(0xFFEFD5)
peachpuff =     HexColor(0xFFDAB9)
peru =  HexColor(0xCD853F)
pink =  HexColor(0xFFC0CB)
plum =  HexColor(0xDDA0DD)
powderblue =    HexColor(0xB0E0E6)
purple =        HexColor(0x800080)
red =   HexColor(0xFF0000)
rosybrown =     HexColor(0xBC8F8F)
royalblue =     HexColor(0x4169E1)
saddlebrown =   HexColor(0x8B4513)
salmon =        HexColor(0xFA8072)
sandybrown =    HexColor(0xF4A460)
seagreen =      HexColor(0x2E8B57)
seashell =      HexColor(0xFFF5EE)
sienna =        HexColor(0xA0522D)
silver =        HexColor(0xC0C0C0)
skyblue =       HexColor(0x87CEEB)
slateblue =     HexColor(0x6A5ACD)
slategray =     HexColor(0x708090)
snow =  HexColor(0xFFFAFA)
springgreen =   HexColor(0x00FF7F)
steelblue =     HexColor(0x4682B4)
tan =   HexColor(0xD2B48C)
teal =  HexColor(0x008080)
thistle =       HexColor(0xD8BFD8)
tomato =        HexColor(0xFF6347)
turquoise =     HexColor(0x40E0D0)
violet =        HexColor(0xEE82EE)
wheat =         HexColor(0xF5DEB3)
white =         HexColor(0xFFFFFF)
whitesmoke =    HexColor(0xF5F5F5)
yellow =        HexColor(0xFFFF00)
yellowgreen =   HexColor(0x9ACD32)

# special case -- indicates no drawing should be done
transparent = Color(-1, -1, -1)

#-------------------------------------------------------------------------
# Font
#-------------------------------------------------------------------------
class Font:
    "This class represents font typeface, size, and style."
        
    def __init__(self, size=12, bold=0, italic=0, underline=0, face=None):
        # public mode variables
        d = self.__dict__
        d["bold"] = bold
        d["italic"] = italic
        d["underline"] = underline

        # public font size (points)
        d["size"] = size

        # typeface -- a name or set of names, interpreted by the Canvas,
        # or "None" to indicate the Canvas-specific default typeface
        d["face"] = face
        
    def __eq__(self, other):
        """Compare two fonts to see if they're the same."""
        if not isinstance(other, Font):
            return False
        return self.face == other.face and self.size == other.size and \
           self.bold == other.bold and self.italic == other.italic \
           and self.underline == other.underline

    def __repr__(self):
        return "Font(%d,%d,%d,%d,%s)" % (self.size, self.bold, self.italic, \
                                         self.underline, repr(self.face))

    def __setattr__(self, name, value):
        raise TypeError("piddle.Font has read-only attributes")


#-------------------------------------------------------------------------
# constants needed for Canvas.drawFigure
#-------------------------------------------------------------------------
figureLine = 1
figureArc = 2
figureCurve = 3

#-------------------------------------------------------------------------
# key constants used for special keys in the onKey callback
#-------------------------------------------------------------------------
keyBksp = '\010'                # (erases char to left of cursor)
keyDel = '\177'                 # (erases char to right of cursor)
keyLeft = '\034'
keyRight = '\035'
keyUp = '\036'
keyDown = '\037'
keyPgUp = '\013'
keyPgDn = '\014'
keyHome = '\001'
keyEnd = '\004'
keyClear = '\033'
keyTab = '\t'

modShift = 1            # shift key was also held
modControl = 2          # control key was also held

#-------------------------------------------------------------------------
# Canvas
#-------------------------------------------------------------------------
class Canvas:
        """This is the base class for a drawing canvas.  The 'plug-in renderers'
        we speak of are really just classes derived from this one, which implement
        the various drawing methods."""
        
        def __init__(self, size=(300,300), name="PIDDLE"):
                """Initialize the canvas, and set default drawing parameters. 
                Derived classes should be sure to call this method."""
                # defaults used when drawing
                self.defaultLineColor = black
                self.defaultFillColor = transparent
                self.defaultLineWidth = 1
                self.defaultFont = Font()

                # set up null event handlers
                
                # onClick: x,y is Canvas coordinates of mouseclick
                def ignoreClick(canvas,x,y): pass
                self.onClick = ignoreClick

                # onOver: x,y is Canvas location of mouse
                def ignoreOver(canvas,x,y): pass
                self.onOver = ignoreOver

                # onKey: key is printable character or one of the constants above;
                #       modifiers is a tuple containing any of (modShift, modControl)
                def ignoreKey(canvas,key,modifiers): pass
                self.onKey = ignoreKey

                # size and name, for user's reference
                self.size, self.name = size,name

        #------------ canvas capabilities -------------
        def isInteractive(self):
                "Returns 1 if onClick, onOver, and onKey events are possible, 0 otherwise."
                return 0
        
        def canUpdate(self):
                "Returns 1 if the drawing can be meaningfully updated over time \
                (e.g., screen graphics), 0 otherwise (e.g., drawing to a file)."
                return 0

        #------------ general management -------------
        def clear(self):
                "Call this to clear and reset the graphics context."
                pass
                
        def flush(self):
                "Call this to indicate that any comamnds that have been issued \
                but which might be buffered should be flushed to the screen"
                pass

        def save(self, file=None, format=None):

                """For backends that can be save to a file or sent to a
                stream, create a valid file out of what's currently been
                drawn on the canvas.  Trigger any finalization here.
                Though some backends may allow further drawing after this call,
                presume that this is not possible for maximum portability

                file may be either a string or a file object with a write method
                     if left as the default, the canvas's current name will be used

                format may be used to specify the type of file format to use as
                     well as any corresponding extension to use for the filename
                     This is an optional argument and backends may ignore it if
                     they only produce one file format."""
                pass 

                                
        
        def setInfoLine(self, s):
                "For interactive Canvases, displays the given string in the \
                'info line' somewhere where the user can probably see it."
                pass 
                
        #------------ string/font info ------------
        def stringWidth(self, s, font=None):
                "Return the logical width of the string if it were drawn \
                in the current font (defaults to self.font)."
                raise NotImplementedError('stringWidth')
        
        def fontHeight(self, font=None):
                "Find the height of one line of text (baseline to baseline) of the given font."
                # the following approxmation is correct for PostScript fonts,
                # and should be close for most others:
                if not font: font = self.defaultFont
                return 1.2 * font.size
                
        def fontAscent(self, font=None):
                "Find the ascent (height above base) of the given font."
                raise NotImplementedError('fontAscent')
        
        def fontDescent(self, font=None):
                "Find the descent (extent below base) of the given font."
                raise NotImplementedError('fontDescent')
                
        #------------- drawing helpers --------------

        def arcPoints(self, x1,y1, x2,y2, startAng=0, extent=360):
                "Return a list of points approximating the given arc."          
                # Note: this implementation is simple and not particularly efficient.
                xScale = abs((x2-x1)/2.0)
                yScale = abs((y2-y1)/2.0)
        
                x = min(x1,x2)+xScale
                y = min(y1,y2)+yScale
        
                # "Guesstimate" a proper number of points for the arc:
                steps = min(max(xScale,yScale)*(extent/10.0)/10,200)
                if steps < 5: steps = 5
                
                from math import sin, cos, pi
        
                pointlist = []
                step = float(extent)/steps
                angle = startAng
                for i in range(int(steps+1)):
                        point = (x+xScale*cos((angle/180.0)*pi),
                                         y-yScale*sin((angle/180.0)*pi))
                        pointlist.append(point)
                        angle = angle+step
        
                return pointlist
                        
        def curvePoints(self, x1, y1, x2, y2, x3, y3, x4, y4):
                "Return a list of points approximating the given Bezier curve."
        
                # Adapted from BEZGEN3.HTML, one of the many
                # Bezier utilities found on Don Lancaster's Guru's Lair at
                # <URL: http://www.tinaja.com/cubic01.html>     
                bezierSteps = min(max(max(x1,x2,x3,x4)-min(x1,x2,x3,x3),
                                      max(y1,y2,y3,y4)-min(y1,y2,y3,y4)),
                                  200)
        
                dt1 = 1. / bezierSteps
                dt2 = dt1 * dt1
                dt3 = dt2 * dt1
        
                xx = x1
                yy = y1
                ux = uy = vx = vy = 0
        
                ax = x4 - 3*x3 + 3*x2 - x1
                ay = y4 - 3*y3 + 3*y2 - y1
                bx = 3*x3 - 6*x2 + 3*x1
                by = 3*y3 - 6*y2 + 3*y1
                cx = 3*x2 - 3*x1
                cy = 3*y2 - 3*y1
        
                mx1 = ax * dt3
                my1 = ay * dt3
        
                lx1 = bx * dt2
                ly1 = by * dt2
        
                kx = mx1 + lx1 + cx*dt1
                ky = my1 + ly1 + cy*dt1
        
                mx = 6*mx1 
                my = 6*my1
        
                lx = mx + 2*lx1
                ly = my + 2*ly1
        
                pointList = [(xx, yy)]
        
                for i in range(bezierSteps):
                        xx = xx + ux + kx
                        yy = yy + uy + ky
                        ux = ux + vx + lx
                        uy = uy + vy + ly
                        vx = vx + mx
                        vy = vy + my
                        pointList.append((xx, yy)) 
        
                return pointList

        def drawMultiLineString(self, s, x,y, font=None, color=None, angle=0):
                "Breaks string into lines (on \n, \r, \n\r, or \r\n), and calls drawString on each."
                import math
                import string
                h = self.fontHeight(font)
                dy = h * math.cos(angle*math.pi/180.0)
                dx = h * math.sin(angle*math.pi/180.0)
                s = s.replace('\r\n', '\n')
                s = s.replace('\n\r', '\n')
                s = s.replace('\r', '\n')
                lines = s.split('\n')
                for line in lines:
                        self.drawString(line, x, y, font, color, angle)
                        x = x + dx
                        y = y + dy

        #------------- drawing methods --------------

        # Note default parameters "=None" means use the defaults
        # set in the Canvas method: defaultLineColor, etc.

        def drawLine(self, x1,y1, x2,y2, color=None, width=None):
                "Draw a straight line between x1,y1 and x2,y2."
                raise NotImplementedError('drawLine')
        
        def drawLines(self, lineList, color=None, width=None):
                "Draw a set of lines of uniform color and width.  \
                lineList: a list of (x1,y1,x2,y2) line coordinates."
                # default implementation:
                for x1, y1, x2, y2 in lineList:
                        self.drawLine(x1, y1, x2, y2 ,color,width)
                

        #       For text, color defaults to self.lineColor.
        
        def drawString(self, s, x,y, font=None, color=None, angle=0):
                "Draw a string starting at location x,y."
                # NOTE: the baseline goes on y; drawing covers (y-ascent,y+descent)
                raise NotImplementedError('drawString')


        #       For fillable shapes, edgeColor defaults to self.defaultLineColor,
        #       edgeWidth defaults to self.defaultLineWidth, and
        #       fillColor defaults to self.defaultFillColor.
        #       Specify "don't fill" by passing fillColor=transparent.

        def drawCurve(self, x1,y1, x2,y2, x3,y3, x4,y4, 
                                edgeColor=None, edgeWidth=None, fillColor=None, closed=0):
                "Draw a B�zier curve with control points x1,y1 to x4,y4."

                pointlist = self.curvePoints(x1, y1, x2, y2, x3, y3, x4, y4)
                self.drawPolygon(pointlist,
                                                 edgeColor=edgeColor,
                                                 edgeWidth=edgeWidth,
                                                 fillColor=fillColor, closed=closed)

        def drawRect(self, x1,y1, x2,y2, edgeColor=None, edgeWidth=None, fillColor=None):
                "Draw the rectangle between x1,y1, and x2,y2. \
                These should have x1<x2 and y1<y2."
                
                pointList = [ (x1,y1), (x2,y1), (x2,y2), (x1,y2) ]
                self.drawPolygon(pointList, edgeColor, edgeWidth, fillColor, closed=1)

        def drawRoundRect(self, x1,y1, x2,y2, rx=8, ry=8,
                                        edgeColor=None, edgeWidth=None, fillColor=None):
                "Draw a rounded rectangle between x1,y1, and x2,y2, \
                with corners inset as ellipses with x radius rx and y radius ry. \
                These should have x1<x2, y1<y2, rx>0, and ry>0."

                x1, x2 = min(x1,x2), max(x1, x2)
                y1, y2 = min(y1,y2), max(y1, y2)
                
                dx = rx*2
                dy = ry*2
        
                partList = [
                        (figureArc, x1, y1, x1+dx, y1+dy, 180, -90),
                        (figureLine, x1+rx, y1, x2-rx, y1),
                        (figureArc, x2-dx, y1, x2, y1+dy, 90, -90),
                        (figureLine, x2, y1+ry, x2, y2-ry),
                        (figureArc, x2-dx, y2, x2, y2-dy, 0, -90),
                        (figureLine, x2-rx, y2, x1+rx, y2),
                        (figureArc, x1, y2, x1+dx, y2-dy, -90, -90),
                        (figureLine, x1, y2-ry, x1, y1+rx)
                        ]

                self.drawFigure(partList, edgeColor, edgeWidth, fillColor, closed=1)

        def drawEllipse(self, x1,y1, x2,y2, edgeColor=None, edgeWidth=None, fillColor=None):
                "Draw an orthogonal ellipse inscribed within the rectangle x1,y1,x2,y2. \
                These should have x1<x2 and y1<y2."

                pointlist = self.arcPoints(x1, y1, x2, y2, 0, 360)
                self.drawPolygon(pointlist,edgeColor, edgeWidth, fillColor, closed=1)

        def drawArc(self, x1,y1, x2,y2, startAng=0, extent=360,
                                edgeColor=None, edgeWidth=None, fillColor=None):
                "Draw a partial ellipse inscribed within the rectangle x1,y1,x2,y2, \
                starting at startAng degrees and covering extent degrees.   Angles \
                start with 0 to the right (+x) and increase counter-clockwise. \
                These should have x1<x2 and y1<y2."
                
                center = (x1+x2)/2, (y1+y2)/2
                pointlist = self.arcPoints(x1, y1, x2, y2, startAng, extent)
                
                # Fill...
                self.drawPolygon(pointlist+[center]+[pointlist[0]],
                         transparent, 0, fillColor)

                # Outline...
                self.drawPolygon(pointlist, edgeColor, edgeWidth, transparent)

        def drawPolygon(self, pointlist, 
                                edgeColor=None, edgeWidth=None, fillColor=None, closed=0):
                """drawPolygon(pointlist) -- draws a polygon
                pointlist: a list of (x,y) tuples defining vertices
                closed: if 1, adds an extra segment connecting the last point to the first
                """
                raise NotImplementedError('drawPolygon')
        
        def drawFigure(self, partList,
                                edgeColor=None, edgeWidth=None, fillColor=None, closed=0):
                """drawFigure(partList) -- draws a complex figure
                partlist: a set of lines, curves, and arcs defined by a tuple whose
                                  first element is one of figureLine, figureArc, figureCurve
                                  and whose remaining 4, 6, or 8 elements are parameters."""
        
                pointList = []
        
                for tuple in partList:
                        op = tuple[0]
                        args = list(tuple[1:])
        
                        if op == figureLine:
                                pointList.extend( [args[:2], args[2:]] )
                        elif op == figureArc:
                                pointList.extend(self.arcPoints(*args))
                        elif op == figureCurve:
                                pointList.extend(self.curvePoints(*args))
                        else:
                                raise TypeError("unknown figure operator: "+op)
        
                self.drawPolygon(pointList, edgeColor, edgeWidth, fillColor, closed=closed)


        # no colors apply to drawImage; the image is drawn as-is

        def drawImage(self, image, x1,y1, x2=None,y2=None):
                """Draw a PIL Image into the specified rectangle.  If x2 and y2 are
                omitted, they are calculated from the image size."""
                raise NotImplementedError('drawImage')



#-------------------------------------------------------------------------

# utility functions #

def getFileObject(file):
        """Common code for every Canvas.save() operation takes a string
        or a potential file object and assures that a valid fileobj is returned"""

        if file:
                if isinstance(file, str):
                        fileobj = open(file, "wb")
                else:
                        if hasattr(file, "write"):
                                fileobj = file
                        else:
                                raise Exception('Invalid file argument to save')
        else:
                raise Exception('Invalid file argument to save')
        
        return fileobj


class AffineMatrix:
    # A = [ a c e]
    #     [ b d f]
    #     [ 0 0 1]
    # self.A = [a b c d e f] = " [ A[0] A[1] A[2] A[3] A[4] A[5] ]"
    def __init__(self, init=None):
        if init:
            if len(init) == 6 :
                self.A = init
            if type(init) == type(self): # erpht!!! this seems so wrong
                self.A = init.A
        else:
            self.A = [1.0, 0, 0, 1.0, 0.0, 0.0] # set to identity

    def scale(self, sx, sy):
        self.A = [sx*self.A[0], sx*self.A[1], sy*self.A[2], sy * self.A[3], self.A[4], self.A[5] ]

    def rotate(self, theta):
        "counter clockwise rotation in standard SVG/libart coordinate system"
        # clockwise in postscript "y-upward" coordinate system
        # R = [ c  -s  0 ]
        #     [ s   c  0 ]
        #     [ 0   0  1 ]

        co = math.cos(PI*theta/180.0)
        si = math.sin(PI*theta/180.0)
        self.A = [self.A[0] * co + self.A[2] * si,
                  self.A[1] * co + self.A[3] * si,
                  -self.A[0]* si + self.A[2] * co,
                  -self.A[1]* si + self.A[3] * co,
                  self.A[4],
                  self.A[5] ]

    def translate(self, tx, ty):
        self.A  = [ self.A[0], self.A[1], self.A[2], self.A[3],
                    self.A[0]*tx + self.A[2]*ty + self.A[4],
                    self.A[1]*tx + self.A[3]*ty + self.A[5] ]











