#--------------------------------------------------------------------------
#     This file is part of BKChem - a chemical drawing program
#     Copyright (C) 2002-2009 Beda Kosata <beda@zirael.org>

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


"""here is the http server that server data from application on demand"""


import BaseHTTPServer
from . import xml_writer
import string
from . import xml_serializer
import xml.dom.minidom as dom
import time
import os.path
import urlparse

from . import oasa_bridge

from .singleton_store import Store




class bkchem_http_handler( BaseHTTPServer.BaseHTTPRequestHandler):

  dirs = ('smiles','inchi','gtml','images')

  def __init__( self, *args):
    BaseHTTPServer.BaseHTTPRequestHandler.__init__( self, *args)

  def do_GET_fallback( self):
    protocol, address, path, parameters, query, fragment = urlparse.urlparse( self.path)
    path_list = filter( None, path.split("/"))

    if len( path_list) == 1 or path_list[0] not in self.dirs:
      # these are static pages
      path = string.replace( path, ".", "_")
      path = string.replace( path, "/", "__")
      method = 'serve' + path

      if method in self.__class__.__dict__:
        self.__class__.__dict__[ method]( self)
      else:
        self.return_error()
    else:
      method = "servedir_" + path_list[0]
      self.__class__.__dict__[ method]( self, path_list[1:])


  def serve__content_xml( self):
    t = time.time()
    self.send_response( 200)
    self.send_header("Content-Type", "text/xml")
    self.end_headers()

    doc = dom.Document()
    xml_serializer.serialize( Store.app.paper, doc, doc)
    self.wfile.write( doc.toxml())
    print("%.2f ms" % (1000*(time.time() - t)))

  def serve__content_svg( self):
    self.send_response( 200)
    self.send_header("Content-Type", "image/svg+xml")
    self.end_headers()

    exporter = xml_writer.SVG_writer( Store.app.paper)
    exporter.construct_dom_tree( Store.app.paper.top_levels)
    self.wfile.write( exporter.document.toxml())



  def serve__content_html( self): 
    self.send_response( 200)
    self.send_header("Content-Type", "text/html")
    self.end_headers()


    result = '''
    <html>
    <head>
    <script src="bkchem.js" type="text/javascript"></script>
    </head>
    <body style="background-color:#dddddd;">
    <img src="content.png" id="the_pict" onclick="javascript:click( event)" style="float:left"/>
    <div style="margin-left:500px;">
    <div class="buttons">
    <form name="input_form">
    <button type="button" onclick="javascript:send_action(\'undo\');">Undo</button>
    <button type="button" onclick="javascript:send_action(\'redo\');">Redo</button>
    <br />
    <span>Atom symbol:</span>
    <button type="button" onclick="javascript:set_symbol(\'C\');">C</button>
    <button type="button" onclick="javascript:set_symbol(\'H\');">H</button>
    <button type="button" onclick="javascript:set_symbol(\'O\');">O</button>
    <button type="button" onclick="javascript:set_symbol(\'N\');">N</button>
    <button type="button" onclick="javascript:set_symbol(\'P\');">P</button>
    <button type="button" onclick="javascript:set_symbol(\'S\');">S</button>
    <button type="button" onclick="javascript:set_symbol(\'F\');">F</button>
    <button type="button" onclick="javascript:set_symbol(\'Cl\');">Cl</button>
    <button type="button" onclick="javascript:set_symbol(\'Br\');">Br</button>
    <button type="button" onclick="javascript:set_symbol(\'I\');">I</button>
    <br />
    <span>Symbol text:</span>
    <input type="text" name="symbol_text" />
    <button type="button" onclick="javascript:set_symbol_from_entry();">Set</button>
    <br />
    <input type="radio" name="template" value="draw" onclick="javascript:set_mode(\'draw\');"><img src="images/normal.gif"/></input>
    <input type="radio" name="template" value="benzene" onclick="javascript:set_template(\'benzene\');"><img src="images/benzene.gif"/></input>
    <input type="radio" name="template" value="cyclopentane" onclick="javascript:set_template(\'cyclopentane\');"><img src="images/cyclopentane.gif"/></input>
    <br />
    <button type="button" onclick="javascript:send_action(\'expand_all\');">Expand all groups</button>
    </div>
    </form>

    <hr />
    <div id="the_smiles">%(smiles)s</div>
    </div>
    </body>
    </html>
    ''' % {'smiles': self._get_all_smiles()}
    self.wfile.write( result)
   


  def serve__content_png( self):
    Store.app.plugin_export( "PNG (Cairo)", filename="http_temp.png", interactive=False)
    self._serve_file( "http_temp.png", "image/png")
    


  def servedir_smiles( self, path_list):
    if not len( path_list) == 1:
      self.return_error()
    else:
      Store.app.paper.clean_paper()
      Store.app.paper.create_background()
      Store.app.read_smiles( path_list[0])
      self.serve__content_svg()

  def servedir_inchi( self, path_list):
    Store.app.paper.clean_paper()
    Store.app.paper.create_background()
    Store.app.read_inchi( '/'.join( path_list))
    self.serve__content_svg()


  def servedir_gtml( self, path_list):
    Store.app.paper.clean_paper()
    Store.app.paper.create_background()
    Store.app.plugin_import( 'GTML', '/'.join( path_list))
    self.serve__content_svg()
    

  def servedir_images( self, path_list):
    self._serve_file( os.path.join( "..", "pixmaps", *path_list))


  def serve__bkchem_js( self):
    self._serve_file( "bkchem.js", content_type="text/javascript")
    
    


  def return_error( self):
    self.send_response( 400)
    self.send_header("Content-Type", "text/html")
    self.end_headers()    

    self.wfile.write("<html><body><h1>Bad request</h1><p>This address does not exist</p></body></html>")



  def do_GET( self):
    protocol, address, path, parameters, query, fragment = urlparse.urlparse( self.path)
    if path == "/" or path == "content.html":
      attrs = self._get_attrs( query)
      if "action" in attrs:
        method = "_action_"+attrs['action']
        if hasattr( self, method):
          getattr( self, method)( attrs)
          try:
            smiles = self._get_all_smiles()
          except:
            smiles = "SMILES not available"
          self._serve_xml( "<smiles>%s</smiles>" % smiles)
          
      else:
        self.serve__content_html()
    else:
      self.do_GET_fallback()



  def _action_click( self, attrs):
    x = float( attrs['x'])-8
    y = float( attrs['y'])-9
    e = Event( x=x, y=y)
    Store.app.paper._move( e)
    #Store.app.mode.mouse_click( e)
    Store.app.mode.mouse_down( e)
    Store.app.mode.mouse_up( e)
    #Store.app.mode.leave_object( e)
    

  def _action_undo( self, attrs):
    Store.app.mode.undo()


  def _action_redo( self, attrs):
    Store.app.mode.redo()


  def _action_setsymbol( self, attrs):
    Store.app.mode.set_given_name_to_selected( attrs['symbol'])


  def _action_expand_all( self, attrs):
    Store.app.paper.expand_groups( selected=False)


  def _action_setmode( self, attrs):
    Store.app.change_mode( attrs['mode'])


  def _action_settemplate( self, attrs):
    Store.app.change_mode( 'template')
    Store.app.mode.set_submode( attrs['temp'])



  def _serve_xml( self, text):
    self.send_response( 200)
    self.send_header("Content-Type", "text/xml")
    self.end_headers()

    self.wfile.write( text)


  def _serve_file( self, filename, content_type="image/png"):
    self.send_response( 200)
    self.send_header("Content-Type", content_type)
    self.end_headers()
    
    f = file( filename, "rb")
    self.wfile.write( f.read())
    f.close()
    


  def _get_attrs( self, query):
    attrs = query.split( "&")
    _as = {}
    for a in attrs:
      if a:
        k, v = a.split("=")
        _as[ k] = v
    return _as


  def _get_all_smiles( self):
    sms = []
    for m in Store.app.paper.molecules:
      sms.append( oasa_bridge.mol_to_smiles( m))
    smiles = ", ".join( sms)
    return smiles


  # LOGGING

  def log_request( self, *args):
    pass

  def log_message( self, *args):
    pass

  def log_error( self, *args):
    pass





class bkchem_http_server( BaseHTTPServer.HTTPServer):

  def __init__( self, *args):
    BaseHTTPServer.HTTPServer.__init__( self, *args)



class Event:

  def __init__( self, x, y):
    self.x = x
    self.y = y
