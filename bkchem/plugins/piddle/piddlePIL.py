# piddlePIL.py -- a Python Imaging Library backend for PIDDLE
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

"""piddlePIL

This module implements a Python Imaging Library PIDDLE canvas.
In other words, this is a PIDDLE backend that renders into a
PIL Image object.  From there, you can save as GIF, plot into
another PIDDLE canvas, etc.
        
Joe Strout (joe@strout.net), 10/26/99
"""

###  6/22/99: updated drawString to handle non-integer x and y

from .piddle import *
from PIL import Image
from PIL import ImageFont
import os, sys
Log =  sys.stderr

if __name__ == '__main__':
    _fontprefix = os.path.join(os.curdir,'pilfonts')
else:
    _fontprefix = os.path.join(os.path.split(__file__)[0],'pilfonts')

# load font metrics
try:
    f = open(os.path.join(_fontprefix,'metrics.dat'), 'rb')
    import pickle
    _widthmaps = pickle.load(f)
    _ascents = pickle.load(f)
    _descents = pickle.load(f)
    f.close()
except:
    Log.write("Warning: unable to load font metrics!\n")
    _widthmaps = {}
    _ascents = {}
    _descents = {}
#finally:
#   pass    # (just here so we can comment out the except clause for debugging)

def _closestSize(size):
    supported = [8,10,12,14,18,24]      # list of supported sizes
    if size in supported: return size
    best = supported[0]
    bestdist = abs(size-best)
    for trial in supported[1:]:
        dist = abs(size - trial)
        if dist < bestdist:
            best = trial
            bestdist = dist
    return best

def _pilFontPath(face,size,bold=0):
    if face == 'monospaced': face = 'courier'
    elif face == 'serif': face = 'times'
    elif face == 'sansserif' or face == 'system': face = 'helvetica'

    if bold and face != 'symbol': fname = "%s-bold-%d.pil" % (face,size)
    else: fname = "%s-%d.pil" % (face,size)
    path = os.path.join(_fontprefix,fname)
    return path

def _matchingFontPath(font):
    # returns a font path which matches info in our font metrics
    if font.face: face = font.face
    else: face = 'times'

    size = int(font.size)  # Use exact size without rounding
    if isinstance(face, str):
        path = _pilFontPath(face,size,font.bold)
        path = path.split(os.sep)[-1]
        if path in _widthmaps.keys(): return path
    else:
        for item in font.face:
            path = _pilFontPath(item,size,font.bold)
            path = path.split(os.sep)[-1]
            if path in _widthmaps.keys(): return path
    # not found?  Try it with courier, which should always be there
    path = _pilFontPath('courier',size,font.bold)
    return path.split(os.sep)[-1]

def _pilFont(font):
    from PIL import ImageFont
    if font.face: face = font.face
    else: face = 'times'

    # Use the exact font size without rounding
    size = int(font.size)  # Ensure it's an integer
    
    # Try modern TrueType font loading first
    try:
        # Map common font names to system fonts
        font_map = {
            'times': 'times.ttf',
            'helvetica': 'arial.ttf',
            'courier': 'cour.ttf',
            'arial': 'arial.ttf',
            'monospaced': 'cour.ttf',
            'serif': 'times.ttf',
            'sansserif': 'arial.ttf',
            'system': 'arial.ttf'
        }
        
        font_name = font_map.get(face.lower(), face.lower())
        
        # Try to load as TTF
        try:
            pilfont = ImageFont.truetype(font_name, size)
            if pilfont:
                return pilfont
        except:
            pass
            
        # Try common system font paths
        import os
        system_paths = [
            'C:/Windows/Fonts/',
            '/usr/share/fonts/truetype/',
            '/System/Library/Fonts/',
            '/Library/Fonts/'
        ]
        
        for path in system_paths:
            try:
                full_path = os.path.join(path, font_name)
                if os.path.exists(full_path):
                    pilfont = ImageFont.truetype(full_path, size)
                    if pilfont:
                        return pilfont
            except:
                pass
                
    except:
        pass
    
    # Fall back to old PIL font loading
    if isinstance(face, str):
        try: 
            pilfont = ImageFont.load_path(_pilFontPath(face,size,font.bold))
            if pilfont:
                return pilfont
        except:
            pass
    else:
        for item in font.face:
            try:
                pilfont = ImageFont.load_path(_pilFontPath(item,size,font.bold))
                if pilfont:
                    return pilfont
            except: 
                pass
    
    # Last resort: use default bitmap font
    try:
        return ImageFont.load_default()
    except:
        return 0  # font not found!


class PILCanvas( Canvas ):
    
    def __init__(self, size=(300,300), name='piddlePIL'):
        self._image = Image.new('RGB',size, (255,255,255))
        from PIL import ImageDraw
        self._pen = ImageDraw.ImageDraw(self._image)
        # Store default ink color for drawing operations
        self._ink_color = 0
        self._setFont( Font() )
        # PIL version check removed - using modern Pillow API
        self._pilversion = [10, 0, 0]  # Assume modern PIL/Pillow
        Canvas.__init__(self, size, name)
        
    def __setattr__(self, attribute, value):
        self.__dict__[attribute] = value
        if attribute == "defaultLineColor":
            self._setColor(self.defaultLineColor)

    # utility functions
    def _setColor(self,c):
        "Set the pen color from a piddle color."
        self._ink_color = (int(c.red*255), int(c.green*255), int(c.blue*255))

    def _setFont(self,font):
        self._pen.font = _pilFont(font)

    # public functions

    def getImage(self):
        return self._image
    
    def save(self, file=None, format=None):
        """format may be a string specifying a file extension corresponding to
                an image file format. Ex: 'png', 'jpg', 'gif', 'tif' etc."""
        file = file or self.name
        if hasattr(file, 'write'):
            self._image.save(file, format)
            return
                # below here, file is guaranteed to be a string
        if format == None:
            if '.' not in file:
                raise TypeError('no file type given to save()')
            filename = file
        else:
            filename = file + '.' + format
        self._image.save(filename)


        def clear(self) :
                # why is edgeColor yellow ???
                self.drawRect( 0,0,self.size[0],self.size[1], edgeColor=yellow,fillColor=white )
                ### FIXME: need to reset canvas as well to defaults ???


    #------------ string/font info ------------
    def stringWidth(self, s, font=None):
        "Return the logical width of the string if it were drawn \
        in the current font (defaults to self.defaultFont)."

        if not font: font = self.defaultFont
        if not _widthmaps:
            Log.write("warning no _widthmaps available\n")
            return font.size * len(s)

        path = _matchingFontPath(font)
        map = _widthmaps[path]
        out = 0
        for c in s:
            out = out + map[c]
        return out          
    
    def fontAscent(self, font=None):
        "Find the ascent (height above base) of the given font."

        if not font: font = self.defaultFont
        if not _ascents: return font.size
        
        path = _matchingFontPath(font)
        return _ascents[path]
    
    def fontDescent(self, font=None):
        "Find the descent (extent below base) of the given font."

        if not font: font = self.defaultFont
        if not _descents: return font.size/2
        
        path = _matchingFontPath(font)
        return _descents[path]
        
    #------------- drawing methods --------------
    def drawLine(self, x1,y1, x2,y2, color=None, width=None):
        "Draw a straight line between x1,y1 and x2,y2."
        # set color...
        if color:
            if color == transparent: return
            self._setColor(color)
        elif self.defaultLineColor == transparent: return
        
        if width: w = width
        else: w = self.defaultLineWidth
        if w > 1:
            # thick lines are not supported by PIL,
            # so we'll have to implement them as polygons
            hw = int((w-1)/2)
            pts = []
            if (x1<=x2 and y1<=y2):     # line down and to the right
                pts.append( (x1-hw+w,y1-hw) )
                pts.append( (x1-hw,  y1-hw) )
                pts.append( (x1-hw,  y1-hw+w) )

                pts.append( (x2-hw,  y2-hw+w) )
                pts.append( (x2-hw+w,y2-hw+w) )
                pts.append( (x2-hw+w,y2-hw) )

            elif (x1<=x2):              # line up and to the right
                pts.append( (x1-hw,  y1-hw) )
                pts.append( (x1-hw,  y1-hw+w) )
                pts.append( (x1-hw+w,y1-hw+w) )

                pts.append( (x2-hw+w,y2-hw+w) )
                pts.append( (x2-hw+w,y2-hw) )
                pts.append( (x2-hw,  y2-hw) )
                
            elif (y1<=y2):              # line down and to the left
                pts.append( (x1-hw+w,y1-hw+w) )
                pts.append( (x1-hw+w,y1-hw) )
                pts.append( (x1-hw,  y1-hw) )

                pts.append( (x2-hw,  y2-hw) )
                pts.append( (x2-hw,  y2-hw+w) )
                pts.append( (x2-hw+w,y2-hw+w) )
                
            else:                       # line up and to the left
                pts.append( (x1-hw,  y1-hw+w) )
                pts.append( (x1-hw+w,y1-hw+w) )
                pts.append( (x1-hw+w,y1-hw) )

                pts.append( (x2-hw+w,y2-hw) )
                pts.append( (x2-hw,  y2-hw) )
                pts.append( (x2-hw,  y2-hw+w) )
                
            pts = [tuple(int(coord) for coord in pt) for pt in pts]
            self._pen.polygon(pts, fill=self._ink_color)
            
        else:
            # for width <= 1, just use fast line method
            self._pen.line( (int(x1),int(y1),int(x2),int(y2)), fill=self._ink_color )


    def drawPolygon(self, pointlist, 
                edgeColor=None, edgeWidth=None, fillColor=None, closed=0):
        """drawPolygon(pointlist) -- draws a polygon
        pointlist: a list of (x,y) tuples defining vertices
        """
        # PIL's routine requires a sequence of tuples...
        # the input is not so restricted, so fix it
        pts = list(pointlist)
        pts = [tuple(int(coord) for coord in pt) for pt in pts]

        # set color for fill...
        filling = 0
        if fillColor:
            if fillColor != transparent:
                self._setColor(fillColor)
                filling = 1
        elif self.defaultFillColor != transparent:
            self._setColor(self.defaultFillColor)
            filling = 1

        # do the fill
        if filling:
            pts_fill = [tuple(int(coord) for coord in pt) for pt in pts]
            self._pen.polygon(pts_fill, fill=self._ink_color)
            
        # set color for edge...
        if edgeColor:
            self._setColor(edgeColor)
        else:
            self._setColor(self.defaultLineColor)

        if edgeColor != transparent:        
            # set edge width...
            if edgeWidth == None: edgeWidth = self.defaultLineWidth

            # draw the outline

            if (closed or (pts[0][0]==pts[-1][0] and pts[0][1]==pts[-1][1])) \
                     and edgeWidth <= 1:
                pts_outline = [tuple(int(coord) for coord in pt) for pt in pts]
                self._pen.polygon(pts_outline, outline=self._ink_color)
            else:
                # ...since PIL's polygon routine insists on closing,
                # and does not support thick edges, we'll use our drawLine instead
                # OFI: use default color/width to speed this up!
                oldp = pts[0]
                if closed: pts.append(oldp)
                for p in pts[1:]:
                    self.drawLine(oldp[0],oldp[1], p[0],p[1], edgeColor, edgeWidth)
                    oldp = p

    def drawString(self, s, x,y, font=None, color=None, angle=0):
        "Draw a string starting at location x,y."
        if '\n' in s or '\r' in s:
            self.drawMultiLineString(s, x,y, font, color, angle) 
            return
        if not font: font = self.defaultFont
        
        if not color:
            color = self.defaultLineColor
        if color == transparent: return

        # draw into an offscreen Image
        # tmpsize was originally 1.2* stringWidth, added code to give enough room for single character strings (piddle bug#121995)
        sHeight = (self.fontAscent(font) + self.fontDescent(font)) 
        sWidth = self.stringWidth(s, font)
        tempsize = int(max(sWidth*1.2, sHeight*2.0))

        tempimg = Image.new('RGB',(tempsize,tempsize), (0,0,0))
        from PIL import ImageDraw
        temppen = ImageDraw.ImageDraw(tempimg)
        # Draw white text on black background
        pilfont = _pilFont(font)
        if not pilfont: raise Exception("bad font!", font)
        temppen.font = pilfont
        pos = [4, int(tempsize/2 - self.fontAscent(font)) - self.fontDescent(font)]
        temppen.text((int(pos[0]), int(pos[1])), s, fill=(255,255,255))
        pos[1] = int(tempsize/2)
        
        # underline
        if font.underline:
            ydown = int(0.5 * self.fontDescent(font))
            temppen.line([(int(pos[0]), int(pos[1]+ydown)), (int(pos[0]+sWidth), int(pos[1]+ydown))])
            
        # rotate
        if angle:
            from math import pi, sin, cos
            tempimg = tempimg.rotate( angle, Image.Resampling.BILINEAR )
            temppen = ImageDraw.ImageDraw(tempimg)
            radians = -angle * pi/180.0
            r = tempsize/2 - pos[0]
            pos[0] = int(tempsize/2 - r * cos(radians))
            pos[1] = int(pos[1] - r * sin(radians))
            
        ### temppen.rectangle( (pos[0],pos[1],pos[0]+2,pos[1]+2) ) # PATCH for debugging
        # colorize, and copy it in
        mask = tempimg.convert('L').point(lambda c:c)
        # Fill temp image with target color
        color_tuple = (int(color.red*255), int(color.green*255), int(color.blue*255))
        temppen.rectangle((0, 0, tempsize, tempsize), fill=color_tuple)
        self._image.paste(tempimg, (int(x)-pos[0],int(y)-pos[1]), mask)       


        
    def drawImage(self, image, x1,y1, x2=None,y2=None):
        """Draw a PIL Image into the specified rectangle.  If x2 and y2 are
        omitted, they are calculated from the image size."""

        if x2 and y2:
            bbox = image.getbbox()
            if int(x2)-int(x1) != bbox[2]-bbox[0] or int(y2)-int(y1) != bbox[3]-bbox[1]:
                image = image.resize( (int(x2-x1), int(y2-y1)) )
        self._image.paste( image, (int(x1), int(y1)) )

def test():
#... for testing...
    canvas = PILCanvas()

    canvas.defaultLineColor = Color(0.7,0.7,1.0)    # light blue
    canvas.drawLines( [(i*10,0,i*10,300) for i in range(30)] )
    canvas.drawLines( [(0,i*10,300,i*10) for i in range(30)] )
    canvas.defaultLineColor = black     
    
    canvas.drawLine(10,200, 20,190, color=red)

    canvas.drawEllipse( 130,30, 200,100, fillColor=yellow, edgeWidth=4 )
    
    canvas.drawArc( 130,30, 200,100, 45,50, fillColor=blue, edgeColor=navy, edgeWidth=4 )
    
    canvas.defaultLineWidth = 4
    canvas.drawRoundRect( 30,30, 100,100, fillColor=blue, edgeColor=maroon )
    canvas.drawCurve( 20,20, 100,50, 50,100, 160,160 )
    
    canvas.drawString("This is a test!", 30,130, Font(face="times",size=16,bold=1), 
            color=green, angle=-45)

    canvas.drawString("This is a test!", 30,130, color=red, angle=-45)
    
    polypoints = [ (160,120), (130,190), (210,145), (110,145), (190,190) ]
    canvas.drawPolygon(polypoints, fillColor=lime, edgeColor=red, edgeWidth=3, closed=1)
    
    canvas.drawRect( 200,200,260,260, edgeColor=yellow, edgeWidth=5 )
    canvas.drawLine( 200,260,260,260, color=green, width=5 )
    canvas.drawLine( 260,200,260,260, color=red, width=5 )

    # now, for testing, save the image as a PNG file
    canvas.flush()
    canvas.getImage().save("test.png")

    
    return canvas

def testit(canvas, s, x,y, font=None):
    canvas.defaultLineColor = black
    canvas.drawString(s, x,y, font=font)
    canvas.defaultLineColor = blue
    w = canvas.stringWidth(s, font=font)
    canvas.drawLine(x,y, x+w,y)
    canvas.drawLine(x,y-canvas.fontAscent(font=font), x+w,y-canvas.fontAscent(font=font))
    canvas.drawLine(x,y+canvas.fontDescent(font=font), x+w,y+canvas.fontDescent(font=font)) 
    
def test2():
    
    canvas = PILCanvas()
    testit( canvas, "Foogar", 20, 30 )
    
    testit( canvas, "Foogar", 20, 90, font=Font(size=24) )
    global dammit
    dammit = _pilFont(Font(size=24))
    
    testit( canvas, "Foogar", 20, 150, font=Font(face='courier',size=24) )
    
    testit( canvas, "Foogar", 20, 240, font=Font(face='courier') )
    
    
    import piddleQD
    global qdcanvas
    try:
        qdcanvas.close()
    except: pass
    qdcanvas = piddleQD.QDCanvas()
    qdcanvas.drawImage( canvas.getImage(), 0, 0 );
    

if __name__ == '__main__': test()
    
