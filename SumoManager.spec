# -*- mode: python -*-

block_cipher = None


a = Analysis(['main.py'],
             pathex=['/Users/silbo/Downloads/sumomanager-desktop'],
             binaries=[],
             datas=[('res/sumologo.svg', 'res'), ('res/main.qss', 'res'), ('res/orbitron.ttf', 'res'), ('res/usb_connected.png', 'res'), ('res/usb.png', 'res')],
             hiddenimports=[],
             hookspath=[],
             runtime_hooks=[],
             excludes=[],
             win_no_prefer_redirects=False,
             win_private_assemblies=False,
             cipher=block_cipher)
pyz = PYZ(a.pure, a.zipped_data,
             cipher=block_cipher)
exe = EXE(pyz,
          a.scripts,
          exclude_binaries=True,
          name='SumoManager',
          debug=False,
          strip=False,
          upx=True,
          runtime_tmpdir=None,
          console=False , icon='res\\sumologo.ico')
coll = COLLECT(exe,
               a.binaries,
               a.zipfiles,
               a.datas,
               strip=False,
               upx=True,
               name='SumoManager')
app = BUNDLE(coll,
             name='SumoManager.app',
             icon='res/sumologo.icns',
             bundle_identifier=None)
