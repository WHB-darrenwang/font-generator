from setuptools import setup

APP = ['font_maker.py']
DATA_FILES = [
    'canvas_manager.py',
    'glyph_list.py',
    'char_sets.py',
    'project.py',
    'exporter.py',
]
OPTIONS = {
    'argv_emulation': False,
    'packages': ['tkinter', 'PIL', 'numpy', 'skimage', 'fontTools'],
    'includes': [],
    'excludes': ['PyInstaller'],
    'iconfile': 'icon.icns' if __import__('os').path.exists('icon.icns') else None,
    'plist': {
        'CFBundleName': 'Font Maker',
        'CFBundleDisplayName': 'Font Maker',
        'CFBundleIdentifier': 'com.fontmaker.app',
        'CFBundleVersion': '1.0.0',
        'CFBundleShortVersionString': '1.0.0',
        'NSHighResolutionCapable': True,
    },
}

# Remove None iconfile
if OPTIONS['iconfile'] is None:
    del OPTIONS['iconfile']

setup(
    app=APP,
    data_files=DATA_FILES,
    options={'py2app': OPTIONS},
    setup_requires=['py2app'],
)
