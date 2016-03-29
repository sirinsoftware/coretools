from SCons.Script import *
from SCons.Environment import Environment
import sys
import platform
import os.path
from pymomo.utilities.paths import MomoPaths
import utilities
import pyparsing
from pymomo.mib.descriptor import MIBDescriptor

def build_program(name, chip):
	"""
	Build an ARM cortex executable
	"""

	dirs = chip.build_dirs()

	output_name = '%s.elf' % (chip.output_name(),)
	map_name = '%s.map' % (chip.output_name(),)

	VariantDir(dirs['build'], os.path.join('firmware', 'src'), duplicate=0)

	prog_env = setup_environment(chip)
	prog_env['OUTPUT'] = output_name
	prog_env['MODULE'] = name

	#Setup specific linker flags for building a program
	##Specify the linker script
	ldscript = utilities.join_path(chip.property('linker'))
	prog_env['LINKFLAGS'].append('-T"%s"' % ldscript)

	##Specify the output map file
	prog_env['LINKFLAGS'].extend(['-Xlinker', '-Map="%s"' % os.path.join(dirs['build'], map_name)])
	Clean(os.path.join(dirs['build'], output_name), [os.path.join(dirs['build'], map_name)])

	#Compile the CDB command definitions
	compile_mib(prog_env)

	SConscript(os.path.join(dirs['build'], 'SConscript'), exports='prog_env')

	prog_env.Depends(os.path.join(dirs['build'], output_name), [ldscript])

	prog_env.InstallAs(os.path.join(dirs['output'], output_name), os.path.join(dirs['build'], output_name))
	prog_env.InstallAs(os.path.join(dirs['output'], map_name), os.path.join(dirs['build'], map_name))

	return os.path.join(dirs['output'], output_name)

def build_library(name, chip):
	"""
	Build a static ARM cortex library
	"""

	dirs = chip.build_dirs()

	output_name = '%s.a' % (chip.output_name(),)

	VariantDir(dirs['build'], 'src', duplicate=0)

	library_env = setup_environment(chip)
	library_env['OUTPUT'] = output_name

	SConscript(os.path.join(dirs['build'], 'SConscript'), exports='library_env')

	library_env.InstallAs(os.path.join(dirs['output'], output_name), os.path.join(dirs['build'], output_name))
	return os.path.join(dirs['output'], output_name)

def setup_environment(chip):
	"""
	Setup the SCons environment for compiling arm cortex code
	"""

	#Make sure we never get MSVC settings for windows since that has the wrong command line flags for gcc
	if platform.system() == 'Windows':
		env = Environment(tools=['mingw', 'ldf_compiler'], ENV = os.environ)
	else:
		env = Environment(tools=['default', 'ldf_compiler'], ENV = os.environ)

	env['INCPREFIX'] = '-I"'
	env['INCSUFFIX'] = '"'
	env['CPPPATH'] = chip.includes()
	env['ARCH'] = chip

	#Setup Cross Compiler
	env['CC'] 		= 'arm-none-eabi-gcc'
	env['AS'] 		= 'arm-none-eabi-as'
	env['LINK'] 		= 'arm-none-eabi-gcc'
	env['AR'] 		= 'arm-none-eabi-ar'
	env['RANLIB']	= 'arm-none-eabi-ranlib'

	#Setup Nice Display Strings
	env['CCCOMSTR'] = "Compiling $TARGET"
	env['ARCOMSTR'] = "Building static library $TARGET"
	env['RANLIBCOMSTR'] = "Indexing static library $TARGET"
	env['LINKCOMSTR'] = "Linking $TARGET"

	#Setup Compiler Flags
	env['CCFLAGS'] = chip.combined_properties('cflags')
	env['LINKFLAGS'] = chip.combined_properties('ldflags')
	env['ARFLAGS'].append(chip.combined_properties('arflags')) #There are default ARFLAGS that are necessary to keep

	#Add in compile tile definitions
	defines = utilities.build_defines(chip.property('defines', {}))
	env['CCFLAGS'].append(defines)

	#Setup Target Architecture
	env['CCFLAGS'].append('-mcpu=%s' % chip.property('cpu'))
	env['LINKFLAGS'].append('-mcpu=%s' % chip.property('cpu'))

	#Setup any linked in libraries
	libdirs, libnames = utilities.process_libaries(chip.combined_properties('libraries'), chip)
	env['LIBPATH'] = libdirs
	env['LIBS'] = libnames

	return env

def compile_mib(env, mibname=None, outdir=None):
	"""
	Given a path to a *.mib file, use mibtool to process it and return a command_map.asm file
	return the path to that file.
	"""

	if outdir is None:
		dirs = env["ARCH"].build_dirs()
		outdir = dirs['build']

	if mibname is None: 
		mibname = os.path.join('firmware', 'src', 'cdb', env["MODULE"] + ".cdb")

	cmdmap_c_path = os.path.join(outdir, 'command_map_c.c')
	cmdmap_h_path = os.path.join(outdir, 'command_map_c.h')

	env['MIBFILE'] = '#' + cmdmap_c_path

	return env.Command([cmdmap_c_path, cmdmap_h_path], mibname, action=env.Action(mib_compilation_action, "Compiling MIB definitions"))

def mib_compilation_action(target, source, env):
	"""
	Compile mib file into a .h/.c pair for compilation into an ARM object
	"""

	try:
		d = MIBDescriptor(str(source[0]))
	except pyparsing.ParseException as e:
		raise BuildError("Could not parse mib file", parsing_exception=e, )

	#Build a MIB block from the mib file
	block = d.get_block()
	block.create_c(os.path.dirname(str(target[0])))
