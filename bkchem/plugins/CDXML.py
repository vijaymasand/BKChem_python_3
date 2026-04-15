# encoding: utf-8

#--------------------------------------------------------------------------
#     This file is part of BKChem - a chemical drawing program
#     Copyright (C) 2002-2009 Beda Kosata <beda@zirael.org>

#     This plugin was create for BKChem by Simona Pourová
#     Copyright (C) 2009 Simona Pourová

#     This program is free software; you can redistribute it and/or modify
#     it under the terms of the GNU General Public License as published by
#     the Free Software Foundation; either version 2 of the License, or
#     (at your option) any later version.

#     This program is distributed in the hope that it will be useful,
#     but WITHOUT ANY WARRANTY; without even the implied warranty of
#     MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#     GNU General Public License for more details.

#     Complete text of GNU GPL can be found in the file gpl.txt in the
#     main directory of the program

#--------------------------------------------------------------------------


"""CDXML import-export plugin"""

from . import plugin
import xml.dom.minidom as dom
from .. import dom_extensions as dom_ext
import math
from ..molecule import molecule
from ..classes import plus, point, text as text_class
from ..arrow import arrow
from ..singleton_store import Screen
import re
import gettext
_ = gettext.gettext

## DEFINITIONS

class CDXML_importer( plugin.importer):
  """Imports a CDXML (ChemDraw XML format) document"""
  doc_string = _("Imports a CDXML (ChemDraw XML format) document.")
  gives_molecule = 1
  gives_cdml = 0

  def __init__( self, paper):
    self.paper = paper

  def on_begin( self):
    return 1

  def get_molecules( self, file_name):
    doc = dom.parse( file_name)
    molecules = []
    # read colors
    colors=[]
    for elem7 in doc.getElementsByTagName("color"):
      red=(float(elem7.getAttribute("r"))*255)
      green=(float(elem7.getAttribute("g"))*255)
      blue=(float(elem7.getAttribute("b"))*255)
      colors.append("#%02x%02x%02x" % (red,green,blue))

    # read fonts
    fonts={}
    for elem8 in doc.getElementsByTagName("font"):
      family=str(elem8.getAttribute("name"))
      fonts[int(elem8.getAttribute("id"))]=family

    # read molecules
    for elem1 in doc.getElementsByTagName("fragment"):
      if elem1.parentNode.nodeName=="page":
        mol = molecule( paper=self.paper) 
        atom_id_to_atom = {}
        atom_id_to_text = {}
        for elem2 in elem1.childNodes:
          
          # atom
          if elem2.nodeName=="n":
            font = ""
            Size = 12
            text = "C"
            color1="#000000"
            for elem3 in elem2.childNodes:
              if elem3.nodeName=="t":
                if elem3.hasAttribute("color"):
                  color1=colors[int(elem3.getAttribute("color"))-2]
                text = ""
                for elem4 in elem3.childNodes:
                  if elem4.nodeName=="s":
                    if elem3.hasAttribute("color"):
                      color1=colors[int(elem3.getAttribute("color"))-2]
                    for (Id,Font) in fonts.items():
                      if Id==int(elem4.getAttribute("font")):
                        font=Font
                    Size= int(elem4.getAttribute("size"))
                    text += dom_ext.getAllTextFromElement( elem4).strip()
            
            position = elem2.getAttribute("p").split()
            assert len( position) == 2
            
            
            # we must postpone symbol assignment until we know the valency of the atoms
            atom_id_to_text[ elem2.getAttribute('id')] = text
            atom = mol.create_vertex()
            atom.line_color = color1
            atom.font_family = font
            atom.font_size = Size
            atom.x = float( position[0])
            atom.y = float( position[1])
            mol.add_vertex( atom)
            atom_id_to_atom[ elem2.getAttribute('id')] = atom
          
          # bond
          #{"v BKChemu bond.type":"v ChemDraw hodnota atributu Display elementu b"}
          bondType2={"WedgeBegin":"w",
          "WedgedHashBegin":"h",
          "Wavy":"a",
          "Bold":"b",
          "Dash":"d"
          }
          
          if elem2.nodeName=="b":
            if elem2.hasAttribute("color"):
              color2 = colors[(int(elem2.getAttribute("color"))-2)]
            else:
              color2="#000000"
            order = 1
            if elem2.hasAttribute("Order"):
              order = int( elem2.getAttribute("Order"))      
            bond = mol.create_edge()
            if elem2.hasAttribute("Display"):
              display = elem2.getAttribute("Display").strip()
              for bondC,bondB in bondType2.items():
                if bondC ==display:
                  bond.type = bondB
            bond.line_color = color2
            bond.order = order
            atom1 = atom_id_to_atom[ elem2.getAttribute("B")]
            atom2 = atom_id_to_atom[ elem2.getAttribute("E")]
            mol.add_edge( atom1, atom2, bond)
        
        
        # here we reassign the symbols
        for id,atom in atom_id_to_atom.items():
          text = atom_id_to_text[ id]
          v = mol.create_vertex_according_to_text( atom, text)
          atom.copy_settings( v)
          mol.replace_vertices( atom, v)
          atom.delete()
        # finally we add the molecule to the list of molecules for output
        molecules.append( mol)

    # read texts
    textik={2:"i",
            1:"b",
            32:"sub",
            64:"sup"}

    for elem5 in doc.getElementsByTagName("t"):
      if elem5.parentNode.nodeName=="page":
        position = map( float, elem5.getAttribute("p").split())
        assert len( position) == 2
        celyText=""
        for elem51 in elem5.childNodes:
          if elem51.nodeName=="s":
            for elem52 in elem51.childNodes:
              if isinstance( elem52, dom.Text):
                rodice=[]
                text100=elem52.data
                if elem51.hasAttribute("face"):
                  Face01=int(elem51.getAttribute("face"))
                  for face,parent in textik.items():
                    for i in range(9):
                      if not Face01&2**i==0:
                        if face==Face01&2**i:
                          rodice.append(parent)
                for rodic in rodice:
                  text100 = "<%s>%s</%s>" % (rodic,text100,rodic)
            celyText += text100
  
            if elem5.hasAttribute("color"):
              color3=colors[(int(elem5.getAttribute("color"))-2)]
            else:
              color3="#000000"
              
            font_id = elem51.getAttribute("font")
            if font_id != "":
              font=fonts[int(font_id)]
            #text = dom_ext.getAllTextFromElement(elem51)
        #print celyText    
        text = celyText
        t = text_class( self.paper, position, text=text)
        t.line_color = color3
        #print elem51
        if elem51.hasAttribute("size"):
          t.font_size = int( elem51.getAttribute("size"))
        if font:
          t.font_family = font
        molecules.append(t)
        
    # read graphics - plus
    for elem6 in doc.getElementsByTagName("graphic"):
      if elem6.getAttribute("GraphicType")=="Symbol" and elem6.getAttribute("SymbolType")=="Plus":
        position = map( float, elem6.getAttribute("BoundingBox").split())
        position2=[position[0],position[1]]
        assert len(position2) == 2
        if elem6.hasAttribute("color"):
          color4=colors[(int(elem6.getAttribute("color"))-2)]
        else:
          color4="#000000"
        pl = plus(self.paper, position2)
        pl.line_color = color4
        molecules.append(pl)
        
    sipka=[]
    #for elem71 in doc.getElementsByTagName("graphic"):
      #if elem71.getAttribute("GraphicType")=="Line":

    
    for elem7 in doc.getElementsByTagName("arrow"):
      sipka.insert(0,elem7.getAttribute('Head3D') )
      sipka.insert(1,elem7.getAttribute('Tail3D') )
      if elem7.hasAttribute("color"): 
        sipka.insert(0,colors[(int(elem7.getAttribute("color"))-2)])
      point1 = map( float, sipka[1].split())
      point2 = map( float, sipka[2].split())
      arr = arrow( self.paper, points=[point2[0:2],point1[0:2]], fill=sipka[0])
      arr.line_color=sipka[0]
      molecules.append( arr)
    
    sipka=[]
    return molecules


class CDXML_exporter( plugin.exporter):
  """Exports a CDXML (ChemDraw XML) document """
  doc_string = _("Exports a CDXML (ChemDraw XML) document")


  def __init__( self, paper):
    self.paper = paper


  def on_begin( self):
    return 1
    

  def write_to_file( self, name):
     #{"v BKChemu bond.type":"v ChemDraw hodnota atributu Display elementu b"}
    bondType={"w":"WedgeBegin",
          "h":"WedgedHashBegin",
          "a":"Wavy",
          "b":"Bold",
          "d":"Dash",
          "o":"Dash"
          }

    #{"arrow.type v BKChemu":["graphic/ArrowType","arrow/ArrowheadHead","arrow/   ArrowheadTail","arrow/ArrowheadType"]}
    #"retro":["RetroSynthetic","Full","","Angle"] - nefunguje, potrebuje dalsi povinne atributy
    arrowType={"equilibrium":["Equilibrium","HalfLeft","HalfLeft","Solid"],
           "equilibrium2":["Equilibrium","HalfLeft","HalfLeft","Solid"],
           "normal":["FullHead","Full","","Solid"],
           "electron":["HalfHead","HalfLeft","","Solid"]
           }

    colors=["#ffffff","#000000","#ff0000","#ffff00","#00ff00","#00ffff","#0000ff","#ff00ff"]

    fonts=["Arial","Times New Roman"]

    out=dom.Document()
    root=out.createElement("CDXML")
    out.appendChild(root)
    elem01=out.createElement("colortable")
    root.appendChild(elem01)


    elem03=out.createElement("fonttable")
    root.appendChild(elem03)

    elem1=out.createElement("page")
    root.appendChild(elem1) 
    PaperX=int(Screen.mm_to_px( self.paper.get_paper_property("size_x") ) )
    PaperY=int(Screen.mm_to_px( self.paper.get_paper_property("size_y") ) )
    elem1.setAttribute("BoundingBox","%d %d %d %d" % (0,0,PaperX,PaperY) )
    elem1.setAttribute("Width",str(PaperX) )
    elem1.setAttribute("Height",str(PaperY) )
    elem1.setAttribute("DrawingSpace","poster")

    for mol in self.paper.molecules:
      elem2=out.createElement("fragment")
      elem1.appendChild(elem2)
  
      for atom in mol.atoms:
        elem3=out.createElement("n")
        elem2.appendChild(elem3)
        elem3.setAttribute("id",re.sub("atom","",atom.id) ) 
        elem3.setAttribute("p","%f %f" %(atom.x,atom.y) )
        elem3.setAttribute("NumHydrogens","%d" % atom.free_valency)
    
        if atom.symbol != "C" or atom.show:
          elem4=out.createElement("t")
          elem3.appendChild(elem4)
          elem6=out.createElement("s")
          elem6.setAttribute("size",str(atom.font_size) )
          elem6.setAttribute("face","96")
          elem4.appendChild(elem6)
          text4 = re.sub( "<.*?>", "", atom.xml_ftext)
          if text4:
            symbol=out.createTextNode(text4)
            elem6.appendChild(symbol)
          else:
            symbol=out.createTextNode(atom.xml_ftext)
            elem6.appendChild(symbol)
          NewColor=self.paper.any_color_to_rgb_string( atom.line_color)
          if NewColor not in colors:
            colors.append (NewColor)
          for color in colors:
            if color==NewColor:
              ShowColor=str(colors.index(color)+2)
          elem4.setAttribute("color",ShowColor)
          elem6.setAttribute("color",ShowColor)
      
          NewFont=atom.font_family
          if NewFont not in fonts:
            fonts.append(NewFont)
          for font in fonts:
            if font==NewFont:
              FontId=str(fonts.index(font)+3)
          elem6.setAttribute("font",FontId)
  
      for bond in mol.bonds:
        elem5=out.createElement("b")
        elem2.appendChild(elem5)
        elem5.setAttribute("B",re.sub("atom","",bond.atom1.id) ) 
        elem5.setAttribute("E",re.sub("atom","",bond.atom2.id) )
        for bondB,bondC in bondType.items():
          if bond.type==bondB:
            elem5.setAttribute("Display",bondC)
          elif bond.type=="h" and bond.equithick==1:
            elem5.setAttribute("Display","Hash")
    
        NewColor=self.paper.any_color_to_rgb_string( bond.line_color)
        if NewColor not in colors:
          colors.append (NewColor)
        for color in colors:
          if color==NewColor:
            ShowColor=str(colors.index(color)+2)
        elem5.setAttribute("color",ShowColor)
    
        #print int( self.paper.any_color_to_rgb_string( bond.line_color)[1:3], 16)
        if bond.order > 1:
          elem5.setAttribute("Order","%d" % bond.order )
        #print bond.type,bond.equithick,bond.simple_double
    
    for text in self.paper.texts:
      elem7=out.createElement("t")
      elem1.appendChild(elem7)
      elem7.setAttribute("id",re.sub("text","",text.id))
      elem7.setAttribute("p","%f %f" % (text.x,text.y))
      elem7.setAttribute("BoundingBox","%d %d %d %d" % (text.bbox()[0],text.bbox()[1],text.bbox()[2],text.bbox()[3]) )
      
      minidoc = dom.parseString( "<a>%s</a>" % text.xml_ftext.encode('utf-8'))
      textik={"i":2,
              "b":1,
              "sub":32,
              "sup":64
              }

      def get_text( el):
        texts = []
        for ch in el.childNodes:
          if isinstance( ch, dom.Text):
            parents = []
            par = ch.parentNode
            while not isinstance( par, dom.Document):
              parents.append( str(par.nodeName))
              par = par.parentNode
            texts.append( (str(ch.nodeValue), parents))
          else:
            texts += get_text( ch)  
        return texts              
      
      texts2= get_text(minidoc.childNodes[0])

      for text2 in texts2:   
        elem001=out.createElement("s")
        elem7.appendChild(elem001)
        elem001.setAttribute("size", str(text.font_size))
        text001=out.createTextNode(text2[0])
        elem001.appendChild(text001)
        
        def LogOR(xs):
          if len(xs) == 0:
            return 0
          else:
            return xs[0] | LogOR (xs[1:])
  
        Faces=[]
  
        for xxx in text2[1]:
          for (P,F) in textik.items():
            if P==xxx:
              Faces.append(F)
  
        Face=LogOR(Faces)
        if Face!=0:
          elem001.setAttribute("face",str(Face) )
      
        NewFont=text.font_family
        if NewFont not in fonts:
          fonts.append(NewFont)
        for font in fonts:
          if font==NewFont:
            FontId=str(fonts.index(font)+3)
        elem001.setAttribute("font",FontId)
        
        NewColor=self.paper.any_color_to_rgb_string(text.line_color)
        if NewColor not in colors:
          colors.append (NewColor)
        for color in colors:
          if color==NewColor:
            ShowColor=str(colors.index(color)+2)
        elem001.setAttribute("color",ShowColor)
        elem7.setAttribute("color",ShowColor)
      
  
    for plus in self.paper.pluses:
      elem9=out.createElement("graphic")
      elem1.appendChild(elem9)
      elem9.setAttribute("SymbolType","Plus")
      elem9.setAttribute("BoundingBox","%f %f %f %f" % plus.bbox())
      elem9.setAttribute("GraphicType","Symbol")
      elem9.setAttribute("id",re.sub("plus","",plus.id))
      #print plus.bbox()
      NewColor=self.paper.any_color_to_rgb_string(plus.line_color)
      if NewColor not in colors:
        colors.append (NewColor)
      for color in colors:
        if color==NewColor:
          ShowColor=str(colors.index(color)+2)
      elem9.setAttribute("color",ShowColor)

    for arrow in self.paper.arrows:
      arrowPoints=[p.get_xy() for p in arrow.points]
  
      elem10=out.createElement("graphic")
      elem1.appendChild(elem10)
      elem10.setAttribute("GraphicType","Line")
      for arrowB,arrowC in arrowType.items():
          if arrow.type==arrowB:
            elem10.setAttribute("ArrowType",arrowC[0])
      NewColor=self.paper.any_color_to_rgb_string(arrow.line_color)
      if NewColor not in colors:
        colors.append (NewColor)
      for color in colors:
        if color==NewColor:
          ShowColor=str(colors.index(color)+2)
      elem10.setAttribute("color",ShowColor)

      elem11=out.createElement("arrow")
      elem1.appendChild(elem11)
      for arrowB,arrowC in arrowType.items():
          if arrow.type==arrowB:
            elem11.setAttribute("ArrowheadHead",arrowC[1]) 
            elem11.setAttribute("ArrowheadTail",arrowC[2])
            elem11.setAttribute("ArrowheadType",arrowC[3])
      elem11.setAttribute("Head3D",str(arrowPoints[-1][0])+" "+str(arrowPoints[-1][1]))
      elem11.setAttribute("Tail3D",str(arrowPoints[0][0])+" "+str(arrowPoints[0][1]))
      elem11.setAttribute("BoundingBox","%f %f %f %f" % (arrowPoints[-1][0],arrowPoints[-1][1],arrowPoints[0][0],arrowPoints[0][1]) )
      elem11.setAttribute("color",ShowColor)
      #print arrow
      #print arrow.type

    for color in colors:
      elem02=out.createElement("color")
      elem01.appendChild(elem02)
      red=str(int(color[1:3],16)/255.0)
      green=str(int(color[3:5],16)/255.0)
      blue=str(int(color[5:7],16)/255.0)
  
      elem02.setAttribute("r",red)
      elem02.setAttribute("g",green)
      elem02.setAttribute("b",blue)

    FontId=3
    for font in fonts:
      elem04=out.createElement("font")
      elem03.appendChild(elem04) 
      elem04.setAttribute("id",str(FontId) )
      FontId+=1
      elem04.setAttribute("name",font)
    
    f = open( name, "wb")
    f.write( out.toxml().encode('utf-8'))
    f.close()

# PLUGIN INTERFACE SPECIFICATION
name = "CDXML"
extensions = [".cdxml",".xml"]
importer = CDXML_importer
exporter = CDXML_exporter
local_name = _("CDXML")
