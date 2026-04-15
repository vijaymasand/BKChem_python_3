
from urllib import urlopen
import re
import oasa_bridge
import dialogs


molfile_link = re.compile( '(<a href=")(.*)(">2d Mol file</a>)')
cas_re = re.compile('(<strong>CAS Registry Number:</strong>)(.*)(</li>)')
#link_re = re.compile('(<a href=")(/cgi/cbook.cgi?ID=.*">)(.*)(</a>)')


def get_mol_from_web_molfile( name):
  dialog = dialogs.progress_dialog( App, title=_("Fetching progress"))
  url = "http://webbook.nist.gov/cgi/cbook.cgi?Name=%s&Units=SI" % ("+".join( name.split()))
  dialog.update( 0, top_text = _("Connecting to WebBook..."), bottom_text=url)
  try:
    stream = urlopen( url)
  except IOError:
    dialog.close()
    return None
  dialog.update( 0.4, top_text = _("Searching for the compound..."), bottom_text=url)
  cas = ''
  for line in stream.readlines():
    casm = cas_re.search( line)
    if casm:
      cas = casm.group(2)
    m = molfile_link.search( line)
    if m:
      dialog.update( 0.8, top_text = _("Reading the molfile..."), bottom_text=m.group(2))      
      molfile = urlopen( "http://webbook.nist.gov" + m.group( 2))
      stream.close()
      ret = molfile.read()
      molfile.close()
      dialog.close()
      return ret, cas
  dialog.close()
  return None



## ask for the name to fetch

import Pmw

dial = Pmw.PromptDialog( App.paper,
                         title=_('Name'),
                         label_text=_('Give the name of a molecule to fetch:'),
                         entryfield_labelpos = 'n',
                         buttons=(_('OK'),_('Cancel')))
res = dial.activate()
if res == _('OK'):
  name = dial.get()

  # fetch the molfile

  import StringIO

  molcas = get_mol_from_web_molfile( name)
  if molcas:
    mol, cas = molcas
    mol = StringIO( mol)
    molec = oasa_bridge.read_molfile( mol, App.paper)
    mol.close()
    App.paper.stack.append( molec)
    molec.draw()
    if cas:
      t = App.paper.new_text( 280, 300, text="CAS: "+cas.strip())
      t.draw()
    App.paper.add_bindings()
    App.paper.start_new_undo_record()
  else:
    App.update_status( _("Sorry, molecule with name %s was not found") % name)

