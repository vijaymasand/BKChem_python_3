""" piddleAI.py - a  backend for PIDDLE which produces file in Abode Illustrator 3 format.

These can be read by most vector graphic applications on all common platforms.

Note: This back end assumes that the output is intended as a graphic that
is to used elsewhere and so the "size" attribute is ignored and the
artboard size is calculated to slightly bigger than the bounding box.


(C) Copyright Bill Bedford 1999


BB 28/09/99 Added Rewrote drawEllipse, drawroundRect and drawArc to use drawBezier
                        fixed bug in name in AICanvas.__init__
                        
                        
"""
from .piddle import *
from . import aigen
import string
import zlib
from io import StringIO, BytesIO

from math import sin, cos, pi, ceil

author = 'Me'
pageSize = (595, 842) #A4

class AICanvas(Canvas):
        """This works by accumulating a list of strings containing 
        AI page marking operators, as you call its methods.  We could
        use a big string but this is more efficient - only concatenate
        it once, with control over line ends.  When
        done, it hands off the stream to a AIPage object."""

        def __init__(self, size=(0,0), name='piddle.ai'):
                Canvas.__init__(self, size, name=name)
                print(name)
                if name[-3:] == '.ai':
                        self.name = name
                else:
                        self.name = name + '.ai'
                self.code = []  # list of strings to join later
                self._colorNames = {}
                self.currentPageHasImages = 0
                self.doc = aigen.AIDocument()
                
                self.pageNumber = 1   # keep a count
                
                # now for any default graphics settings 
                self.defaultFont=Font(face='Helvetica')
                self.defaultLineColor = black
                self.defaultFillColor = transparent
                c = self._currentLineColor = self.defaultLineColor
                self._currentFillColor = self.defaultFillColor
                self._currentTextColor = self.defaultLineColor
                
                r,g,b = c.red, c.green, c.blue
                w = self._currentWidth = self.defaultLineWidth
                self._currentFont = self.defaultFont

                self._currentWidth = self.defaultLineWidth = 1
                self.maxline = 1
                self.maxx, self.minx, self.maxy, self.miny = (0,0,0,0)
                self.boundbox = self.maxx, self.minx, self.maxy, self.miny, self.maxline
                
                self.mitre = '4.5 M'
                self.linejoin = '0 j'
                self.linecap = '0 J' # 0=butt, 1=round, 2=square
                self.winding = '1 XR' # 0=nozerwinding, 1=even/odd fillrule
                self.winOrder = '0 D' #0=clockwise, 1=antoclockwise

        #info functions - non-standard
                
        def setTitle(self):
                self.doc.setTitle(self.name)
                
        def setPageSize(self, pageSize):
                self.doc.setPageSize(pageSize)
                
        def setBoundingBox(self):
                self.doc.setBoundingBox(self.boundbox)
                
                
                
        
        def showPage(self):
                """This is where the fun happens"""
                self.setTitle()
                self.setAuthor(author)
                self.setBoundingBox()
                stream = self.winding + '\n' + self.winOrder
                stream = [stream] + self.code
                self.doc.setPage(stream)

        def save(self, file=None, format=None):
                """Saves the file.  If holding data, do
                a showPage() to save them having to.""" 
                if len(self.code):  
                        self.showPage()
                self.doc.SaveToFile(self.name)
                print('saved', self.name)




        #------------ canvas capabilities -------------
        def isInteractive(self):
                return 0

        def canUpdate(self):
                return 0

        #------------ general management -------------
        def clear(self):
                "same as ShowPage"
                self.showPage()
        
        def flush(self):
                pass

                
        def setInfoLine(self, s):
                self.doc.setTitle(s)
                        
        def setAuthor(self, name):
                self.doc.setAuthor(name)
        
        def _bounds(self, x1, y1, x2, y2):
#               print self.maxx, x1, x2, y1, y2
                self.maxx = max(self.maxx, x1, x2)
                self.maxy = max(self.maxy, y1, y2)
                self.minx = min(self.minx, x1, x2)
                self.miny = min(self.miny, y1, y2)
                self.boundbox = self.minx, self.miny, self.maxx, self.maxy, self.maxline
#               print self.boundbox

        def _updateLineColor(self, color):
                color = color or self.defaultLineColor
                if color != self._currentLineColor:
                        self._currentLineColor = color
                        if  self._currentLineColor != transparent:
                                r,g,b = color.red, color.green, color.blue
                                self.code.append('%s %s %s XA' % (r,g,b))
         


        def _updateFillColor(self, color):
                color = color or self.defaultFillColor
                if color != self._currentFillColor:
                        self._currentFillColor = color
                        if  self._currentLineColor != transparent:
                                r,g,b = color.red, color.green, color.blue
                                self.code.append('%s %s %s Xa' % (r,g,b))
 

        def _updateLineWidth(self, width):
                if width == None: 
                        width = self.defaultLineWidth
                if width != self._currentWidth:
                        self.maxline = max(self.maxline, width)
                        self._currentWidth = width
                        self.code.append('%s w' % width)
  
#       def _updateFont(self, font):
#               font = font or self.defaultFont
#               if font != self._currentFont:
#                       self._currentFont = font
#                       ps_font_name = self._findExternalFontName(font)
#                       pdf_font_name = self._findInternalFontName(ps_font_name)
#                       s = font.size
#                       self.code.append('BT /%s %s Tf %s TL ET' % (pdf_font_name, s, s))
#

        #------------ string/font info ------------
                
        def stringWidth(self, s, font=None):
                "Return the logical width of the string if it were drawn \
                in the current font (defaults to self.font)."
                if not font:
                        font = self.defaultFont
                fontname = self._findExternalFontName(font)
                return pdfmetrics.stringwidth(s, fontname) * font.size * 0.001


        def fontHeight(self, font=None):
                if not font:
                        font = self.defaultFont
                return font.size

        def fontAscent(self, font=None):
                if not font:
                        font = self.defaultFont
                fontname = self._findExternalFontName(font)
                return pdfmetrics.ascent_descent[fontname][0] * 0.001 * font.size
                
        def fontDescent(self, font=None):
                if not font:
                        font = self.defaultFont
                fontname = self._findExternalFontName(font)
                return -pdfmetrics.ascent_descent[fontname][1] * 0.001 * font.size
        
        #------------- drawing methods --------------

                
        def drawLine(self, x1,y1, x2,y2, color=None, width=None):
                self._updateLineColor(color)
                self._updateLineWidth(width)
                w = self._currentWidth/2
                self._bounds(x1-w, y1-w, x2+w, y2+w)
                self.code.append(x1, y1, 'm')
                self.code.append(x2, y2, 'L')
                self.code.append('S')


        def drawLines(self, lineList, color=None, width=None):
                self._updateLineColor(color)
                self._updateLineWidth(width)
                self.code.append('u ')
                for (x1, y1, x2, y2) in lineList:
                        w = self._currentWidth/2
                        self._bounds(x1-w, y1-w, x2+w, y2+w)
                        self.code.append(x1, y1, 'm')
                        self.code.append(x2, y2, 'L')
                        self.code.append('S')
                self.code.append('U')

#       def drawString(self, s, x, y, font=None, color=None, angle=0):
#               # all escaping of text is done in the back end
#               self._updateLineColor(color)
#               self._updateFont(font)
#               text = self._escape(text)
#               fnt = self._currentFont
#               if self._currentTextColor != transparent:
#                       c = cos(angle * pi / 180.0)
#                       s = sin(angle * pi / 180.0)
#                       self.code.append('BT')
#                       color = color or self._currentTextColor
#                       r,g,b = color.red, color.green, color.blue
#                       self.code.append('%s %s %s rg' % (r,g,b))
#                       self.code.append('%f %f %f %f %s %s Tm' % (c, s, -s, c, x, -y))
#                       self.code.append(' (%s) Tj ET' % text)
#                       #keep underlining separate - it is slow and unusual anyway
#                       if fnt.underline:
#                               ypos = y + (0.5 * self.fontDescent(fnt))
#                               thickness = 0.08 * fnt.size
#                               width = self.stringWidth(text, fnt)
#                               self.drawLine(x, ypos, x + width, ypos, width=thickness)
#                               
#       def drawJustifiedString(self, s, x, y, font=None, color=None, angle=0):
#               self._updateLineColor(color)
#               self._updateFont(font)
#               text = self._escape(text)
#               if self._currentTextColor != transparent:
#                       c = cos(angle * pi / 180.0)
#                       s = sin(angle * pi / 180.0)
#                       self.code.append('BT')
#                       color = color or self._currentTextColor
#                       r,g,b = color.red, color.green, color.blue
#                       self.code.append('%s %s %s rg' % (r,g,b))
#                       self.code.append('%f %f %f %f %s %s Tm' % (c, s, -s, c, x, -y))
#                       self.code.append('36 Tw')
#                       self.code.append(' (%s) Tj ET' % text)
#
#

        def drawCurve(self, x1, y1, x2, y2, x3, y3, x4, y4,
                                        edgeColor=None, edgeWidth=None, fillColor=None, closed=0):
                self._updateFillColor(fillColor)
                self._updateLineWidth(edgeWidth)
                self._updateLineColor(edgeColor)
                w = self._currentWidth/2
                self._bounds(x1-w, y1-w, x4+w, y4+w)
                if self._currentLineColor != transparent:
#                       if closed:
#                               ##XXX Not what we want
#                               if self._currentFillColor != transparent:
#                                       op = 'B'        #closepath, eofill, stroke
#                               else:
#                                       op = 'S'  # closepath and stroke
#                       else:
#                               if self._currentFillColor != transparent:
#                                       op = 'B'        #eofill, stroke
#                               else:
#                                       op = 'S'  # stroke
                        op = 'S'  # stroke
                else:
                        op  = 'f'
                self.code.append('u')
                self.code.append(x1, y1, 'm' )
                self.code.append(x2, y2, x3, y3, x4, y4, 'c')
                self.code.append(op + ' U')
                
        def bezierArc(self, x1,y1, x2,y2, startAng=0, extent=90):
                """bezierArc(x1,y1, x2,y2, startAng=0, extent=90) --> List of Bezier
                curve control points.
                Contributed by Robert Kern, 28/7/99.
                (x1, y1) and (x2, y2) are the corners of the enclosing rectangle such that
                x1<x2 and y1<y2.  The coordinate system has coordinates that increase to the
                right and down.  Angles, measured in degress, start with 0 to the right (the
                positive X axis) and increase counter-clockwise.  The arc extends from startAng
                to startAng+extent.  I.e. startAng=0 and extent=180 yields an openside-down
                semi-circle.

                The resulting coordinates are of the form (x1,y1, x2,y2, x3,y3, x4,y4) such that
                the curve goes from (x1, y1) to (x4, y4) with (x2, y2) and (x3, y3) as their
                respective Bzier control points."""

                if abs(extent) <= 90:
                        arcList = [startAng]
                        fragAngle = float(extent)
                        Nfrag = 1
                else:
                        arcList = []
                        Nfrag = int(ceil(abs(extent)/90.))
                        fragAngle = float(extent) / Nfrag

                x_cen = (x1+x2)/2.
                y_cen = (y1+y2)/2.
                rx = (x2-x1)/2.
                ry = (y2-y1)/2.
                halfAng = fragAngle * pi / 360.
                kappa = 4. / 3. * (1. - cos(halfAng)) / sin(halfAng)

                pointList = []

                for i in range(Nfrag):
                        theta0 = (startAng + i*fragAngle) * pi / 180.
                        theta1 = (startAng + (i+1)*fragAngle) *pi / 180.
                        pointList.append((x_cen + rx * cos(theta0),
                                y_cen - ry * sin(theta0),
                                x_cen + rx * (cos(theta0) - kappa * sin(theta0)),
                                y_cen - ry * (sin(theta0) + kappa * cos(theta0)),
                                x_cen + rx * (cos(theta1) + kappa * sin(theta1)),
                                y_cen - ry * (sin(theta1) - kappa * cos(theta1)),
                                x_cen + rx * cos(theta1),
                                y_cen - ry * sin(theta1)))

                return pointList


        
        def drawArc(self, x1, y1, x2, y2, startAng=0, extent=90, edgeColor=None, 
                        edgeWidth=None, fillColor=None, closed=0):
                self._updateFillColor(fillColor)
                self._updateLineWidth(edgeWidth)
                self._updateLineColor(edgeColor)
                w = self._currentWidth/2
                self._bounds(x1-w, y1-w, x2+w, y2+w)
                if self._currentLineColor != transparent:
                        if self._currentFillColor != transparent:
                                op = 'B'        #eofill, stroke
                        else:
                                op = 'S'  # stroke
                else:
                        op = 'f'
                pointlist = self.bezierArc(x1, y1, x2, y2, startAng, extent)
#               print pointlist, type(pointlist)
                st = list(pointlist[0][:2])
                st.append('m')
                self.code.append('u')
                self.code.append(tuple(st))
                for i in range(len(pointlist)):
                        st = list(pointlist[i][2:])
                        st.append('c')
                        self.code.append(tuple(st))
                self.code.append(op + ' U')
                        


        def drawRect(self, x1, y1, x2, y2, edgeColor=None, 
                        edgeWidth=None, fillColor=None, closed=0):
                self._updateFillColor(fillColor)
                self._updateLineWidth(edgeWidth)
                self._updateLineColor(edgeColor)
                w = self._currentWidth/2
                self._bounds(x1-w, y1-w, x2+w, y2+w)
                if self._currentLineColor != transparent:
                        if closed:
                                if self._currentFillColor != transparent:
                                        op = 'b'        #closepath, eofill, stroke
                                else:
                                        op = 's'  # closepath and stroke
                        else:
                                if self._currentFillColor != transparent:
                                        op = 'B'        #eofill, stroke
                                else:
                                        op = 'S'  # stroke
                else:
                        op = 'f'
                self.code.append('u')
                self.code.append(x1, y1, 'm' )
                self.code.append(x1, y2, 'L')
                self.code.append(x2, y2, 'L')
                self.code.append(x2, y1, 'L')
                self.code.append(x1, y1, 'L')
                self.code.append(op + ' U')

        def drawRoundRect(self, x1, y1, x2, y2, rx=8, ry=8,
                                        edgeColor=None, edgeWidth=None, fillColor=None):
                self._updateLineWidth(edgeWidth)
                self._updateLineColor(edgeColor)
                self._updateFillColor(fillColor)
                w = self._currentWidth
                self._bounds(x1-w, y1-w, x2+w, y2+w)

                pointlist = self.bezierArc(x1, y1, x1+2*rx, y1+2*ry, 90, 360)
#               for c in pointlist:
#                       print c

                trans = [(0, 0), (0, y2-y1-2*ry), (x2-x1-2*rx, y2-y1-2*ry), (x2-x1-2*rx, 0)]
                st = list(pointlist[0][:2])
                stx = [0, 2, 4, 6]
                sty = [1, 3, 5, 7]
                st.append('m')
#               print st
                self.code.append('u')
                self.code.append(tuple(st))
                for i in range(len(pointlist)):
                        sl = list(pointlist[i])
                        for k in stx:
                                sl[k] = sl[k] + trans[i][0]
                        for k in sty:
                                sl[k] = sl[k] + trans[i][1]
                        sk = sl[2:]
                        sl = sl[:2]
                        sk.append('c')
                        sl.append('l')
#                       print sl
#                       print sk
                        if i != 0:
                                self.code.append(tuple(sl))
                        self.code.append(tuple(sk))

                if self._currentLineColor != transparent:
                        if self._currentFillColor != transparent:
                                op = 'b'        #closepath, eofill, stroke
                        else:
                                op = 's'  # closepath and stroke
                else:
                        op = 'f'
                self.code.append( op + ' U')


        def drawEllipse(self, x1, y1, x2, y2,
                                        edgeColor=None, edgeWidth=None, fillColor=None):
                self._updateLineWidth(edgeWidth)
                self._updateLineColor(edgeColor)
                self._updateFillColor(fillColor)
                w = self._currentWidth/2
                self._bounds(x1-w, y1-w, x2+w, y2+w)
                pointlist = self.bezierArc(x1, y1, x2, y2, 0, 360)
#               print pointlist, type(pointlist)
                st = list(pointlist[0][:2])
                st.append('m')
                self.code.append('u')
                self.code.append(tuple(st))
                for i in range(len(pointlist)):
                        st = list(pointlist[i][2:])
                        st.append('c')
                        self.code.append(tuple(st))

                if self._currentLineColor != transparent:
                        if self._currentFillColor != transparent:
                                op = 'b'        #closepath, eofill, stroke
                        else:
                                op = 's'  # closepath and stroke
                else:
                        op = 'f'
                self.code.append( op + ' U')


        def drawPolygon(self, pointlist, edgeColor=None, 
                        edgeWidth=None, fillColor=None, closed=0):
                start = pointlist[0]
                pointlist = pointlist[1:]
                x1 = min(map(lambda _p: _p[0], pointlist))
                x2 = max(map(lambda _p: _p[0], pointlist))
                y1 = min(map(lambda _p: _p[1], pointlist))
                y2 = max(map(lambda _p: _p[1], pointlist))
                self._updateFillColor(fillColor)
                self._updateLineWidth(edgeWidth)
                self._updateLineColor(edgeColor)
                w = self._currentWidth/2
                self._bounds(x1-w, y1-w, x2+w, y2+w)
                self.code.append('u')
                self.code.append(start[0], start[1], 'm')
                for point in pointlist:
                        self.code.append(point[0], point[1], 'L')
                if self._currentLineColor != transparent:
                        if closed:
                                self.code.append(start[0], start[1], 'L')
                                if self._currentFillColor != transparent:
                                        op = 'b'        #closepath, eofill, stroke
                                else:
                                        op = 's'  # closepath and stroke
                        else:
                                if self._currentFillColor != transparent:
                                        op = 'B'        #eofill, stroke
                                else:
                                        op = 'S'  # stroke
                else:
                        op = 'f'
                self.code.append(op + ' U')


        def drawString():
                print("Sorry Not yet impemented")



##########################################################
#
#  tests
#
##########################################################




def test():
        c = AICanvas('piddletest3')
        c.drawLine(000, 000, 000, 400, magenta, 20)
        c.drawLine(000, 400, 400, 400, cyan, 20)
        c.drawLine(400, 400, 400, 000, yellow, 20)
        c.drawLine(400, 000, 000, 000, black, 20)
        
        Lines = [   (100, 100, 300, 100),
                                (300, 100, 300, 300),
                                (300, 300, 100, 300),
                                (100, 300, 100, 100)  ]
        c.drawLines(Lines, red, 10)
##      
##      f = Font()
##      f.face = 'Times'
##      f.bold = 1
##      f.size = 24
##
##      c.drawString('AI PIDDLE RULES!', 
##                      100,450, font=f, angle=0, color=teal)
##      
##
##      for i in range(12):
##              c.drawString('------AI PIDDLE RULES!', 
##                      300,600, angle=i*15)
##                      
        #curve
        c.drawCurve(100,500,300,500,400,600,400,800,
                        edgeColor=purple,
                        edgeWidth=1,
                        fillColor=yellow,
                        closed=1)       

        #rectangle
        c.drawRect(100,550,200,600,
                        edgeColor=purple,
                        edgeWidth=1,
                        fillColor=yellow,
                        closed=1)       

        #polygon
        c.drawPolygon([(72,72),(72,150),(80,100), (200,72), (130, 40)],
                        edgeColor=blue,
                        edgeWidth=6,
                        closed=0)
        #arc
        c.drawEllipse( 130,30, 200,100,
                fillColor=green, 
                edgeWidth=4 )
#
        c.drawArc( 130,30, 200,100, 45, 180, 
                edgeColor=red, 
                edgeWidth=4 )
                
        c.drawRoundRect(0,0, 200,100, 30,30,
                edgeColor=red, 
                edgeWidth=2 )

        c.flush()


if __name__ == '__main__':
                test()  
                import sys
                sys.exit(1)
