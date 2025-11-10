[app]
# (str) Title of your application
title = Dispensador Inteligente

# (str) Package name
package.name = dispensador

# (str) Package domain (used for android package, iOS bundle identifier)
package.domain = org.mafrezz

# (str) Your source code directory
source.dir = .

# (list) List of inclusions using pattern matching
source.include_exts = py,kv,json,png,jpg,db

# (list) Application requirements
requirements = python3,setuptools,wheel,cython==0.29.36,kivy==2.3.0,https://github.com/kivymd/KivyMD/archive/master.zip,sqlite3,pyjnius,plyer

# (str) Application versioning (method 1)
version = 1.0.0

# (str) Orientation of the app
orientation = portrait

# (bool) If true, the app will run in full-screen mode
fullscreen = 0

# (list) Permissions for Android (needed for Bluetooth)
android.permissions = BLUETOOTH,BLUETOOTH_ADMIN,BLUETOOTH_CONNECT,BLUETOOTH_SCAN,ACCESS_FINE_LOCATION,ACCESS_COARSE_LOCATION

# (int) Target Android API
android.api = 33

# (int) Minimum Android API your app will support
android.minapi = 21

# (list) Optional architectures you want to support
# android.archs = arm64-v8a, armeabi-v7a

# (str) Path to your app icon (uncomment the following line to specify the icon file)
# icon.filename = %(source.dir)s/assets/app_icon.png

[buildozer]
# (int) Log level (0 = no logs, 1 = errors, 2 = warnings, 3 = info)
log_level = 2

# (bool) Whether to show a warning when running with root
warn_on_root = 0