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

from .singleton_store import Store



class bkchem_http_handler( BaseHTTPServer.BaseHTTPRequestHandler):

  dirs = ('smiles','inchi','gtml')

  def __init__( self, *args):
    BaseHTTPServer.BaseHTTPRequestHandler.__init__( self, *args)

  def do_GET( self):
    path_list = filter( None, self.path.split("/"))

    if len( path_list) == 1 or path_list[0] not in self.dirs:
      # these are static pages
      path = string.replace( self.path, ".", "_")
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
    


  def return_error( self):
    self.send_response( 400)
    self.send_header("Content-Type", "text/html")
    self.end_headers()    

    self.wfile.write("<html><body><h1>Bad request</h1><p>This address does not exist</p></body></html>")


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

