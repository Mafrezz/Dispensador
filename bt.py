from kivy.utils import platform
from datetime import datetime

if platform == "android":
    from jnius import autoclass
    BluetoothAdapter = autoclass('android.bluetooth.BluetoothAdapter')
    UUID = autoclass('java.util.UUID')

SPP_UUID = "00001101-0000-1000-8000-00805F9B34FB"

class MockBluetooth:
    def __init__(self):
        self._connected = False
        self._device_name = None

    def list_paired(self):
        return [("HC-05-MOCK", "00:00:00:00:00:00")]

    def connect(self, name_or_mac):
        self._connected = True
        self._device_name = name_or_mac
        return True, f"Conectado a {name_or_mac} (simulado)"

    def is_connected(self):
        return self._connected

    def send(self, text: str):
        if not self._connected:
            return False, "No conectado"
        print(f"[MOCK BT] → {text.strip()}")
        return True, "Enviado (simulado)"

class AndroidBluetooth:
    def __init__(self):
        self._connected = False
        self._socket = None
        self._in_stream = None
        self._out_stream = None

    def list_paired(self):
        adapter = BluetoothAdapter.getDefaultAdapter()
        if adapter is None or not adapter.isEnabled():
            return []
        set_bonded = adapter.getBondedDevices()
        devices = []
        for d in set_bonded.toArray():
            devices.append((d.getName(), d.getAddress()))
        return devices

    def connect(self, name_or_mac):
        try:
            adapter = BluetoothAdapter.getDefaultAdapter()
            if adapter is None or not adapter.isEnabled():
                return False, "Bluetooth apagado o no disponible"
            target = None
            for d in adapter.getBondedDevices().toArray():
                if d.getAddress() == name_or_mac or d.getName() == name_or_mac:
                    target = d
                    break
            if target is None:
                return False, "Dispositivo no emparejado"

            uuid = UUID.fromString(SPP_UUID)
            socket = target.createRfcommSocketToServiceRecord(uuid)
            adapter.cancelDiscovery()
            socket.connect()

            self._socket = socket
            self._in_stream = socket.getInputStream()
            self._out_stream = socket.getOutputStream()
            self._connected = True
            return True, f"Conectado a {target.getName()}"
        except Exception as e:
            return False, f"Error conectando: {e}"

    def is_connected(self):
        return self._connected

    def send(self, text: str):
        try:
            if not self._connected or self._out_stream is None:
                return False, "No conectado"
            if not text.endswith("\n"):
                text = text + "\n"
            self._out_stream.write(text.encode('utf-8'))
            self._out_stream.flush()
            return True, "Enviado"
        except Exception as e:
            return False, f"Error enviando: {e}"

def get_bluetooth():
    if platform == "android":
        return AndroidBluetooth()
    return MockBluetooth()
