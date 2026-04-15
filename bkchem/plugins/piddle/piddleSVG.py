# Copyright (C) 2000  Greg Landrum
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

"""piddleSVG

This module implements an SVG PIDDLE canvas.
In other words, this is a PIDDLE backend that renders into a
SVG file.

Bits have been shamelessly cobbled from piddlePDF.py and/or
piddlePS.py
		
Greg Landrum (greglandrum@earthlink.net) 3/10/2000
"""

"""
  Functionality implemented:
  -drawLine
  -drawPolygon
  -drawEllipse
  -drawArc
  -drawCurve
  -drawString (rotated text is, mostly, fine... see below)
  -drawFigure
  -drawImage

  Known problems:
   -Rotated text is right in either IBM's SVGView or Adobe's plugin.  This
    problem is explained in drawString()
   -The font/string handling is not perfect.  There are definite problems
    with getting the widths of strings.  Thus far heights seem to work okay
    in the tests that I've done, but those could well be broken as well.

"""

from .piddle import *
from . import pdfmetrics # for font info
import string, os

from math import *

SVG_HEADER = """<?xml version="1.0" encoding="iso-8859-1"?>
<!DOCTYPE svg PUBLIC "-//W3C//DTD SVG 03December 1999//EN"
"SVG-19991203.dtd">
"""

def _ColorToSVG(color):
  """ convenience function for converting a PIDDLE color to an SVG color

  """
  if color == transparent:
    return 'none'
  else:
    return 'rgb(%d,%d,%d)'%(int(color.red*255),int(color.green*255),
                            int(color.blue*255))
def _PointListToSVG(points,dupFirst=0):
  """ convenience function for converting a list of points to a string
      suitable for passing to SVG path operations

  """
  outStr = ''
  for i in range(len(points)):
    outStr = outStr + '%.2f,%.2f '%(points[i][0],points[i][1])
  # add back on the first point.  This is not required in the spec,
  #  but Adobe's beta-quality viewer seems to not like it being skipped
  if dupFirst == 1:
    outStr = outStr + '%.2f,%.2f'%(points[0][0],points[0][1])
  return outStr

class SVGCanvas( Canvas ):
  def __init__(self, size=(300,300), name='SVGCanvas'):
    self._nImages=1
    # I'd rather do this as PNG, but IBM's SVGView doesn't support those
    #  yet. Adobe's plugin works just fine with them, however.
    self._imageFormat='GIF'
    self.size = size
    self._initOutput()
    Canvas.__init__(self, size, name)

  def _initOutput(self):
    self._txt = SVG_HEADER +\
                '<svg xml:space="preserve" width="%dpx" height="%dpx">\n'%self.size
    
  def _findExternalFontName(self, font):       #copied from piddlePDF by cwl- hack away!
        """Attempts to return proper font name.
        PDF uses a standard 14 fonts referred to
        by name. Default to self.defaultFont('Helvetica').
        The dictionary allows a layer of indirection to
        support a standard set of PIDDLE font names."""

        piddle_font_map = {
            'Times':'Times',
            'times':'Times',
            'Courier':'Courier',
            'courier':'Courier',
            'helvetica':'Helvetica',
            'Helvetica':'Helvetica',
            'symbol':'Symbol',
            'Symbol':'Symbol',
            'monospaced':'Courier',
            'serif':'Times',
            'sansserif':'Helvetica',
            'ZapfDingbats':'ZapfDingbats',
            'zapfdingbats':'ZapfDingbats',
            'arial':'Helvetica'
            }

        try:
            face = piddle_font_map[font.face.lower()]
        except:
            return piddle_font_map['sansserif'.lower()]

        name = face + '-'
        if font.bold and face in ['Courier','Helvetica','Times']:
            name = name + 'Bold'
        if font.italic and face in ['Courier', 'Helvetica']:
            name = name + 'Oblique'
        elif font.italic and face == 'Times':
            name = name + 'Italic'

        if name == 'Times-':
            name = name + 'Roman'
        # symbol and ZapfDingbats cannot be modified!

        #trim and return
        if name[-1] == '-':
            name = name[0:-1]
        return name

  def _FormFontStr(self,font):
    """ form what we hope is a valid SVG font string.
      Defaults to 'sansserif'
      This should work when an array of font faces are passed in.
    """
    fontStr = ''
    if font.face is None:
      font.face = 'sansserif'
    if isinstance(font.face, str):
      if len(font.face.split()) > 1:
        familyStr = '\'%s\''%font.face
      else:
        familyStr = font.face
    else:
      face = font.face[0]
      if len(face.split()) > 1:
        familyStr = '\'%s\''%(face)
      else:
        familyStr = face
      for i in range(1,len(font.face)):
        face = font.face[i]
        if len(face.split()) > 1:
          familyStr = ', \'%s\''%(face)
        else:
          familyStr = familyStr + ', %s'%face
    if font.italic:
      styleStr = 'font-style:italic;'
    else:
      styleStr = ''
    if font.bold:
      weightStr = 'font-weight:bold;'
    else:
      weightStr = ''
    if font.size:
      sizeStr = 'font-size:%.2f;'%font.size
    else:
      sizeStr = ''

    fontStr = 'font-family: %s; %s %s %s'%(familyStr,styleStr,weightStr,sizeStr)
    return fontStr

  def _FormArcStr(self,x1,y1,x2,y2,theta1,extent):
    """ Forms an arc specification for SVG
    
    """
    if abs(extent) > 360:
      if extent < 0:
        extent = -abs(extent)%360
      else:
        extent = extent%360
    
    # deal with figuring out the various arc flags
    #  required by SVG.
    if extent > 180:   # this one is easy
      arcFlag = 1
    else:
      arcFlag = 0

    if extent >=0: 
      sweepFlag = 0
    else:
      sweepFlag = 1

    # convert angles to radians (grn)
    theta1 = pi * theta1 / 180.
    extent = pi * extent / 180.

    # center of the arc
    cx = (x1+x2)/2.
    cy = (y1+y2)/2.
    # its radius
    rx = abs(x2 - x1)/2.
    ry = abs(y2 - y1)/2.    

    # final angle
    theta2 = theta1 + extent

    # SVG takes arcs as paths running from one point to another.
    #  figure out what those start and end points are now.
    #  the -thetas are required because of a difference in the handedness
    #  of angles in Piddle and SVG
    startx = cx + rx*cos(-theta1)
    starty = cy + ry*sin(-theta1)
    endx = cx + rx*cos(-theta2)
    endy = cy + ry*sin(-theta2)

    arcStr = '%.2f %.2f A%.2f %.2f 0 %d %d %.2f %.2f'%(startx,starty,rx,ry,
                                                       arcFlag,sweepFlag,
                                                       endx,endy)
    return arcStr

  # public functions
  def clear(self):
    self._initOutput()

  def flush(self):
    pass
    
  def save(self, file=None, type='svg'):
    if file:
      self.name = file
    if type == '':
      if '.' not in self.name:
        raise TypeError('no file type given to save()')
      filename = self.name
    else:
      if '.' not in self.name:
        filename = self.name + '.' + type
      else:
        filename = self.name
    outFile = open(filename,'w+')
    outFile.write(self._txt+'</svg>')
    outFile.close()
    #print filename, "saved"


  #------------- drawing methods --------------
  def drawLine(self, x1,y1, x2,y2, color=None, width=None):
    "Draw a straight line between x1,y1 and x2,y2."
    # set color...
    if color:
      if color == transparent: return
    elif self.defaultLineColor == transparent:
      return
    else:
      color = self.defaultLineColor
      
    svgColor = _ColorToSVG(color)

    if width:
      w = width
    else:
      w = self.defaultLineWidth
    styleStr = '"stroke:%s; stroke-width:%d"'%(svgColor,w)
    outStr = '<line x1="%.2f" y1="%.2f" x2="%.2f" y2="%.2f" style=%s />\n'%(x1,y1,x2,y2,styleStr)
    self._txt = self._txt + outStr
    

  def drawPolygon(self, pointlist, 
                  edgeColor=None, edgeWidth=None, fillColor=transparent, closed=0):
    """drawPolygon(pointlist) -- draws a polygon
    pointlist: a list of (x,y) tuples defining vertices
    """

    # get the points into SVG format
    pointStr = _PointListToSVG(pointlist,dupFirst=closed)

    # set color for fill...
    filling = 0
    if fillColor:
      if fillColor != transparent:
        filling = 1
          
    # do the fill
    if filling:
      fillStr = 'fill:%s;'%_ColorToSVG(fillColor)
    else:
      fillStr = 'fill:none;'

    # set color for edge...
    if not edgeColor:
      edgeColor = self.defaultLineColor
    # set edge width...
    if edgeWidth == None: edgeWidth = self.defaultLineWidth

    # SVG markers
    edgeStr = 'stroke:%s; stroke-width:%d;'%(_ColorToSVG(edgeColor),int(edgeWidth))

    # draw it
    outStr = '<polygon style="%s %s" points="%s"/>\n'%(fillStr,edgeStr,pointStr)
    self._txt = self._txt + outStr

  def drawEllipse(self, x1,y1,x2,y2,
                  edgeColor=None, edgeWidth=None, fillColor=transparent):

    # get the points into SVG format
    cx = (x1+x2)/2.
    cy = (y1+y2)/2.
    rx = abs(x2 - x1)/2.
    ry = abs(y2 - y1)/2.    
    ellipseStr = 'cx="%.2f" cy="%.2f" rx="%.2f" ry="%.2f"'%(cx,cy,rx,ry)

    # set color for fill...
    filling = 0
    if fillColor:
      if fillColor != transparent:
        filling = 1
          
    # do the fill
    if filling:
      fillStr = 'fill:%s;'%_ColorToSVG(fillColor)
    else:
      fillStr = 'fill:none;'

    # set color for edge...
    if not edgeColor:
      edgeColor = self.defaultLineColor
    # set edge width...
    if edgeWidth == None: edgeWidth = self.defaultLineWidth

    edgeStr = 'stroke:%s; stroke-width:%d;'%(_ColorToSVG(edgeColor),int(edgeWidth))

    # draw it
    outStr = '<ellipse style="%s %s" %s/>\n'%(fillStr,edgeStr,ellipseStr)
    self._txt = self._txt + outStr


  def drawArc(self, x1,y1,x2,y2,theta1=0,extent=360,
              edgeColor=None, edgeWidth=None, fillColor=None):

    # set color for fill...
    filling = 0
    if not fillColor:
      fillColor = self.defaultFillColor

    if fillColor != transparent:
      filling = 1

          
    # do the fill
    if filling:
      fillStr = 'fill:%s;'%_ColorToSVG(fillColor)
    else:
      fillStr = 'fill:none;'
    arcStr = self._FormArcStr(x1,y1,x2,y2,theta1,extent)

    if not filling:
      pathStr = 'M' + arcStr
    else:
      # this is a bit trickier.  Piddle requires filled arcs to stroke the
      #  arc bit and fill into the middle (like a piece of pie) without
      #  stroking the lines to the middle.  So we need *two* paths here.
      strokePathStr = 'M' + arcStr
      cx = (x1 + x2)/2.
      cy = (y1 + y2)/2.
      fillPathStr = 'M%.2f %.2f L%sZ'%(cx,cy,arcStr)

    # set color for edge...
    if not edgeColor:
      edgeColor = self.defaultLineColor
    # set edge width...
    if edgeWidth == None: edgeWidth = self.defaultLineWidth

    # SVG markers
    edgeStr = 'stroke:%s; stroke-width:%d;'%(_ColorToSVG(edgeColor),int(edgeWidth))

    # draw it
    if not filling:
      outStr = '<path style="%s %s" d="%s"/>\n'%(fillStr,edgeStr,pathStr)
    else:
      outStr = '<path style="%s" d="%s"/>\n'%(fillStr,fillPathStr)
      outStr = outStr+'<path style="fill:none; %s" d="%s"/>\n'%(edgeStr,strokePathStr)      
    self._txt = self._txt + outStr

  def drawCurve(self, x1,y1,x2,y2,x3,y3,x4,y4,
                  edgeColor=None, edgeWidth=None, fillColor=transparent, closed=0):

    # get the points into SVG format
    curveStr = 'M%.2f %.2f C%.2f %.2f %.2f %.2f %.2f %.2f'%(x1,y1,x2,y2,x3,y3,x4,y4)
    if closed:
      curveStr = curveStr + 'Z'

    # set color for fill...
    filling = 0
    if fillColor:
      if fillColor != transparent:
        filling = 1
          
    # do the fill
    if filling:
      fillStr = 'fill:%s;'%_ColorToSVG(fillColor)
    else:
      fillStr = 'fill:none;'

    # set color for edge...
    if not edgeColor:
      edgeColor = self.defaultLineColor

    # set edge width...
    if edgeWidth == None: edgeWidth = self.defaultLineWidth

    # SVG markers
    edgeStr = 'stroke:%s; stroke-width:%d;'%(_ColorToSVG(edgeColor),int(edgeWidth))

    # draw it
    outStr = '<path style="%s %s" d="%s"/>\n'%(fillStr,edgeStr,curveStr)
    self._txt = self._txt + outStr

  
  def drawString(self, s, x,y, font=None, color=None, angle=0):
    # set color...
    if color:
      if color == transparent: return
    elif self.defaultLineColor == transparent:
      return
    else:
      color = self.defaultLineColor
    if font is None:
      font = self.defaultFont
    if font:
      fontStr = self._FormFontStr(font)
    else:
      fontStr = ''
      
    svgColor = _ColorToSVG(color)

    outStr = ''
    if angle != 0:
      # note: this is the correct order of the transforms according to my reading of
      #  the SVG spec and the behavior of Adobe's SVG plugin.  If you want it to work
      #  in IBM's SVGView, you'll have to use the second (commented out) form.
      # Ah, the joys of using mature technologies. ;-)
      outStr = outStr + '<g transform="translate(%.2f,%.2f) rotate(%.2f)">\n'%(x,y,360-angle)
      #outStr = outStr + '<g transform="rotate(%.2f) translate(%.2f,%.2f)">\n'%(360-angle,x,y)
      xLoc = 0
      yLoc = 0
    else:
      xLoc = x
      yLoc = y
    lines = s.split('\n')
    lineHeight = self.fontHeight(font)
    yP = yLoc
    for line in lines:
      outStr = outStr + self._drawStringOneLine(line,xLoc,yP,fontStr,svgColor)
      yP = yP + lineHeight

    if angle != 0:
      outStr = outStr + '</g>'

    self._txt = self._txt + outStr
		
  def _drawStringOneLine(self,line,x,y,fontStr,svgColor):
    styleStr = 'style="%s stroke:%s"'%(fontStr,svgColor)
    return '  <text %s x="%.2f" y="%.2f">%s</text>\n'%(styleStr,x,y,line)

  def drawFigure(self, partList,
                 edgeColor=None, edgeWidth=None, fillColor=None, closed=0):
    """drawFigure(partList) -- draws a complex figure
    partlist: a set of lines, curves, and arcs defined by a tuple whose
    first element is one of figureLine, figureArc, figureCurve
    and whose remaining 4, 6, or 8 elements are parameters."""

    filling = 0
    if fillColor:
      if fillColor != transparent:
        filling = 1
          
    # do the fill
    if filling:
      fillStr = 'fill:%s;'%_ColorToSVG(fillColor)
    else:
      fillStr = 'fill:none;'

    # set color for edge...
    if not edgeColor:
      edgeColor = self.defaultLineColor
    # set edge width...
    if edgeWidth == None: edgeWidth = self.defaultLineWidth

    # SVG markers
    edgeStr = 'stroke:%s; stroke-width:%d;'%(_ColorToSVG(edgeColor),int(edgeWidth))

    pathStr = ''
    for item in partList:
      op = item[0]
      args = list(item[1:])

      if pathStr == '':
        pathStr = pathStr + 'M'
      else:
        pathStr = pathStr + 'L'          
      if op == figureLine:
        pathStr = pathStr + '%.2f %.2f L%.2f %.2f'%(tuple(args))
      elif op == figureCurve:
        pathStr = pathStr + '%.2f %.2f C%.2f %.2f %.2f %.2f %.2f %.2f'%(tuple(args))
      elif op == figureArc:
        x1,y1,x2,y2,theta1,extent=tuple(args)
        pathStr = pathStr + self._FormArcStr(x1,y1,x2,y2,theta1,extent)

      else:
        raise TypeError("unknown figure operator: "+op)

    if closed == 1:
      pathStr = pathStr + 'Z'
    outStr = '<path style="%s %s" d="%s"/>\n'%(edgeStr,fillStr,pathStr)
    self._txt = self._txt + outStr

  def drawImage(self, image, x1,y1, x2=None,y2=None):
    """
      to the best of my knowledge, the only real way to get an image
      into SVG is to read it from a file.  So we'll save out to a PNG
      file, then set a link to that in the SVG.
    """
    imageFileName= '%s-%d.%s'%(self.name,self._nImages,self._imageFormat.lower())
    self._nImages = self._nImages + 1
    image.save(imageFileName,format=self._imageFormat)

    im_width,im_height=image.size
    if x2 is not None:
      im_width = abs(x2-x1)
    if y2 is not None:
      im_height = abs(y2-y1)
    outStr = '<image x="%.2f" y="%.2f" width="%.2f" height="%.2f" xlink:href="%s"/>\n'%\
             (x1,y1,im_width,im_height,imageFileName)
    self._txt = self._txt + outStr

  def stringWidth(self, s, font=None):
    "Return the logical width of the string if it were drawn \
    in the current font (defaults to self.font)."
    if not font:
      font = self.defaultFont
    fontname = self._findExternalFontName(font)
    return pdfmetrics.stringwidth(s, fontname) * font.size * 0.001

  def fontAscent(self, font=None):
    if not font:
      font = self.defaultFont
    #return -font.size
    fontname = self._findExternalFontName(font)
    return pdfmetrics.ascent_descent[fontname][0] * 0.001 * font.size

  def fontDescent(self, font=None):
    if not font:
      font = self.defaultFont
    fontname = self._findExternalFontName(font)
    return -pdfmetrics.ascent_descent[fontname][1] * 0.001 * font.size


def test():
  #... for testing...
  canvas = SVGCanvas(name="test")

  canvas.defaultLineColor = Color(0.7,0.7,1.0)	# light blue
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

  canvas.flush()

def testit(canvas, s, x,y, font=None):
  canvas.defaultLineColor = black
  canvas.drawString(s, x,y, font=font)
  canvas.defaultLineColor = blue
  w = canvas.stringWidth(s, font=font)
  canvas.drawLine(x,y, x+w,y)
  canvas.drawLine(x,y-canvas.fontAscent(font=font), x+w,y-canvas.fontAscent(font=font))
  canvas.drawLine(x,y+canvas.fontDescent(font=font), x+w,y+canvas.fontDescent(font=font))	

def test2():

  canvas = SVGCanvas(name="Foogar")
  testit( canvas, "Foogar", 20, 30 )

  testit( canvas, "Foogar", 20, 90, font=Font(size=24) )
  global dammit

  testit( canvas, "Foogar", 20, 150, font=Font(face='courier',size=24) )

  testit( canvas, "Foogar", 20, 240, font=Font(face='courier') )
  canvas.flush()

if __name__ == '__main__':
  test()
  test2()
