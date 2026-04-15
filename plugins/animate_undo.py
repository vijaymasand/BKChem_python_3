
import os.path

crop_svg = App.paper.get_paper_property( 'crop_svg')
App.paper.set_paper_properties( crop_svg=0)

name = App.paper.file_name['name']

name, ext = os.path.splitext( name)

n = App.paper.um.get_number_of_records()

for i in range( n):
  App.paper.undo()

for i in range( n):
  App.save_CDML( name="%s-%02d%s" % (name, i, ext))
  App.paper.redo()

 
App.paper.set_paper_properties( crop_svg=crop_svg)


