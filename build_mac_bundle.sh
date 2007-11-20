rm -rf build
rm -rf dist
find . -name \*.pyc | xargs rm
python setup.py py2app
hdiutil create -imagekey zlib-level=9 -srcfolder dist/Pyrope.app dist/Pyrope.dmg
