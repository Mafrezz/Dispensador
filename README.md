# Dispensador Inteligente - App Móvil (Kivy)

Aplicación en **Python (Kivy + KivyMD)** para Android (y ejecutable en escritorio para pruebas con Bluetooth simulado).
Desarrollada para Visual Studio Code.

## Características
- Conexión Bluetooth clásica (HC-05/HC-06) en Android (RFCOMM / SPP UUID).
- Dispensar por **gramos** o **calorías** (conversión según base de datos de alimentos).
- **CRUD de alimentos** (nombre, gramos por porción, calorías por porción).
- **Programación** de dispensado (alimento, cantidad, fecha y hora).
- **Historial** de los últimos 7 días.
- Persistencia con **SQLite** (`app.db`).

> En escritorio (Windows/macOS/Linux) se usa un **Bluetooth simulado** para poder probar la interfaz sin hardware.

## Requisitos (desarrollo local)
1. Python 3.10+
2. `pip install -r requirements.txt`
3. Ejecutar: `python main.py`

## Empaquetar en Android (opción A: Buildozer en Linux/WSL)
1. Instala buildozer (guía Kivy). En WSL Ubuntu suele ser lo más cómodo.
2. Genera `buildozer.spec` con `buildozer init` y agrega en `requirements`: `kivy, kivymd, plyer, pyjnius`
3. Permisos Android (en `buildozer.spec`):
   ```
   android.permissions = BLUETOOTH, BLUETOOTH_ADMIN, BLUETOOTH_CONNECT, BLUETOOTH_SCAN, ACCESS_FINE_LOCATION
   android.api = 33
   android.minapi = 24
   ```
4. Compila: `buildozer -v android debug`

## Empaquetar en Android (opción B: BeeWare/Briefcase)
Preferible Kivy+Buildozer para acceso a Bluetooth clásico. BeeWare no está tan maduro para Bluetooth Android.

## Conexión con Arduino
- Usa un módulo **HC-05** configurado como **Slave**, PIN por defecto `1234` o `0000` (parear en Android).
- Protocolo simple vía Serial RFCOMM (SPP):
  - `DISPENSE:<hopper_index>:<grams>\n`
  - Ejemplo: `DISPENSE:1:50\n` → Tolva 1, 50 gramos
- Opcional: `PING\n` para pruebas, el firmware puede responder `OK\n`.

## Notas sobre Programación
La programación se ejecuta **mientras la app está abierta**. Si necesitas que funcione en segundo plano o con la app cerrada,
deberás implementar un **Android Service** via `python-for-android` y `service=...` (no incluido aquí por brevedad).

## Estructura
```
dispensador_app_kivy/
├── assets/
│   └── app_icon.png
├── main.py
├── models.py
├── bt.py
├── scheduler.py
├── ui.kv
├── requirements.txt
└── README.md
```
