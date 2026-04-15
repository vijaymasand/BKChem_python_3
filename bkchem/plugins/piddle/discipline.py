pass  # types wildcard removed
from .piddle import *

def checkMethods(parentMethod, childMethod):
	"Make sure the child's method obey's the parent's interface; return 1 if OK."
	# get the parameter names
	pf = parentMethod.func_code
	cf = childMethod.func_code
	pargs = pf.co_varnames[:pf.co_argcount]
	cargs = cf.co_varnames[:cf.co_argcount]
	
	# make sure they match, at least as far as the parent's go
	if len(cargs) < len(pargs):
		print("too few args")
		return 0	
	for i in range(len(pargs)):
		if pargs[i] != cargs[i]:
			print("arg names don't match")
			return 0

	# if child has any additional arguments, make sure
	# they have default values
	extras = len(cargs) - len(pargs)
	defs = childMethod.func_defaults
	if extras and (defs is None or len(defs) < extras):
		print("need %s defaults, got %s" % (extras, defs))
		print(cargs)
		print(pargs)
		return 0
	
	# otherwise, it's OK
	return 1
	
def checkClasses(parent, child):
	"Make sure the child class obeys the parent's interface."
	
	parentDir = dir(parent)
	childDir = dir(child)			
	for name in childDir:
		item = getattr(child, name)
		if type(item) != MethodType or name[0] == '_':
			pass  # print "     %s is not a public method" % name
		elif name in parentDir:
			if not checkMethods(getattr(parent, name).im_func, item.im_func):
				print("NAUGHTY CHILD disobeys arguments to", name)
			else:
				print("     %s looks OK" % name)
		else:
			print("     %s is unique to the child" % name)

foo = raw_input("backend to check (e.g., PDF):")
if foo:
	canvasname = foo+"Canvas"
	module = __import__("piddle"+foo, globals(), locals(), [canvasname] )
	child = getattr(module, canvasname)
	print("\nChecking %s...\n" % canvasname)
	checkClasses( Canvas, child )
