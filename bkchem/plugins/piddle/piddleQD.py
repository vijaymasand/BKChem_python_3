# piddleQD.py -- a QuickDraw backend for PIDDLE
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

"""QDCanvas

This class implements a PIDDLE Canvas object that draws using QuickDraw
(the MacOS drawing API) into an IDE window.

Joe Strout (joe@strout.net), September 1999
"""

# Revisions:
#
#       9/20/99 JJS: added interactive methods and info line
#
#   6/14/99 JJS: added support for Copy command

# Implementation notes:
#       Each QDCanvas maintains a Picture, and uses this for refreshing.
#       This means that drawing is not visible until it is flushed, but
#       flushing is expensive, as the entire picture must be redrawn (to
#       reopen it for further drawing).
#
#       The line color is stored in the QD fore color, and the fill color
#       is stored in the back color -- fills are actually done by erasing.

from .piddle import *
import Qd
import QuickDraw
import Scrap
import W
import Fonts
import Events
import Evt
import string
pass  # types wildcard removed

# utility functions
def _setForeColor(c):
        "Set the QD fore color from a piddle color."
        Qd.RGBForeColor( (c.red*65535, c.green*65535, c.blue*65535) )

def _setBackColor(c):
        "Set the QD background color from a piddle color."
        Qd.RGBBackColor( (c.red*65535, c.green*65535, c.blue*65535) )

# global -- which QDCanvas has the current port
_curCanvas = None

# global dictionary mapping font names to QD font IDs
_fontMap = {}
for item in filter(lambda x:x[0]!='_',dir(Fonts)):
        _fontMap[string.lower(item)] = Fonts.__dict__[item]
_fontMap['system'] = Fonts.kFontIDGeneva
_fontMap['monospaced'] = Fonts.kFontIDMonaco
_fontMap['serif'] = Fonts.kFontIDNewYork
_fontMap['sansserif'] = Fonts.kFontIDGeneva

# utility classes
class _PortSaver:

        def __init__(self, qdcanvas):
                self.port = Qd.GetPort()
                Qd.SetPort(qdcanvas._window.wid)
        
        def __del__(self):
                Qd.SetPort(self.port)

class _QDCanvasWindow(W.Window):
        "This internally-used class implements the window in which QDCanvas draws."
        
        def __init__(self, owner, size=(300,300), title="Graphics"):
                self.owner = owner
                size = (size[0], size[1]+16)                    # leave room for info line!
                W.Window.__init__(self, size, title)
                self.infoline = ''
                self.open()
                self.lastMouse = (-1,-1)
                
        def close(self):
                try: self.owner._noteWinClosed(self)
                except: pass
                W.Window.close(self)
        
        def domenu_copy(self, *args):
                r = self._bounds
                pict = Qd.OpenPicture(r)
                self.owner._drawWindow()
                Qd.ClosePicture()
                Scrap.ZeroScrap()
                Scrap.PutScrap('PICT',pict.data)

        def do_update(self, window, event):
                # draw the content
                try: self.owner._drawWindow()
                except: pass
                
                # draw the info line
                self.drawInfoLine()
        
        def drawInfoLine(self):
                Qd.ForeColor(QuickDraw.blackColor)
                Qd.BackColor(QuickDraw.whiteColor)
                bounds = self.getbounds()
                width = bounds[2] - bounds[0]
                height = bounds[3] - bounds[1]
                Qd.MoveTo( 0, height-16 )
                Qd.LineTo( width, height-16 )
                r = (0,height-15,width,height)
                Qd.EraseRect(r)
                Qd.TextFont(Fonts.kFontIDGeneva)
                Qd.TextSize(9)
                Qd.TextFace(0)
                Qd.MoveTo( 8, height-6 )
                Qd.DrawString(self.infoline)
        
        def do_activate(self, activate, event):
                global _curCanvas
                if _curCanvas == self.owner and not activate:
                        #print self.owner, "is no longer current"
                        _curCanvas = None
                
        def do_contentclick(self, point, modifiers, event):
                if self.owner: self.owner.onClick( self.owner, point[0], point[1] )
                
        def do_char(self, char, event):
                import Wkeys
                (what, message, when, where, modifiers) = event
                mods = []
                if modifiers & Events.shiftKey: mods.append( modShift )
                if modifiers & Events.controlKey: mods.append( modControl )
                if self.owner: self.owner.onKey( self.owner, char, mods )
                W.Window.do_char(self, char, event)

        def idle(self, *args):
                if self.owner:
                        bounds = self.getbounds()
                        x,y = mouse = Evt.GetMouse()
                        maxx, maxy = self.owner.size
                        if mouse != self.lastMouse and x >= 0 and x < maxx \
                                        and y >= 0 and y < maxy:
                                self.owner.onOver( self.owner, x,y )
                                self.lastMouse = mouse
                W.Window.idle(self,args)

class QDCanvas( Canvas ):
        
        def __init__(self, size=(300,300), name="Graphics"):
                "Initialize QuickDraw canvas with window size and title."
                self._window = _QDCanvasWindow(self, size, name)
                self._port = Qd.GetPort()
                Canvas.__init__(self, size, name)
                self._penstate = Qd.GetPenState()
                self.picture = Qd.OpenPicture(self._window._bounds)
                self.picopen = 1
        
                self.patch = 0          # PATCH just for testing!
        
        #----------- custom QDCanvas methods -----------
        
        def __setattr__(self, attribute, value):
                self.__dict__[attribute] = value
                if attribute == "defaultLineColor":
                        self._window.SetPort()
                        _setForeColor(self.defaultLineColor)
                elif attribute == "defaultLineWidth":
                        self._window.SetPort()
                        Qd.PenSize(value,value)
                        self._penstate = Qd.GetPenState()
                elif attribute == "defaultFont":
                        self._window.SetPort()
                        self._setFont(value)
        
        def __del__(self):
                #print "Deleting", self
                try: self._window.close()
                except: pass
                self._window = None
                Qd.KillPicture(self.picture)

        def _noteWinClosed(self, win):
                "Note that our window has been closed."
                self._window = None

        def _drawWindow(self):
                "Update the drawing in the window."
                if not hasattr(self,'picture'): return
                if self.picopen:
                        self.flush()
                else:
                        portsaver = _PortSaver(self)
                        Qd.DrawPicture(self.picture, self._window._bounds)              

        def _prepareToDraw(self):
                global _curCanvas
                
                # open the picture, if not already open
                if not self.picopen:
                        portsaver = _PortSaver(self)
                        temp = Qd.OpenPicture(self._window._bounds)
                        Qd.DrawPicture( self.picture, self._window._bounds)
                        self.picture = temp
                        self.picopen = 1
                
                # and set the default drawing parameters, if we weren't the default before
                if Qd.GetPort() != self._port: # _curCanvas != self:
                        #print "setting port to", self
                        self._window.SetPort()
                        _setForeColor(self.defaultLineColor)
                        _setBackColor(self.defaultFillColor)
                        Qd.SetPenState(self._penstate)
                        self.patch = self.patch + 1
                        _curCanvas = self

        def _setFont(self, font):
                global _fontMap
                if not font.face:
                        Qd.TextFont(Fonts.applFont)
                elif hasattr(font,'_QDfontID'):
                        Qd.TextFont(font._QDfontID)
                else:
                        if type(font.face) == str:
                                try: fontID = _fontMap[string.lower(font.face)]
                                except:
                                        return 0        # font not found!
                        else:
                                for item in font.face:
                                        fontID = None
                                        try:
                                                fontID = _fontMap[string.lower(item)]
                                                break
                                        except: pass
                                if fontID == None:
                                        return 0        # font not found!

                        # cache the fontID for quicker reference next time!
                        font.__dict__['_QDfontID'] = fontID
                        # font._QDfontID = fontID
                        Qd.TextFont(fontID)
                
                # now, set the size and style as well!
                Qd.TextSize(font.size)
                stylecode = QuickDraw.bold * font.bold + \
                                        QuickDraw.italic * font.italic + \
                                        QuickDraw.underline * font.underline
                Qd.TextFace( stylecode)
                return 1
                
        def close(self):
                self._window.close()
                self._window = None
        
        #------------ canvas capabilities -------------
        def isInteractive(self):
                "Returns 1 if onClick, onOver, and onKey events are possible, 0 otherwise."
                return 1
        
        def canUpdate(self):
                "Returns 1 if the drawing can be meaningfully updated over time \
                (e.g., screen graphics), 0 otherwise (e.g., drawing to a file)."
                # since we can update, but it gets progressively more expensive
                # until you call clear(), we'll return 0.5 for canUpdate
                return 0.5

        #------------ general management -------------

        def clear(self, andFlush=1):
                "Call this to clear and reset the graphics context."
                # in addition to clearing the screen, also reset our picture
                portsaver = _PortSaver(self)
                if self.picopen:
                        Qd.ClosePicture()
                self.picture = Qd.OpenPicture(self._window._bounds)
                self.picopen = 1
                self._prepareToDraw()
                _setBackColor(white)
                Qd.EraseRect( self._window._bounds )
                _setBackColor(self.defaultFillColor)
                if andFlush: self.flush()               # by default, we flush upon clear
                
        def flush(self):
                "Call this when done with drawing, to indicate that the drawing \
                should be printed/saved/blasted to screen etc."
                if not self.picopen: return
                portsaver = _PortSaver(self)
                Qd.ClosePicture()
                Qd.DrawPicture(self.picture, self._window._bounds)
                self.picopen = 0

        def setInfoLine(self, s):
                "For interactive Canvases, displays the given string in the \
                'info line' somewhere where the user can probably see it."
                if self._window:
                        portsaver = _PortSaver(self)
                        self._window.infoline = str(s)
                        self._window.drawInfoLine()
                
        #------------ string/font info ------------
        def stringWidth(self, s, font=None):
                "Return the logical width of the string if it were drawn \
                in the current font (defaults to self.font)."
                portsaver = _PortSaver(self)
                self._prepareToDraw()
                if font: self._setFont(font)
                return Qd.StringWidth(s)
        
        def fontHeight(self, font=None):
                "Find the line height of the given font."
                portsaver = _PortSaver(self)
                self._prepareToDraw()
                if font: self._setFont(font)
                fontinfo = Qd.GetFontInfo()
                return fontinfo[0] + fontinfo[1] + fontinfo[3]
        
        def fontAscent(self, font=None):
                "Find the ascent (height above base) of the given font."
                portsaver = _PortSaver(self)
                self._prepareToDraw()
                if font: self._setFont(font)
                return Qd.GetFontInfo()[0]
        
        def fontDescent(self, font=None):
                "Find the descent (extent below base) of the given font."
                portsaver = _PortSaver(self)
                self._prepareToDraw()
                if font: self._setFont(font)
                return Qd.GetFontInfo()[1]
                
        #------------- drawing methods --------------

        # Note default parameters "=None" means use the defaults
        # set in the Canvas method: defaultLineColor, etc.

        def drawLine(self, x1,y1, x2,y2, color=None, width=None):
                "Draw a straight line between x1,y1 and x2,y2."
                portsaver = _PortSaver(self)
                self._prepareToDraw()
                if color:
                        if color == transparent: return
                        _setForeColor(color)
                elif self.defaultLineColor == transparent: return
                if width!=None:
                        Qd.PenSize(width, width)
                        hw = (width-1)/2
                else: hw = (self.defaultLineWidth-1)/2
                if hw:
                        # adjust so that thick lines are centered on the given coordinates!
                        x1 = x1-hw
                        x2 = x2-hw
                        y1 = y1-hw
                        y2 = y2-hw
                Qd.MoveTo( x1,y1 )      # later: handle scaling!
                Qd.LineTo( x2,y2 )
                if color:
                        _setForeColor(self.defaultLineColor)
                if width: Qd.SetPenState(self._penstate)

        def drawRect(self, x1,y1, x2,y2, edgeColor=None, edgeWidth=None, fillColor=None):
                "Draw the rectangle between x1,y1, and x2,y2. \
                These should have x1<x2 and y1<y2."
                portsaver = _PortSaver(self)
                self._prepareToDraw()
                # first, draw the fill (if any)
                if fillColor:
                        if fillColor != transparent:
                                _setBackColor(fillColor)
                                Qd.EraseRect( (x1,y1, x2,y2) )
                else:
                        if self.defaultFillColor != transparent:
                                Qd.EraseRect( (x1,y1, x2,y2) )
                # then, draw the frame
                if edgeColor:
                        if edgeColor == transparent: return
                        _setForeColor(edgeColor)
                elif self.defaultLineColor == transparent: return
                if edgeWidth:
                        Qd.PenSize(edgeWidth, edgeWidth)
                        hw = (edgeWidth-1)/2
                else: hw = (self.defaultLineWidth-1)/2
                if hw:
                        # adjust so that thick lines are centered on the given coordinates!
                        x1 = x1-hw
                        x2 = x2+hw
                        y1 = y1-hw
                        y2 = y2+hw
                Qd.FrameRect( (x1,y1, x2+1,y2+1) )
                if edgeColor:
                        _setForeColor(self.defaultLineColor)
                if edgeWidth: Qd.SetPenState(self._penstate)

        def drawEllipse(self, x1,y1, x2,y2, edgeColor=None, edgeWidth=None, fillColor=None):
                "Draw an orthogonal ellipse inscribed within the rectangle x1,y1,x2,y2. \
                These should have x1<x2 and y1<y2."
                portsaver = _PortSaver(self)
                self._prepareToDraw()
                # first, draw the fill (if any)
                if fillColor:
                        if fillColor != transparent:
                                _setBackColor(fillColor)
                                Qd.EraseOval( (x1,y1, x2,y2) )
                elif self.defaultFillColor != transparent:
                        Qd.EraseOval( (x1,y1, x2,y2) )
                # then, draw the frame
                if edgeColor:
                        if edgeColor == transparent: return
                        _setForeColor(edgeColor)
                elif self.defaultLineColor == transparent: return
                if edgeWidth:
                        Qd.PenSize(edgeWidth, edgeWidth)
                        hw = (edgeWidth-1)/2
                else: hw = (self.defaultLineWidth-1)/2
                if hw:
                        # adjust so that thick lines are centered on the given coordinates!
                        x1 = x1-hw
                        x2 = x2+hw
                        y1 = y1-hw
                        y2 = y2+hw
                Qd.FrameOval( (x1,y1, x2+1,y2+1) )
                if edgeColor:
                        _setForeColor(self.defaultLineColor)
                if edgeWidth: Qd.SetPenState(self._penstate)

        def drawArc(self, x1,y1, x2,y2, startAng=0, extent=360,
                            edgeColor=None, edgeWidth=None, fillColor=None):
                "Draw a partial oval inscribed within the rectangle x1,y1,x2,y2, \
                starting at startAng degrees and covering extent degrees (counterclockwise). \
                These should have x1<x2, y1<y2, and angle1 < angle2."
                portsaver = _PortSaver(self)
                self._prepareToDraw()
                # first, draw the fill (if any)
                if fillColor:
                        if fillColor != transparent:
                                _setBackColor(fillColor)
                                Qd.EraseArc( (x1,y1, x2,y2), 90-startAng, -extent )
                elif self.defaultFillColor != transparent:
                        Qd.EraseOval( (x1,y1, x2,y2), 90-startAng, -extent )
                # then, draw the frame
                if edgeColor:
                        if edgeColor == transparent: return
                        _setForeColor(edgeColor)
                elif self.defaultLineColor == transparent: return
                if edgeWidth:
                        Qd.PenSize(edgeWidth, edgeWidth)
                        hw = (edgeWidth-1)/2
                else: hw = (self.defaultLineWidth-1)/2
                if hw:
                        # adjust so that thick lines are centered on the given coordinates!
                        x1 = x1-hw
                        x2 = x2+hw
                        y1 = y1-hw
                        y2 = y2+hw
                Qd.FrameArc( (x1,y1, x2+1,y2+1), 90-startAng, -extent )
                if edgeColor:
                        _setForeColor(self.defaultLineColor)
                if edgeWidth: Qd.SetPenState(self._penstate)


        def drawPolygon(self, pointlist, 
                                edgeColor=None, edgeWidth=None, fillColor=None, closed=0):
                """drawPolygon(pointlist) -- draws a polygon
                pointlist: a list of (x,y) tuples defining vertices
                """
                portsaver = _PortSaver(self)
                self._prepareToDraw()
                polygon = Qd.OpenPoly()
                filling = 0
                if fillColor:
                        if fillColor != transparent:
                                _setBackColor(fillColor)
                                filling = 1
                elif self.defaultFillColor != transparent:
                        filling = 1

                Qd.MoveTo(pointlist[0][0], pointlist[0][1])
                for p in pointlist[1:]:
                        Qd.LineTo(p[0],p[1])
                
                Qd.ClosePoly()
                if filling:
                        Qd.ErasePoly(polygon)
                        if fillColor:
                                _setBackColor(self.defaultFillColor)
                
                if edgeColor:
                        if edgeColor == transparent: return
                        _setForeColor(edgeColor)
                elif self.defaultLineColor == transparent: return
                if edgeWidth: Qd.PenSize(edgeWidth, edgeWidth)
                Qd.FramePoly(polygon)
                if closed:
                        Qd.MoveTo( pointlist[0][0], pointlist[0][1] )
                        Qd.LineTo( pointlist[-1][0], pointlist[-1][1] )
                if edgeColor:
                        _setForeColor(self.defaultLineColor)
                if edgeWidth: Qd.SetPenState(self._penstate)
                


        def drawString(self, s, x,y, font=None, color=None, angle=0):
                "Draw a string starting at location x,y."
                if '\n' in s or '\r' in s:
                        self.drawMultiLineString(s, x,y, font, color, angle)
                        return
                portsaver = _PortSaver(self)
                self._prepareToDraw()
                if font: self._setFont(font)
                if color:
                        if color == transparent: return
                        _setForeColor(color)
                elif self.defaultLineColor == transparent: return
                Qd.MoveTo( x,y )
                if angle:
                        import QDRotate
                        QDRotate.DrawRotatedString(s,angle)
                else:
                        Qd.DrawString(s)
                if font: self._setFont(self.defaultFont)
                if color:
                        _setForeColor(self.defaultLineColor)


        def drawImage(self, image, x1,y1, x2=None,y2=None):
                """Draw a PIL Image into the specified rectangle.  If x2 and y2 are
                omitted, they are calculated from the image size."""
        
                from PixMapWrapper import PixMapWrapper
                pm = PixMapWrapper()    # make a QD pixel map
                pm.fromImage(image)             # load the image into it
                if x2==None: x2 = x1 + pm.bounds[2]-pm.bounds[0]
                if y2==None: y2 = y1 + pm.bounds[3]-pm.bounds[1]
                self._prepareToDraw()
                Qd.ForeColor(QuickDraw.blackColor)
                Qd.BackColor(QuickDraw.whiteColor)
                pm.blit(x1,y1,x2,y2, self._port)
                _setForeColor(self.defaultLineColor)
                

#-------------------------------------------------------------------------

def test():
        global canvas
        
        # testing...
        try:
                canvas.close()
        except: pass

        canvas = QDCanvas()
        canvas.defaultLineColor = Color(0.7,0.7,1.0)    # light blue

        #import macfs
        #fsspec, ok = macfs.PromptGetFile("Image File:")
        #if not ok: return
        #path = fsspec.as_pathname()
        #import Image
        #canvas.drawImage( Image.open(path), 0,0,300,300 );

        def myOnClick(canvas,x,y): print("clicked %s,%s" % (x,y))
        canvas.onClick = myOnClick

        def myOnOver(canvas,x,y): canvas.setInfoLine( "mouse is over %s,%s" % (x,y) )

        canvas.onOver = myOnOver

        def myOnKey(canvas,key,mods): print("pressed %s with modifiers %s" % (key,mods))
        canvas.onKey = myOnKey
        

        canvas.drawLines( map(lambda i:(i*10,0,i*10,300), range(30)) )
        canvas.drawLines( map(lambda i:(0,i*10,300,i*10), range(30)) )
        canvas.defaultLineColor = black         
        
        canvas.drawLine(10,200, 20,190, color=red)
        canvas.drawEllipse( 130,30, 200,100, fillColor=yellow, edgeWidth=4 )
        
        canvas.drawArc( 130,30, 200,100, 45,50, fillColor=blue, edgeColor=navy, edgeWidth=4 )
        
        canvas.defaultLineWidth = 4
        canvas.drawRoundRect( 30,30, 100,100, fillColor=blue, edgeColor=maroon )
        canvas.drawCurve( 20,20, 100,50, 50,100, 160,160 )
        
        canvas.drawString("This is a test!", 30,130, Font(face="newyork",size=16,bold=1), 
                        color=green, angle=-45)
        
        polypoints = [ (160,120), (130,190), (210,145), (110,145), (190,190) ]
        canvas.drawPolygon(polypoints, fillColor=lime, edgeColor=red, edgeWidth=3, closed=1)
        
        canvas.drawRect( 200,200,260,260, edgeColor=yellow, edgeWidth=5 )
        canvas.drawLine( 200,260,260,260, color=green, width=5 )
        canvas.drawLine( 260,200,260,260, color=red, width=5 )

        
        canvas.flush()


#test()

