"""
 py2app/py2exe build script for Pyrope

 Will automatically ensure that all build prerequisites are available
 via ez_setup

 Usage (Mac OS X):
     python setup.py py2app

 Usage (Windows):
     python setup.py py2exe
"""
import ez_setup
ez_setup.use_setuptools()

import sys
from setuptools import setup
mainscript = 'pyrope_client.py'

if sys.platform == 'darwin':
    extra_options = dict(
        setup_requires=['py2app'],
        app=[mainscript],
        # Cross-platform applications generally expect sys.argv to
        # be used for opening files.
        options=dict(py2app=dict(argv_emulation=True,
                                 iconfile='pyrope.icns',
                                 resources=["images"],
#                                 packages=["Crypto", "OpenSSL"],
                                 ),
                     )
        )
elif sys.platform == 'win32':
    import py2exe
    extra_options = dict(
        windows=[{"script":mainscript,
#                  'icon_resources':[(1,'pipeline.icns')]
                  }
        ],
    )
else:
    extra_options = dict(
        # Normally unix-like platforms will use "setup.py install"
        # and install the main script as such
        scripts=[mainscript],
        resources=["images"],
    )

setup(
  name="Pyrope",
  **extra_options
)
