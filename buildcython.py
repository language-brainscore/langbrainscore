import os
import shutil
from distutils.command.build_ext import build_ext
from distutils.core import Distribution, Extension

from Cython.Build import cythonize

compile_args = [] #"-std=c++11"]
link_args = []
include_dirs = []

libraries = ["m"]
# get environmental variables to determine the flow of the build process
BUILD_WHEELS = os.getenv("BUILD_WHEELS", None)
LIBS_DIR = os.getenv("LIBS_DIR", '/usr/lib')
if BUILD_WHEELS:
    library_dirs = ['/usr/lib64']
else:
    library_dirs = [LIBS_DIR]

def build(setup_kwargs):
    """Build extension modules."""    
#def build():
    extensions = [
        Extension(
            "*",
            ["langbrainscore/**/*.pyx"],
            extra_compile_args=compile_args,
            extra_link_args=link_args,
            include_dirs=include_dirs,
            libraries=libraries,
            library_dirs=library_dirs,
        )
    ]
    ext_modules = cythonize(
        extensions,
        include_path=include_dirs,
        compiler_directives={"binding": True, "language_level": 3},
    )
    
    kwargs = dict(ext_modules=ext_modules, name='c_extension')
    setup_kwargs.update(kwargs)
    distribution = Distribution(setup_kwargs)#
    distribution.package_dir = "c_extension"

    cmd = build_ext(distribution)
    cmd.ensure_finalized()
    cmd.run()

    # Copy built extensions back to the project
    for output in cmd.get_outputs():
        relative_extension = os.path.relpath(output, cmd.build_lib)
        shutil.copyfile(output, relative_extension)
        mode = os.stat(relative_extension).st_mode
        mode |= (mode & 0o444) >> 2
        os.chmod(relative_extension, mode)

    return setup_kwargs


if __name__ == "__main__":
    build({})
