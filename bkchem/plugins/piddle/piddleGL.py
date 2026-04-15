#####
#
# glPiddle.py
#
#####
# 
# Copyright 1999 by David Ascher
# 
#                         All Rights Reserved
# 
# Permission to use, copy, modify, and distribute this software and its
# documentation for any purpose and without fee is hereby granted,
# provided that the above copyright notice appear in all copies and that
# both that copyright notice and this permission notice appear in
# supporting documentation, and that the name of David Ascher not be
# used in advertising or publicity pertaining to distribution of the
# software without specific, written prior permission.
# 
# DAVID ASCHER DISCLAIMS ALL WARRANTIES WITH REGARD TO THIS SOFTWARE,
# INCLUDING ALL IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS, IN NO
# EVENT SHALL DAVID ASCHER BE LIABLE FOR ANY SPECIAL, INDIRECT OR
# CONSEQUENTIAL DAMAGES OR ANY DAMAGES WHATSOEVER RESULTING FROM LOSS OF
# USE, DATA OR PROFITS, WHETHER IN AN ACTION OF CONTRACT, NEGLIGENCE OR
# OTHER TORTIOUS ACTION, ARISING OUT OF OR IN CONNECTION WITH THE USE OR
# PERFORMANCE OF THIS SOFTWARE.
#                      
#####

__version__ = 0.1 # public release -- Sep 28, 1999

# TODO: fix GLU Tesselation code for polygon handling
# TODO: fix font size information (ascent/descent), fix symbol font behavior
# TODO: document the ToglCanvas vs. GlutCanvas issues, as well as
#       GLTT vs. GLUT font handling
# TODO: document apparent GLTT bug which causes the glitch in the
#       basics test (missing character)
# TODO: document fact that OpenGL doesn't specify pixel-specific behavior,
#       which explains the spectrum issue.
# $Log: piddleGL.py,v $
# Revision 1.4  2000/08/03 23:03:24  clee
# revert  "import PIL as package" fix because it breaks under win32
#   - will try again for piddle 1.1 (possibly w/ PIL 1.1)
#



from .piddle import *
from OpenGL.GL import *
from OpenGL.GLU import *
try:
    # the tesselator is currently broken.  As the latest spec says
    # that polygon filling for non-simple polygons is undefined, it's
    # 'more or less' ok.  I will fix it.
    gluTessProperty
    _have_tesselator = 0
    class Combo:
        def beginCB(self, i):
            glBegin(i)
        def endCB(self):
            glEnd()
        def vertexCB(self, O):
            glVertex2d(O[0], O[1])
        def combineCB(self, p1, p2, p3):
            print(len(p3))
            return p3[0][-1]
        def edgeFlagCB(self, *args):
            pass
        combo = Combo()

except NameError:
    _have_tesselator = 0

from math import sin, cos, atan, pi
import os
_debug = 0
_tryGLTTFirst = 0

class _GLCanvas(Canvas):
    defaultFont = Font()
    def __init__(self, size=(300,300), name='piddleGL'):
        self._inList = 0
        self._lists = []
        if _have_tesselator:
            self.tesselator = gluNewTess()
        self.defaultTransparency = 1.0
        Canvas.__init__(self, size=size, name=name)
        
    def __setattr__(self, attribute, value):
        self.__dict__[attribute] = value
        if attribute == "defaultTransparency":
            if hasattr(self, 'defaultLineColor'):
                glColor4f(self.defaultLineColor.red,
                          self.defaultLineColor.green,
                          self.defaultLineColor.blue,
                          self.defaultTransparency)
        elif attribute == "defaultLineColor":
            if not self._inList: self._startList()
            glColor4f(self.defaultLineColor.red,
                      self.defaultLineColor.green,
                      self.defaultLineColor.blue,
                      self.defaultTransparency)
        elif attribute == "defaultLineWidth":
            if not self._inList: self._startList()
            glLineWidth(value/5.0)
        
    def __repr__(self):
        return '<GLCanvas at ' + str(id(self)) + '>'
    
    __str__=__repr__
    
    def clear(self):
        if self._inList: self._saveList()
        self._lists = []
        glClearColor(1,1,1,1)
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)

    def flush(self):
        glFlush()

    def _saveList(self):
        glEndList()
        self._inList = 0
        
    def _startList(self):
        list = glGenLists(1)
        self._lists.append(list)
        glNewList(list, GL_COMPILE)
        self._inList = 1

    def _glSetup(self):
        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        glOrtho(0, float(self._width), float(self._height), 0, 0, 1)
        glEnable(GL_POINT_SMOOTH)
        glEnable(GL_LINE_SMOOTH)
        glLineWidth(1.)
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        glClearColor(1,1,1,1)
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)

    def _drawList(self):
        if self._inList: self._saveList()
        int = type(1)
        for list in self._lists:
            if type(list) is int:
                glCallList(list)
            else:
                func, args, kw = list
                apply(func, args, kw)
        glFlush()
        
    def drawLine(self, x1,y1, x2,y2, color=None, width=None):
        "Draw a straight line between x1,y1 and x2,y2."
        if not self._inList: self._startList()
        if color is None:
            color = self.defaultLineColor
        glColor4f(color.red, color.green, color.blue, self.defaultTransparency)
        if width is None:
            width = self.defaultLineWidth
        glLineWidth(width)

        x1, x2 = min(x1, x2), max(x1, x2)
        y1, y2 = min(y1, y2), max(y1, y2)
        dx = x2-x1
        dy = y2-y1
        if abs(dx) < 0.001:
            a = pi/2.0
        else:
            a = atan(dy/dx)
        delta_x = width/2.0*cos(a)
        delta_y = width/2.0*sin(a)
        x1 = x1 - delta_x
        x2 = x2 + delta_x
        y1 = y1 - delta_y
        y2 = y2 + delta_y

        glBegin(GL_LINES)
        glVertex2f(x1, y1)
        glVertex2f(x2, y2)
        glVertex2f(0,0)
        glEnd()
        
    def drawPolygon(self, pointlist, 
                    edgeColor=None, edgeWidth=None, fillColor=None, closed=0):
        """drawPolygon(pointlist) -- draws a polygon
        pointlist: a list of (x,y) tuples defining vertices
        closed: if 1, adds an extra segment connecting the last point
                    to the first 
        """
        if not self._inList: self._startList()

        if closed: pointlist.append(pointlist[0])

        if fillColor is None:
            fillColor = self.defaultFillColor
        if fillColor is not transparent:
            glColor4f(fillColor.red, fillColor.green,
                      fillColor.blue, self.defaultTransparency)
            if _have_tesselator:
                self._drawTess(pointlist)
            else:
                glBegin(GL_POLYGON)
                for x,y in pointlist:
                    glVertex2f(x, y)
                glEnd()
	    #if self._inList: self._saveList()
	    #self._lists.append(self._drawTess, (pointlist,), {})
	    #self._startList()
        if edgeWidth is None:
            edgeWidth = self.defaultLineWidth
        if edgeColor is not transparent:
            glLineWidth(edgeWidth)
            if edgeColor is None:
                edgeColor = self.defaultLineColor
            glColor4f(edgeColor.red, edgeColor.green, edgeColor.blue,
                      self.defaultTransparency)
            glBegin(GL_LINE_STRIP)
            for x,y in pointlist:
                glVertex2f(x, y)
            glEnd()
    

    def _drawTess(self, pointlist):
        if _have_tesselator:
            gluTessNormal(self.tesselator, 0,0,1)
            gluTessProperty(self.tesselator,
			    GLU_TESS_WINDING_RULE,
			    GLU_TESS_WINDING_ODD)
            gluTessBeginPolygon(self.tesselator, combo)
            gluTessBeginContour(self.tesselator)
            for (x,y) in pointlist:
                gluTessVertex(self.tesselator, (x,y,0.0), (x,y,combo))
            gluTessEndContour(self.tesselator)
            gluTessEndPolygon(self.tesselator)
        else:
            glBegin(GL_POLYGON)
            for x,y in pointlist:
                glVertex2f(x, y)
            glEnd()

    # no colors apply to drawImage; the image is drawn as-is

    def drawImage(self, image, x1,y1, x2=None,y2=None):
        """Draw a PIL Image into the specified rectangle.  If x2 and y2 are
        omitted, they are calculated from the image size."""
        w, h = image.size
        if x2 is None: x2 = x1 + w
        if y2 is None: y2 = y1 + h
        glPixelZoom((x2-x1)/float(w), -(y2-y1)/float(h))
        glRasterPos2(x1,y1)
        # IMPORTANT -- otherwise can crash!
        glBitmap(0, 0, 0, 0, 0, 0)
        # in case we have files which aren't 4-byte aligned
        glPixelStorei(GL_UNPACK_ALIGNMENT, 1)
        # could be LUMINANCE, RGB, RGBA  (could add more, but why?)
        if image.mode == 'L':
            mode = GL_LUMINANCE
        elif image.mode == 'RGB':
            mode = GL_RGB
        elif image.mode == 'RGBA':
            mode = GL_RGBA
        else:
            image = image.convert('RGBA')
            mode = GL_RGBA
        glDrawPixels(w, h, mode, GL_UNSIGNED_BYTE, image.tostring())

    def save(self, fname):
        glFlush()
        base, ext = os.path.splitext(fname)
        if ext != '.ppm':
            try:
                import Image
            except ImportError:
                raise ImportError('Saving to a non-PPM format is not available because PIL is not installed')
            savefname = base+'.ppm'
            glSavePPM(savefname, self._width, self._height)
            i = Image.open(savefname)
            i.save(fname)
            os.unlink(savefname)
        else:
            glSavePPM(fname, self._width, self._height)

    def stringWidth(self, s, font=None):
        if font is None: font = self.defaultFont
        return FontWrapper(font).stringWidth(s)

    def fontHeight(self, font=None):
        if font is None: font = self.defaultFont
        return FontWrapper(font).fontHeight(s)

    def fontAscent(self, s='l', font=None):
        if font is None: font = self.defaultFont
        # XXX hack
        return FontWrapper(font).fontHeight(s)*.8

    def fontHeight(self, s='l', font=None):
        if font is None: font = self.defaultFont
        # XXX hack
        return FontWrapper(font).fontHeight(s)

    def fontDescent(self, s='g', font=None):
        if font is None: font = self.defaultFont
        # XXX hack
        return FontWrapper(font).fontHeight(s)*.2

    def drawString(self, s, x,y, font=None, color=None, angle=0):
        if '\n' in s or '\r' in s:
            self.drawMultiLineString(s, x,y, font, color, angle)
            return
        if color is None: color = self.defaultLineColor
        if font is None: font = self.defaultFont
        glColor4f(color.red, color.green,color.blue, 1)
        glTranslate(float(x),float(y),0)
        glScale(1,-1,1)
        glRotate(angle,0,0,1)
        # for some reason, GLTTFont calls can't be in CallLists
        self._saveList()
        self._lists.append(FontWrapper(font).render, (s, angle), {})
        self._startList()
        # end of workaround
        glRotate(-angle,0,0,1)
        glScale(1,-1,1)
        glTranslate(-float(x),-float(y),0)

from GLTT.GLTTFont import MyGLTTFont
def getGLTTFontWrapper():
    class FontWrapper(MyGLTTFont):
        maps = {'newyork': 'times',
                'times':'times',
                'serif': 'times',
                'sansserif': 'arial',
                'symbol': 'symbol',
                'monospaced': 'cour',
                'courier': 'cour',
                'helvetica': 'arial'}

        psfaces = {'arial': 'Helvetica',
		   'arialbd': 'Helvetica-Bold',
		   'ariali': 'Helvetica-Oblique',
		   'cour': 'Courier',
		   'courb': 'Courier-Bold',
		   'times': 'Times-Roman',
		   'timesbd': 'Times-Bold',
		   'timesi': 'Times-Italic',
		   'timesbi': 'Times-BoldItalic',
		   'symbol': 'Symbol'}

        def __init__(self, font):
            bold=font.bold
            italic=font.italic
            underline=font.underline
            face=font.face
            self.fsize=size=font.size
            if face is None: face = 'arial'
            face = string.lower(face)
            self.face = face
            if self.face in maps:
                face = self.maps[face]
            if bold:
                if italic:
                    boldflag = 'b'
                else:
                    boldflag = 'bd'
            else: boldflag = ''
            if italic: italflag = 'i'
            else: italflag = ''
            glttface = face + boldflag + italflag
            self.psface = self.psfaces.get(glttface, 'Courier')
            MyGLTTFont.__init__(self, glttface, size)

        def render(self, s, angle):
            if angle == 0:
                self.pfont.output(0,0, s)
            else:
                self.font.output(s)

        def fontHeight(self,s):
            return self.size(s)[1]

        def stringWidth(self,s):
            return self.pfont.getWidth(s)

    return FontWrapper

try:
    from OpenGL.GLUT import *
    class GlutCanvas(_GLCanvas):
        def __init__(self, size=(300,300), name='GlutCanvas'):
            width, height = size
            self._width = width
            self._height = height
            glutInit(name)
            glutInitDisplayMode(GLUT_DOUBLE | GLUT_RGB)
            glutInitWindowSize(width, height)
            glutCreateWindow(name)
            glutSetReshapeFuncCallback(self.reshape)
            glutReshapeFunc()
            glutSetDisplayFuncCallback(self.display)
            glutDisplayFunc()
            glutSetMouseFuncCallback(self.mouse)
            glutMouseFunc()
            glutSetKeyboardFuncCallback(self.keyboard)
            glutKeyboardFunc()
            _GLCanvas.__init__(self, size=size, name=name)

        def reshape(self, x, y):
            #glViewport(0, 0, x, y)
            self._winHeight = y

        def display(self):
            if self._inList: self._saveList()
            self._glSetup()
            glTranslate(0,-self._winHeight+self._height,0)
            self._drawList()
            glutSwapBuffers()

        def mouse(self, button, state, x, y):
            pass

        def keyboard(*args):
            print(args)

        def mainloop(self):
            glutMainLoop()
    if _debug: print("# GlutCanvas available")
except NameError:
    pass

try:
    import Tkinter
    from OpenGL.Tk import RawOpengl
    class TkInteractive:
        def __init__(self):
            self.bind('<Button-1>', self.mouseDown)
            self.bind('<B1-Motion>', self.mouseMove)
            self.bind('<Motion>', self.mouseMove)
            self.bind('<Key>', self.keyDown)

        def mouseDown(self, e):
            if hasattr(self, 'onClick'):
                self.onClick(self, e.x, e.y)

        def mouseMove(self, e):
            if hasattr(self, 'onOver'):
                self.onOver(self, e.x, e.y)

        def keyDown(self, e):
            if hasattr(self, 'onKey'):
                self.onKey(self, e.char, e.keysym)

    class ToglCanvas(_GLCanvas, RawOpengl, TkInteractive):
        def __init__(self, size=(300,300), name='piddleGL', 
                     master=None, double=1, depth=1,
                     **kw):
            width, height = size
            kw.update({'master':master,
                   'double':1,
                   'depth':depth,
                   'width':width,
                   'height':height})
            self._width = width
            self._height = height
            RawOpengl.__init__(*(self,), **kw)
            _GLCanvas.__init__(self, size=size, name=name)
            TkInteractive.__init__(self)
            self.bind('<Configure>', self.resize)
            self._texts = []

        def resize(self, e):
            w , h = e.width, e.height
            self.configure(width=w, height=h)
            self._width = w
            self._height= h 
            tkinter.Frame.configure(self)

        def redraw(self):
            if self._inList: self._saveList()
            self._glSetup()
            self._drawList()

        def isInteractive(self):
            return 1

        def canUpdate(self):
            return 1

        def setInfoLine(self, s):
            pass
    if _debug: print("# ToglCanvas available")
except ImportError:
    pass

try:
    GLCanvas = ToglCanvas
except NameError:
    GLCanvas = GlutCanvas
except NameError:
    raise ImportError("Couldn't get either GLUT or Togl loaded")

def getGLUTFontWrapper():
    class GLUTFontWrapper:
        maps = {'newyork': 'glutStrokeRoman',
                'times':'glutStrokeRoman',
                'serif': 'glutStrokeRoman',
                'sansserif': 'glutStrokeRomanFixed',
                'monospaced': 'glutStrokeRomanFixed',
                'courier': 'glutStrokeRomanFixed',
                'helvetica': 'glutStrokeRomanFixed'}

        def __init__(self, font):
            self.bold=font.bold
            face=font.face
            self.size=font.size
            if face is None: face = 'glutStrokeRomanFixed'
            face = string.lower(face)
            if self.face in maps:
                face = self.maps[face]
            self.glutface = face
        def stringWidth(self, s):
            x = 0
            for c in s:
                x = x + glutStrokeWidth(self.glutface, ord(c))
            return x * self.size / 100.0

        def fontHeight(self, s):
            return self.size

        def render(self, s, angle):
            glPushMatrix()
            if self.bold:
                glLineWidth(1.9)
            else:
                glLineWidth(1.0)
            glScale(1/100.0, 1/100.0, 1.0)
            glScale(self.size, self.size, 1.0)
            for c in s:
                glutStrokeCharacter(self.glutface, ord(c))
            glPopMatrix()

    return GLUTFontWrapper


if _tryGLTTFirst:
    firstTry = getGLTTFontWrapper
    secondTry = getGLUTFontWrapper
else:
    firstTry = getGLUTFontWrapper
    secondTry = getGLTTFontWrapper

try:
    FontWrapper = firstTry()
    FontSupport = 1 
except ImportError:
    try:
        FontWrapper = secondTry()
        FontSupport = 1 
    except ImportError:
        FontSupport = 0

if _debug:
    if FontSupport == 0:	
        print("# Can't find font support")
    else:
        print("# Using fonts from:", FontWrapper.__name__)
