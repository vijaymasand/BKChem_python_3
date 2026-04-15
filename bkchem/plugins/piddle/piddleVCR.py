# piddleVCR.py -- a record/playback canvas for PIDDLE
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
# $Log: piddleVCR.py,v $
# Revision 1.4  2000/08/29 04:21:28  clee
# sweep through w/ changes to save()/flush()
# just before release
#
# Revision 1.3  2000/08/28 17:08:55  clee
# check of CanvasXX.save() signature
#
# Revision 1.2  2000/07/06 02:58:19  clee
# fixed reference to .recordfunc to .recordfunc, now gives warning when asked to drawImage
#


"""piddleVCR

This module implements a PIDDLE canvas that simply records all
drawing commands given to it.  It can save this recording to
a file, load it again, and play it back into another canvas.

Usage: to record, it must be attached to a canvas so that it
can ask the attached canvas for font metrics.  To play back,
or if no font metrics are needed, then attaching it to a
canvas is not necessary.  Just call myPiddleVCR.playBack(canvas)
to play back recorded drawing commands.

STATUS: Working, but still contains some debugging code.
        Will NOT work with images :(  -cwl
Joe Strout (joe@strout.net), 10/21/99.
"""

VERSION = 0.1

from .piddle import *
pass  # types wildcard removed
import string

# internal utility functions
def _repr(x):
    "Convert x into a representation we can use to play back."
    return repr(x)

def _reprs(*args):
    "Convert a whole set of items into a tuple of their representations."
    return tuple([_repr(x) for x in args])


class VCRCanvas( Canvas ):
    
    def __init__(self, size=(0,0), name="piddleVCR", playthru=None):
        # canvas we send drawing commands to while recording;
        # also used for font metrics:
        self.__dict__['playthru'] = playthru    
        self.__dict__['recording'] = []
        Canvas.__init__(self, size, name)
        self.__dict__['recording'] = []        # wipe out any extra piddle initialization
        
    def __setattr__(self, attribute, value):
        if self.playthru: setattr(self.playthru, attribute, value)
        self.__dict__[attribute] = value
        if attribute[0] == '_': return
        self._record("%s = %s" % (attribute, _repr(value)) )
                
    # private functions
    def _record(self,s):
        self.recording.append(s)
        # print s  # debugging function

    def _recordfunc(self,func,*args):
        prototype = func + "(" + ("%s," * len(args))[:-1] + ")"
        s = prototype % _reprs(*args)
        if self.playthru:
            exec('self.playthru.' + s)
        self._record(s)
        
    # public functions

    def flush(self):
        if self.playthru:
            self.playthru.flush()
        

    def playBack(self, canvas):
        for item in self.recording:
            exec("canvas." + item)
        canvas.flush()
    
    def save(self, file=None, format=None):
        "file may be either a filename or a file object. The format argument is not used"
        if isinstance(file, str): file = open(file,'w')
        file.write("piddleVCR %s\n" % VERSION)
        for item in self.recording:
            file.write(item + '\n')
        file.write("END")
    
    def load(self, file):
        if isinstance(file, str): file = open(file,'r')
        line = ''
        # skip header
        while line[:10] != 'piddleVCR ':
            line = file.readline()
        self.__dict__['recording'] = []
        # read data lines, and append to recording
        line = file.readline()
        while line != "END":
            self.recording.append(line.strip())
            line = file.readline()
        return len(self.recording)        

    #------------ string/font info ------------
    def stringWidth(self, s, font=None):
        "Return the logical width of the string if it were drawn \
        in the current font (defaults to self.defaultFont)."

        if self.playthru:
                        return self.playthru.stringWidth(s,font)
        else:
                        return Canvas.stringWidth(self,s,font)
    
    def fontAscent(self, font=None):
        "Find the ascent (height above base) of the given font."

        if self.playthru:
                        return self.playthru.fontAscent(font)
        else:
                        return Canvas.fontAscent(self,font)
    
    def fontDescent(self, font=None):
        "Find the descent (extent below base) of the given font."

        if self.playthru: return self.playthru.fontDescent(font)
        else: return Canvas.fontDescent(self,font)
    
    #------------- drawing methods --------------
    def drawLine(self, x1,y1, x2,y2, color=None, width=None):
        "Draw a straight line between x1,y1 and x2,y2."

        self._recordfunc('drawLine', x1,y1,x2,y2,color,width)

    def drawLines(self, lineList, color=None, width=None):
        "Draw a set of lines of uniform color and width.  \
        lineList: a list of (x1,y1,x2,y2) line coordinates."

        self._recordfunc("drawLines", lineList,color,width)


    def drawString(self, s, x,y, font=None, color=None, angle=0):
        "Draw a string starting at location x,y."

        self._recordfunc("drawString", s,x,y,font,color,angle)
        

    def drawCurve(self, x1,y1, x2,y2, x3,y3, x4,y4, 
                edgeColor=None, edgeWidth=None, fillColor=None, closed=0):
        "Draw a B�zier curve with control points x1,y1 to x4,y4."

        self._recordfunc("drawCurve", x1,y1,x2,y2,x3,y3,x4,y4,edgeColor,edgeWidth,fillColor,closed)


    def drawRect(self, x1,y1, x2,y2, edgeColor=None, edgeWidth=None, fillColor=None):
        "Draw the rectangle between x1,y1, and x2,y2. \
        These should have x1<x2 and y1<y2."
        
        self._recordfunc("drawRect", x1,y1,x2,y2,edgeColor,edgeWidth,fillColor)


    def drawRoundRect(self, x1,y1, x2,y2, rx=8, ry=8,
                    edgeColor=None, edgeWidth=None, fillColor=None):
        "Draw a rounded rectangle between x1,y1, and x2,y2, \
        with corners inset as ellipses with x radius rx and y radius ry. \
        These should have x1<x2, y1<y2, rx>0, and ry>0."

        self._recordfunc("drawRoundRect", x1,y1, x2,y2, rx, ry, edgeColor,edgeWidth,fillColor)


    def drawEllipse(self, x1,y1, x2,y2, edgeColor=None, edgeWidth=None, fillColor=None):
        "Draw an orthogonal ellipse inscribed within the rectangle x1,y1,x2,y2. \
        These should have x1<x2 and y1<y2."

        self._recordfunc("drawEllipse", x1,y1,x2,y2,edgeColor,edgeWidth,fillColor)


    def drawArc(self, x1,y1, x2,y2, startAng=0, extent=360,
                edgeColor=None, edgeWidth=None, fillColor=None):
        "Draw a partial ellipse inscribed within the rectangle x1,y1,x2,y2, \
        starting at startAng degrees and covering extent degrees.   Angles \
        start with 0 to the right (+x) and increase counter-clockwise. \
        These should have x1<x2 and y1<y2."

        self._recordfunc("drawArc", x1,y1,x2,y2,startAng,extent,edgeColor,edgeWidth,fillColor)

    def drawPolygon(self, pointlist, 
                edgeColor=None, edgeWidth=None, fillColor=None, closed=0):
        """drawPolygon(pointlist) -- draws a polygon
        pointlist: a list of (x,y) tuples defining vertices
        """

        self._recordfunc("drawPolygon", pointlist,edgeColor,edgeWidth,fillColor,closed)


    def drawFigure(self, partList,
                edgeColor=None, edgeWidth=None, fillColor=None, closed=0):
        """drawFigure(partList) -- draws a complex figure
        partlist: a set of lines, curves, and arcs defined by a tuple whose
                  first element is one of figureLine, figureArc, figureCurve
                  and whose remaining 4, 6, or 8 elements are parameters."""

        self._recordfunc("drawFigure", partList, edgeColor,edgeWidth,fillColor,closed)

    def drawImage(self, image, x1,y1, x2=None,y2=None):
        print("Warning!!! piddleVCR does not implent drawImage")
        # These are thoughts on how to implement this using a shelf to store image
        # it kept everyting contained in one file
#          import shelve
#          imageKeyName = `image`
#          print imageKeyName

#          if hasattr(self, 'shelf'):
#              print "has shelf"
#          else:
#              print "creating shelf"
#              self.shelfName = self.name + ".vcr.shelf"
#              self.shelf = shelve.open(self.shelfName)
#              # now let the vcr file know we have this shelf
#              self._record("import shelve")
#              self._record("
#          self.shelf[imageKeyName] = image

#          self._recordfunc("drawImage, 
        
        
def test1():
    import piddlePS
    canvas = piddlePS.PSCanvas()
    vcr = VCRCanvas(canvas)
    vcr.defaultLineWidth = 3
    vcr.drawLine(10,10,100,30, color=red)
    vcr.drawString("This is a test!", 25,50, Font(size=24))
    vcr.flush()

    f = open('test1.vcr','w')
    vcr.save(f)

def test2():
    vcr = VCRCanvas()
    f = open('test1.vcr','r')
    vcr.load(f)
    f.close()
    
    import piddlePS
    canvas2 = piddlePS.PSCanvas()
    vcr.playBack(canvas2)
    canvas2.flush()

test1()
test2()
