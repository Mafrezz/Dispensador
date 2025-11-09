[app]
title = Dispensador Inteligente
package.name = dispensador
package.domain = org.mafrezz
source.dir = .
source.include_exts = py,kv,json,png,jpg,db
# Requisitos probados en tu entorno
requirements = python3,kivy==2.3.0,https://github.com/kivymd/KivyMD/archive/master.zip,sqlite3,pyjnius,plyer
orientation = portrait
fullscreen = 0

# Permisos BT (Android 12+)
android.permissions = BLUETOOTH,BLUETOOTH_ADMIN,BLUETOOTH_CONNECT,BLUETOOTH_SCAN,ACCESS_FINE_LOCATION,ACCESS_COARSE_LOCATION

android.api = 33
android.minapi = 21
# android.archs = arm64-v8a, armeabi-v7a

# Icono opcional si tienes assets/app_icon.png
# icon.filename = %(source.dir)s/assets/app_icon.png

[buildozer]
log_level = 2
warn_on_root = 0