""" 
A Tkinter based backend for piddle. 
  
Perry A. Stoll 
  
Created: February 15, 1999 
  
Requires PIL for rotated string support.

Known Problems: 
     - Doesn't handle the interactive commands yet.
     - PIL based canvas inherits lack of underlining strings from piddlePIL
     
You can find the latest version of this file:
    via http://piddle.sourceforge.net
""" 

import tkinter
import tkinter.font as tkFont
from . import piddle 
import string
  
__version__ = "0.3" 
__date__    = "April 8, 1999" 
__author__  = "Perry Stoll,  perry.stoll@mail.com " 

# fixups by chris lee, cwlee@artsci.wustl.edu
# $Id: piddleTK.py,v 1.5 2000/11/11 18:31:21 clee Exp $
# - added drawImage scaling support
# - shifted baseline y parameter in drawString to work around font metric
#         shift due to Tkinter's Canvas text_item object
# - fixed argument names so that argument keywords agreed with piddle.py (passes discipline.py)
#
#
# ToDo: for BaseTKCanvas
#         make sure that fontHeight() is returnng appropriate measure.  Where is this info?
#     
# $Log: piddleTK.py,v $
# Revision 1.5  2000/11/11 18:31:21  clee
# add method getTkinter(..) to retrieve underlying tkinter canvas
#
# Revision 1.4  2000/02/26 23:12:42  clee
# turn off compression by default on piddlePDF
# add doc string to new pil-based piddleTK
#
# Revision 1.3  2000/02/26 21:23:19  clee
# update that makes PIL based TKCanvas the default Canvas for TK.
# Updated piddletest.py.  Also, added clear() methdo to piddlePIL's
# canvas it clears to "white" is this correct behavior?  Not well
# specified in current documents.
#
# ToDo:
#   - document special access methods

class FontManager:
    __alt_faces = { "serif": "Times",
                    "sansserif": "Helvetica",
                    "monospaced": "Courier"}
    def __init__(self):
        self.font_cache = {}

    # the main interface
    def stringWidth(self, s, font):
        tkfont = self.piddleToTkFont(font)
        return tkfont.measure(s)

    def fontHeight(self, font):
        tkfont = self.piddleToTkFont(font)
        return self._tkfontHeight(tkfont) 
    
    def fontAscent(self, font):
        tkfont = self.piddleToTkFont(font)
        return self._tkfontAscent(tkfont)

    def fontDescent(self, font):
        tkfont = self.piddleToTkFont(font)
        return self._tkfontDescent(tkfont)

    def getTkFontString(self, font):
        """Return a string suitable to pass as the -font option to
        to a Tk widget based on the piddle-style FONT"""
        tkfont = self.piddleToTkFont(font)
        # XXX: should just return the internal tk font name?
        # return str(tkfont)
        return ('-family %(family)s -size %(size)s '
                '-weight %(weight)s -slant %(slant)s '
                '-underline %(underline)s' % tkfont.config())
    

    def getTkFontName(self, font):
        """Return a the name associated with the piddle-style FONT"""
        tkfont = self.piddleToTkFont(font)
        return str(tkfont)

    def piddleToTkFont(self, font): 
        """Return a tkFont instance based on the piddle-style FONT"""
        if font is None: 
            return ''

        if font.face:
            # check if the user specified a generic face type
            # like serif or monospaced. check is case-insenstive.
            f = font.face.lower()
            if self.f in __alt_faces:
                family = self.__alt_faces[f]
            else:
                family = font.face
        else:
            # if no face is specified
            family = "Times"
            
        size = font.size or 12

        if font.bold:
            weight = 'bold'
        else:
            weight = 'normal'

        if font.italic:
            slant = 'italic'
        else:
            slant = 'roman'

        if font.underline:
            underline = 'true'
        else:
            underline = 'false'

        # ugh... is there a better way to do this?
        key = (family,size,weight,slant,underline)

        # check if we've already seen this font.
        if self.key in font_cache:
            # yep, don't bother creating a new one. just fetch it.
            font = self.font_cache[key]
        else:
            # nope, let's create a new tk font.
            # this way we will return info about the actual font
            # selected by Tk, which may be different than what we ask
            # for if it's not availible.
            font = tkFont.Font(family=family, size=size, weight=weight,
                               slant=slant,underline=underline)
            self.font_cache[(family,size,weight,slant,underline)] = font
        
        return font

    def _tkfontAscent(self, tkfont):
        return tkfont.metrics("ascent")

    def _tkfontDescent(self, tkfont):
        return tkfont.metrics("descent")


class BaseTKCanvas(piddle.Canvas): 

    __TRANSPARENT = ''                  # transparent for Tk color
    def __init__(self, size=(0,0), name="piddleTK", master = None): 
        piddle.Canvas.__init__(self, size, name)
        self.draw_width, self.draw_height = size 
        self._create_widgets(master) 

        self._font_manager = FontManager()
        # XXX: do we need this?
        # keep track of the ids of all objects created so we 
        # can delete them later 
        self._item_ids = [] 
        self._images   = []
        
    def _create_widgets(self, master): 
  
        draw_area = tkinter.Canvas(master = master, 
                                   height=self.draw_height, 
                                   width=self.draw_width, 
                                   relief=tkinter.SUNKEN, 
                                   background="white", 
                                   borderwidth=2) 
        #draw_area.tk.call('package','require','Tkimaging')
        self.draw_area = draw_area 
        self.draw_area.pack() 
  
        self.quit_btn = tkinter.Button(master, 
                                       text='QUIT', 
                                       foreground='red', 
                                       command = self._quit) 
        self.quit_btn.pack(side=tkinter.LEFT) 
  
        self.clear_btn = tkinter.Button(master, 
                                        text='CLEAR', 
                                        foreground='red', 
                                        command = self.clear) 
        self.clear_btn.pack(side=tkinter.LEFT) 
  
    # special access method for underlying tkinter.Canvas
    def getTkinterCanvas(self):
        return self.draw_area()
          
    def _display(self): 
        self.flush()
        self.draw_area.mainloop() 
  
    def _quit(self): 
        self.draw_area.quit() 

    # Hmmm...the postscript generated by this causes my Ghostscript to barf... 
    def _to_ps_file(self, filename): 
        self.draw_area.postscript(file=filename) 
          
  
    def flush(self): 
        self.draw_area.update() 
  
    def clear(self): 
        for item_id in self._item_ids:
            self.draw_area.delete(item_id) 
        self._item_ids = [] 
        self._images   = []
        
    def _colorToTkColor(self, c): 
        return "#%02X%02X%02X" %( int(c.red*255), 
                                  int(c.green*255), 
                                  int(c.blue*255)) 
  
    def _getTkColor(self, color, defaultColor): 
        if color is None: 
            color = defaultColor 
        if color is piddle.transparent: 
            color = self.__TRANSPARENT
        else: 
            color = self._colorToTkColor(color) 
        return color 
  
    def drawLine(self, x1, y1, x2, y2, color = None, width = None): 
        color = self._getTkColor(color, self.defaultLineColor) 
        if width is None: 
            width  = self.defaultLineWidth 
        new_item = self.draw_area.create_line(x1,y1,x2,y2,
                                              fill=color, width=width) 
        self._item_ids.append(new_item) 
  
    # NYI: curve with fill 
    #def drawCurve(self, x1, y1, x2, y2, x3, y3, x4, y4, 
    #              edgeColor=None, edgeWidth=None, fillColor=None, closed=0): 
    # 

    def stringWidth(self, s, font=None):
        return self._font_manager.stringWidth(s, font or self.defaultFont)
    
    def fontAscent(self, font=None):
        return self._font_manager.fontAscent(font or self.defaultFont)

    def fontDescent(self, font=None):
        return self._font_manager.fontDescent(font or self.defaultFont)

    def drawString(self, s, x, y, font=None, color=None, angle=None): 
        # fudge factor for TK on linux (at least)
        # strings are being drawn using create_text in canvas
        y = y - self.fontHeight(font) * .28 # empirical
        #y = y - self.fontDescent(font)
    
        color = self._getTkColor(color, self.defaultLineColor) 
        font  = self._font_manager.getTkFontString(font or self.defaultFont) 
        new_item = self.draw_area.create_text(x, y, text=s, 
                                              font=font, fill=color, 
                                              anchor=tkinter.W 
                                              ) 
        self._item_ids.append(new_item) 
  
    def drawRect(self, x1, y1, x2, y2, edgeColor=None, 
                 edgeWidth=None, fillColor=None): 
        fillColor = self._getTkColor(fillColor, self.defaultFillColor) 
        edgeColor = self._getTkColor(edgeColor, self.defaultLineColor) 
        if edgeWidth is None: 
            edgeWidth  = self.defaultLineWidth 
        new_item = self.draw_area.create_rectangle(x1,y1,x2,y2, 
                                                   fill=fillColor, 
                                                   width=edgeWidth, 
                                                   outline=edgeColor) 
        self._item_ids.append(new_item) 
          
    # NYI: 
    #def drawRoundRect(self, x1,y1, x2,y2, rx=5, ry=5, 
    #                  edgeColor=None, edgeWidth=None, fillColor=None): 
  
  
    def drawEllipse(self, x1,y1, x2,y2, 
                    edgeColor=None, edgeWidth=None, fillColor=None): 
        fillColor = self._getTkColor(fillColor, self.defaultFillColor) 
        edgeColor = self._getTkColor(edgeColor, self.defaultLineColor) 
        if edgeWidth is None: 
            edgeWidth  = self.defaultLineWidth 
        new_item = self.draw_area.create_oval(x1, y1, x2, y2, 
                                              fill=fillColor, 
                                              outline=edgeColor,
                                              width=edgeWidth) 
        self._item_ids.append(new_item) 
  
    def drawArc(self, x1, y1, x2, y2, startAng=0, extent=360, 
                edgeColor=None, edgeWidth=None, fillColor=None): 
        fillColor = self._getTkColor(fillColor, self.defaultFillColor) 
        edgeColor = self._getTkColor(edgeColor, self.defaultLineColor) 
        if edgeWidth is None: 
            edgeWidth  = self.defaultLineWidth 
        new_item = self.draw_area.create_arc(x1, y1, x2, y2, 
                                             start=startAng, 
                                             extent=extent, 
                                             fill=fillColor, 
                                             width=edgeWidth,
                                             outline=edgeColor) 
        self._item_ids.append(new_item) 
  
    def drawPolygon(self, pointlist, 
                    edgeColor=None, edgeWidth=None, fillColor=None, closed=0): 
        fillColor = self._getTkColor(fillColor, self.defaultFillColor) 
        edgeColor = self._getTkColor(edgeColor, self.defaultLineColor) 
        if edgeWidth is None: 
            edgeWidth  = self.defaultLineWidth 
        if closed:
            # draw a closed shape
            new_item = self.draw_area.create_polygon(pointlist, 
                                                     fill=fillColor, 
                                                     width=edgeWidth,
                                                     outline=edgeColor)
        else:
            if fillColor == self.__TRANSPARENT:
                # draw open-ended set of lines
                d = { 'fill':edgeColor, 'width': edgeWidth}
                new_item = self.draw_area.create_line(*pointlist, **d)
            else:
                # open filled shape.
                # draw it twice:
                #    once as a polygon with no edge outline with the fill color
                #    and once as an open set of lines of the appropriate color
                new_item = self.draw_area.create_polygon(pointlist, 
                                                         fill=fillColor, 
                                                         outline=self.__TRANSPARENT)
                
                self._item_ids.append(new_item)
                
                d = { 'fill':edgeColor, 'width': edgeWidth}
                new_item = self.draw_area.create_line(*pointlist, **d)
                                                   
        self._item_ids.append(new_item) 
  
    
    #def drawFigure(self, partList, 
    #               edgeColor=None, edgeWidth=None, fillColor=None):
    # use default implementation
          
    def drawImage(self, image, x1, y1, x2=None,y2=None):

        try:
            import ImageTk
        except ImportError:
            raise NotImplementedError('drawImage - require the ImageTk module')

        w,h = image.size
        if not x2 :
            x2 = w + x1
        if not y2 :
            y2 = h + y1

        if (w != x2-x1) or (h != y2-y1) :  # need to scale image
            myimage = image.resize((x2-x1,y2-y1))
        else:
            myimage = image
            
        # unless I keep a copy of this PhotoImage, it seems to be garbage collected
        # and the image is removed from the display after this function. weird
        itk = ImageTk.PhotoImage(myimage)
        new_item = self.draw_area.create_image(x1, y1, image=itk, anchor=tkinter.NW)
        self._item_ids.append(new_item) 
        self._images.append(itk)


try :
    import piddlePIL

    class TKCanvas(piddlePIL.PILCanvas):

        """This canvas maintains a PILCanvas as its backbuffer.  Drawing calls
        are made to the backbuffer and flush() sends the image to the screen
        using BaseTKCanvas.  
           You can also save what is displayed to a file in any of the formats
        supported by PIL"""
        
        def  __init__(self, size=(300,300), name='TKCanvas',  master = None) :
            piddlePIL.PILCanvas.__init__(self, size=size, name=name)
            self._tkcanvas = BaseTKCanvas(size=size, name=name, master=master)

        def flush(self) :
            piddlePIL.PILCanvas.flush(self) # call inherited one first
            self._tkcanvas.drawImage(self._image, 0,0)  # self._image should be a PIL image
            self._tkcanvas.flush()


except:
    # couldn't import piddlePIL so the PIL-based TkCanvas is not available, fall back to BaseTKCanvas w/o rotated strings
    TKCanvas = BaseTKCanvas
