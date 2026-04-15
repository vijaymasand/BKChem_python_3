"""Author: BKR
Copied of......hmmm... Inspired by the "fetch from webbook" plugin :-)

Ideas: 		Getting all alternative names from webbook and or other sources and
			creating a Dialog to choose the one desired
	
"""

from urllib import urlopen
import re
import oasa_bridge
import dialogs
from singleton_store import Store
from main import interactors

# search strings for the name and the cas registry number
name_re = re.compile( '(<h1><a id="Top" name="Top">)(.*)(</a></h1>)')
cas_re = re.compile('(<strong>CAS Registry Number:</strong>)(.*)(</li>)')
stereoisomers = re.compile('(<li><a href=")(.*)(">)(.*)(</a></li>)')

#create inchi
def get_inchi_for_one(u):

	program = Store.pm.get_preference( "inchi_program_path")
	if not oasa_bridge.oasa_available:
		return '',["oasa plugin error",]
	sms = []
	inchi_mol=""
	if not interactors.check_validity( u):
		return '',["validity Error",]	
	try:
		inchi_mol,warning=( oasa_bridge.mol_to_inchi( u, program))
#	except oasa.oasa_exceptions.oasa_inchi_error as e:
#		sms = ["InChI generation failed,", "make sure the path to the InChI program is correct in 'Options/INChI program path'", "", str( e)]
	except:
		sms = ["Unknown error occured during INChI generation, sorry", "Please, try to make sure the path to the InChI program is correct in 'Options/INChI program path'"]
		warning = []
	sms=sms+warning
	return inchi_mol, sms
	
def stereoisomers_found( streamx):
	alt_mol = []
	for line in streamx:
		mol_addrm = stereoisomers.search( line)
		if mol_addrm:
			mol = mol_addrm.group(4)
			if mol[-1] == "-":			#When Nist changes the name around
				mol = turn_name_around( mol)
			addr = mol_addrm.group(2)
			alt_mol.append( (mol, addr))
	mols=[]
	for a in alt_mol:
		mols.append(a[0])
	#Stereoisomer selection dialog	
	dialog = Pmw.Dialog( App.paper,
					buttons=(_('OK'), _('Cancel')),
					defaultbutton=_('OK'),
					title=_('The molekule was not found'))
	w = Pmw.ScrolledListBox(dialog.interior(), labelpos='n', items=mols, label_text='These Stereoisomers were found')
	w.pack(expand=1, fill='both', padx=4, pady=4)
	dialog.activate()
	for a in alt_mol:
		if a[0] == w.getvalue()[0]:
			return download_nist( "http://webbook.nist.gov"+a[1])

#Searches nist by name using inchi instead of the name
def get_name_from_webbook( inchi):
	
	# Escape problematic characters
	searchstr = ""
	for a in inchi:
		if a == "+":
			a = "%2B"
		elif a == "/":
			a = "%2F"
		elif a == "(":
			a = "%28"
		elif a == ")":
			a = "%29"
		searchstr = searchstr + a	
	url = "http://webbook.nist.gov/cgi/cbook.cgi?Name=%s&Units=SI" % ("+".join( searchstr.split()))
	return download_nist( url)
	
	
def download_nist( url):	
#	print url
	dialog = dialogs.progress_dialog( App, title=_("Fetching progress"))
	dialog.update( 0, top_text = "Connecting to WebBook...", bottom_text=url)
	sms=[]
	try:
		stream = urlopen( url)
	except IOError:
		dialog.close()
		sms.append('Nist could not be reached.')
		sms.append('Please check your internet connection')
		return '','', sms
	cas = ''
	mol_name = ''
	dialog.update( 0.5, top_text = "Reading the webbook...", bottom_text=url)      
	stream_lines = stream.readlines()
	for line in stream_lines:
		mol_namem = name_re.search( line)
		if line == "<h2>No matches found</h2>\n": 	#When stereoisomers are found
			dialog.close()
			return stereoisomers_found( stream_lines)
		elif line == "<h1>Name Not Found</h1>\n":	#When nothing is found
			dialog.close()
			sms.append("The molecule was not found")
			return mol_name, cas, sms
		if mol_namem:
			mol_name=mol_namem.group(2)
		casm = cas_re.search( line)
		if casm:
			cas = casm.group(2)
			stream.close()
			dialog.close()
			return mol_name, cas, sms
	dialog.close()
	sms.append("The molecule was not found")
	return mol_name, cas, sms

import Pmw

def err_mess_box (mess): #Pops up error OK-box
	message=""
	for m in mess:
		message=message+m+"\n"
	dialog = Pmw.Dialog(App.paper, buttons=('OK',),
	defaultbutton='OK', title='Error')

	w = Pmw.LabeledWidget(dialog.interior(), labelpos='n', label_text=message)
	w.pack(expand=1, fill='both', padx=4, pady=4)
	dialog.activate()
	
def turn_name_around( mol_name):
	bra = 0		#bracket counter
	back = ""	#end of name
	front= ""	#beginning of name
	frontreached = 0
	citra = "" 	#cis and trans are written at the end of the Nistname
	if mol_name[len(mol_name)-7:] == ",trans-":
		mol_name = mol_name[:len(mol_name)-7]
		citra = "trans-"
	elif mol_name[len(mol_name)-8:] == ", trans-": #Nist has spaces in some Names
		mol_name = mol_name[:len(mol_name)-8]
		citra = "trans-"	
	elif mol_name[len(mol_name)-5:] == ",cis-":
		mol_name =  mol_name[:len(mol_name)-5]
		citra = "cis-"
	elif mol_name[len(mol_name)-6:] == ", cis-": #Nist has spaces in some Names
		mol_name =  mol_name[:len(mol_name)-6]
		citra = "cis-"
	for a in mol_name:
		if not frontreached:  
			#the front and the back are devided by "," that is not in a bracket
			if a == "," and bra == 0:
				frontreached = 1
			else:
				back = back + a
				if a == "(":
					bra = bra + 1
				elif a == ")":
					bra = bra -1
		else:
			front = front + a
	if front[0] == " ": #Nist has spaces in some Names
		front = front[1:]
	mol_name = citra + front + back
	return mol_name

a=App.paper.selected_mols
err_mess=[]
if len(a)!= 0:
	for b in a:
		App.paper.unselect_all()
		App.paper.select(b)
		App.paper.select(b.children)  #select whole molekule for alignment below
		App.paper.swap_sides_of_selected( "horizontal")
		inchi_form, mess = get_inchi_for_one(b)
		App.paper.swap_sides_of_selected( "horizontal")
		if len(mess) != 0:		#Check for Errors
			err_mess = err_mess + mess
		if inchi_form:
			mess = []
			mol_name, cas, mess = get_name_from_webbook(inchi_form)
			err_mess = err_mess + mess
			if mol_name:		#writing Name
				#sometimes Nist changes the Name around e.g.: Cyclohexane,1,2-dibromo-,cis-
				if mol_name[-1] == "-":
					corr_mol_name = turn_name_around( mol_name)	
				else:
					corr_mol_name = mol_name
				t1 = App.paper.new_text( 300, 300, text=corr_mol_name.strip())
				t1.draw()
				App.paper.place_next_to_selected ("b","v",10,t1) #place below mol
				App.paper.select([t1])
			if cas:				#writing CAS
				t2 = App.paper.new_text( 300, 325, text="CAS: "+cas.strip())
				t2.draw()
				App.paper.place_next_to_selected ("b","v",5,t2)	#place below mol
				App.paper.select([t2])
	if len(err_mess)!= 0:	#check for any error messages
		err_mess_box (err_mess)
	App.paper.add_bindings()
else:	
	err_mess_box (["Please select a molecule"])
