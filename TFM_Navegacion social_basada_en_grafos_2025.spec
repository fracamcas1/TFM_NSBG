# -*- mode: python ; coding: utf-8 -*-
import sys, os
sys.setrecursionlimit(sys.getrecursionlimit() * 5)

a = Analysis(
    ['tfm.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('fondo.png', '.'),
        ('rexasi.png', '.'),
        ('icon.png', '.'),
        ('icon.ico', '.'),
        ('boton_sim.png', '.'),
        ('boton_sim_2.png', '.')
    ],
    hiddenimports=[],
    hookspath=['hooks'],
    hooksconfig={},
    runtime_hooks=[],
excludes = [
    # Librerías de visualización y ciencia de datos
    'altair','bokeh','plotly','panel','seaborn','statsmodels','sympy',
    'sklearn','skimage','xarray','xyzservices','matplotlib.tests',

    # Ecosistema Jupyter/IPython
    'IPython','notebook','nbformat','nbconvert','ipywidgets','jupyterlab',

    # Motores gráficos y GUI alternativos
    'PyQt5','PyQt6','PySide2','PySide6','qtpy','pygame','pyglet',

    # Librerías de ML/IA pesadas
    'tensorflow','torch','keras','transformers','spacy','nltk','gensim',

    # Librerías de bases de datos y ORM
    'sqlalchemy','MySQLdb','psycopg2','h5py','tables','openpyxl',

    # Librerías de red y web
    'flask','django','fastapi','dash','requests','httpx','urllib3','aiohttp',

    # Librerías de documentación y formateo
    'sphinx','docutils','black','yapf','pylint','pytest',

    # Otras utilidades pesadas o innecesarias
    'dask','distributed','fsspec','numba','llvmlite','patsy','shapely',
    'cryptography','bcrypt','argon2','markdown','mistune',

    # Extras que estaban en excludedimports 'six.moves' 'typing_extensions',
    'tkinter.test','scipy','pandas','bs4','lxml',
    'xlrd','xlwt','docx','pdfminer','reportlab','pywin32','win32com',
    'pkg_resources','setuptools','pygments','zipp','gi'
],
    excludedimports=[],
    noarchive=False,
    optimize=0,
)

pyz = PYZ(a.pure, a.zipped_data,
          cipher=None)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='tfm',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,   # pon False si quieres ocultar la consola
    icon=['icon.ico'],
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='tfm'
)