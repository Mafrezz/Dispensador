# --- Simulación "teléfono" SOLO en PC ---
import os
from kivy.utils import platform

if platform != "android":
    # Solo en Windows/Linux de escritorio
    os.environ["KIVY_METRICS_DENSITY"] = "2.0"   # escala moderada
    from kivy.core.window import Window
    Window.size = (360, 750)                     # para que se vea como teléfono
else:
    # En Android NO tocamos Window ni density
    from kivy.core.window import Window
# --- fin simulación ---

from kivy.config import Config
Config.set('kivy', 'log_level', 'info')

from kivy.lang import Builder
from kivy.clock import Clock
from kivy.metrics import dp
from kivy.properties import StringProperty

from kivymd.app import MDApp
from kivymd.uix.menu import MDDropdownMenu
from kivymd.uix.snackbar import MDSnackbar
from kivymd.uix.list import MDListItem
from kivymd.uix.dialog import MDDialog
from kivymd.uix.button import MDButton, MDButtonText
from kivymd.uix.textfield import MDTextField
from kivymd.uix.boxlayout import MDBoxLayout

from datetime import datetime
from time import time
import traceback

from models import DB
from bt import get_bluetooth
from scheduler import SchedulerEngine

with open("ui.kv", "r", encoding="utf-8") as f:
    KV = f.read()


def _toast(msg: str):
    try:
        MDSnackbar(text=str(msg)).open()
    except Exception:
        print("[Snackbar FALLÓ]", msg)


class FoodForm(MDBoxLayout):
    def __init__(self, app, food=None, **kwargs):
        super().__init__(**kwargs)
        self.orientation = "vertical"
        self.spacing = dp(8)
        self.app = app
        self.food = food
        self.name = MDTextField(hint_text="Nombre", text=food[1] if food else "")
        self.gpp = MDTextField(
            hint_text="Gramos por porción",
            text=str(food[2]) if food else "100",
            input_filter="float",
        )
        self.cpp = MDTextField(
            hint_text="Calorías por porción",
            text=str(food[3]) if food else "100",
            input_filter="float",
        )
        self.add_widget(self.name)
        self.add_widget(self.gpp)
        self.add_widget(self.cpp)


class ScheduleForm(MDBoxLayout):
    def __init__(self, app, **kwargs):
        super().__init__(**kwargs)
        self.orientation = "vertical"
        self.spacing = dp(8)
        self.app = app
        self.food_field = MDTextField(hint_text="Alimento (exacto)")
        self.hopper_field = MDTextField(
            hint_text="Tolva (1-3)", input_filter="int", text="1"
        )
        self.grams_field = MDTextField(
            hint_text="Gramos", input_filter="float", text="50"
        )
        self.datetime_field = MDTextField(
            hint_text="Fecha y hora (YYYY-MM-DD HH:MM)",
            text=datetime.now().strftime("%Y-%m-%d %H:%M"),
        )
        self.add_widget(self.food_field)
        self.add_widget(self.hopper_field)
        self.add_widget(self.grams_field)
        self.add_widget(self.datetime_field)


class AppMain(MDApp):
    selected_food = None
    selected_food_name = None
    unit = "gramos"
    bt_status_text = StringProperty("No conectado")

    def build(self):
        self.title = "Dispensador Inteligente"
        self.theme_cls.primary_palette = "Blue"
        self.theme_cls.theme_style = "Light"

        # --- Inicializar DB ---
        try:
            self.db = DB()
        except Exception as e:
            print("ERROR iniciando DB:", e)
            traceback.print_exc()
            # Si la base falla no podemos continuar
            raise

        # --- Inicializar Bluetooth ---
        try:
            self.bt = get_bluetooth()
        except Exception as e:
            print("ERROR iniciando Bluetooth:", e)
            traceback.print_exc()

            # Creamos un stub para que la app no truene y puedas probar UI
            class DummyBT:
                def is_connected(self):
                    return False

                def list_paired(self):
                    return []

                def connect(self, mac):
                    return False, "Bluetooth no disponible"

                def send(self, cmd):
                    return False, "Bluetooth no disponible"

            self.bt = DummyBT()
            self.bt_status_text = "BT no disponible"

        # --- Inicializar Scheduler ---
        try:
            self.scheduler = SchedulerEngine(self.db, self._send_schedule)
            self.scheduler.start()
        except Exception as e:
            print("ERROR iniciando Scheduler:", e)
            traceback.print_exc()
            self.scheduler = None

        # --- Cargar interfaz ---
        self.root = Builder.load_string(KV)
        self.sm = self.root  # MDScreenManager

        Clock.schedule_once(lambda *_: self._refresh_foods_ui(), 0.5)
        Clock.schedule_interval(lambda *_: self._refresh_conversion_label(), 0.2)
        Clock.schedule_interval(lambda *_: self._refresh_history_ui(), 10)
        Clock.schedule_interval(lambda *_: self._refresh_schedule_ui(), 10)
        return self.root

    # ---------------- Navegación ----------------
    def go(self, screen_name):
        self.sm.current = screen_name
        if screen_name == "foods":
            self._refresh_foods_ui()
        elif screen_name == "schedule":
            self._refresh_schedule_ui()
        elif screen_name == "history":
            self._refresh_history_ui()

    def go_back(self):
        self.sm.current = "root"

    # ---------------- Dispensar ----------------
    def _dispenser(self):
        return self.sm.get_screen("root").ids.dispenser

    def open_food_menu(self, _caller=None):
        try:
            foods = self.db.list_foods()
            if not foods:
                _toast("No hay alimentos en la base")
                return
            menu_items = []
            for fid, name, gpp, cpp in foods:
                menu_items.append(
                    {
                        "text": name,
                        "on_release": (
                            lambda i=fid, n=name: (
                                self._select_food(i, n),
                                self.food_menu.dismiss(),
                            )
                        ),
                    }
                )
            caller = self._dispenser().ids.food_btn
            self.food_menu = MDDropdownMenu(
                caller=caller, items=menu_items, width_mult=4
            )
            self.food_menu.open()
        except Exception as e:
            traceback.print_exc()
            _toast(f"Error abriendo menú: {e}")

    def _select_food(self, food_id, food_name):
        self.selected_food = self.db.get_food(food_id)
        self.selected_food_name = food_name
        disp = self._dispenser()
        disp.ids.food_btn_text.text = food_name
        disp.ids.sel_food.text = f"Alimento: {food_name}"

    def set_unit(self, unit_text):
        self.unit = unit_text
        disp = self._dispenser()
        disp.ids.unit_label.text = f"Unidad actual: {unit_text}"
        self._refresh_conversion_label()

    def _current_amount(self):
        try:
            return float(self._dispenser().ids.amount.text.strip())
        except Exception:
            return 0.0

    def _current_hopper(self):
        try:
            v = int(self._dispenser().ids.hopper_idx.text.strip())
            return max(1, min(3, v))
        except Exception:
            return 1

    def _refresh_conversion_label(self):
        disp = self._dispenser()
        label = disp.ids.conversion_label

        if not self.selected_food:
            label.text = "Seleccione un alimento para ver equivalencias"
            return

        _, name, gpp, cpp = self.selected_food
        val = self._current_amount()
        if self.unit == "gramos":
            kcal = self.db.calories_for_grams(val, gpp, cpp)
            label.text = f"≈ {kcal:.0f} kcal"
        else:
            grams = self.db.grams_for_calories(val, gpp, cpp)
            label.text = f"≈ {grams:.0f} g"

    def dispense(self):
        try:
            # Validaciones suaves para que no cierre la app
            try:
                connected = bool(self.bt.is_connected())
            except Exception:
                connected = False

            if not connected:
                _toast("Conéctese por Bluetooth primero")
                return

            if not self.selected_food:
                _toast("Seleccione un alimento")
                return

            amount = self._current_amount()
            hopper = self._current_hopper()
            _, name, gpp, cpp = self.selected_food

            grams = (
                amount
                if self.unit == "gramos"
                else self.db.grams_for_calories(amount, gpp, cpp)
            )
            grams = max(0, grams)

            cmd = f"DISPENSE:{hopper}:{int(round(grams))}"
            ok, msg = self.bt.send(cmd)
            _toast(msg)

            if ok:
                kcal = self.db.calories_for_grams(grams, gpp, cpp)
                self.db.add_history(name, hopper, grams, kcal, int(time()))
                self._refresh_history_ui()
        except Exception as e:
            traceback.print_exc()
            _toast(f"Error al dispensar: {e}")

    # ---------------- Conectar ----------------
    def refresh_paired(self):
        try:
            self.bt_status_text = "Buscando..."
            scr = self.sm.get_screen("connect")
            lst = scr.ids.devices_list
            lst.clear_widgets()

            devices = self.bt.list_paired()
            if not devices:
                self.bt_status_text = "No hay emparejados o BT apagado"
                _toast(self.bt_status_text)
                return

            self.bt_status_text = f"Encontrados: {len(devices)}"
            for name, mac in devices:
                item = MDListItem(
                    headline_text=f"{name}  [{mac}]",
                    on_release=lambda x=None, m=mac: self._connect_to(m),
                )
                lst.add_widget(item)
        except Exception as e:
            traceback.print_exc()
            self.bt_status_text = "Error buscando dispositivos"
            _toast(f"Error al buscar BT: {e}")

    def _connect_to(self, mac):
        try:
            ok, msg = self.bt.connect(mac)
            self.bt_status_text = msg
            _toast(msg)
        except Exception as e:
            traceback.print_exc()
            self.bt_status_text = "Error al conectar"
            _toast(f"No se pudo conectar: {e}")

    # ---------------- Alimentos (CRUD) ----------------
    def _refresh_foods_ui(self):
        foods_scr = self.sm.get_screen("foods")
        foods = self.db.list_foods()
        rv = foods_scr.ids.foods_rv
        rv.data = [
            {
                "headline_text": f"{name} · {gpp:g} g → {cpp:g} kcal",
                "on_release": (lambda x=None, i=fid: self.open_food_form(i)),
            }
            for fid, name, gpp, cpp in foods
        ]

    def open_food_form(self, food_id):
        food = self.db.get_food(food_id) if food_id else None
        form = FoodForm(self, food=food)
        self.food_dialog = MDDialog(
            title=("Editar alimento" if food else "Nuevo alimento"),
            type="custom",
            content_cls=form,
            buttons=[
                MDButton(
                    MDButtonText(text="Cancelar"),
                    style="text",
                    on_release=lambda *_: self.food_dialog.dismiss(),
                ),
                MDButton(
                    MDButtonText(text="Guardar"),
                    style="elevated",
                    on_release=lambda *_: self._save_food(
                        form, food[0] if food else None
                    ),
                ),
            ],
        )
        self.food_dialog.open()

    def _save_food(self, form, food_id):
        try:
            name = form.name.text.strip()
            gpp = float(form.gpp.text.strip())
            cpp = float(form.cpp.text.strip())
            if not name or gpp <= 0 or cpp <= 0:
                raise ValueError("Datos inválidos")
            self.db.upsert_food(name, gpp, cpp, food_id)
            self.food_dialog.dismiss()
            _toast("Guardado")
            self._refresh_foods_ui()
        except Exception as e:
            traceback.print_exc()
            _toast(f"Error: {e}")

    # ---------------- Programación ----------------
    def _refresh_schedule_ui(self):
        schedule_scr = self.sm.get_screen("schedule")
        rows = self.db.list_schedules()
        rv = schedule_scr.ids.sched_rv
        rv.data = []
        for sched_id, name, hopper, grams, when_ts, executed, food_id in rows:
            dt = datetime.fromtimestamp(when_ts).strftime("%Y-%m-%d %H:%M")
            status = "✓ ejecutado" if executed else "⏳ pendiente"
            rv.data.append(
                {
                    "headline_text": f"{name} · {grams:.0f} g (Tolva {hopper})",
                    "supporting_text": f"{dt}  —  {status}",
                }
            )

    def open_schedule_form(self):
        form = ScheduleForm(self)
        self.sched_dialog = MDDialog(
            title="Programar dispensado",
            type="custom",
            content_cls=form,
            buttons=[
                MDButton(
                    MDButtonText(text="Cancelar"),
                    style="text",
                    on_release=lambda *_: self.sched_dialog.dismiss(),
                ),
                MDButton(
                    MDButtonText(text="Programar"),
                    style="elevated",
                    on_release=lambda *_: self._save_schedule(form),
                ),
            ],
        )
        self.sched_dialog.open()

    def _save_schedule(self, form):
        try:
            food_name = form.food_field.text.strip()
            hopper = int(form.hopper_field.text.strip())
            grams = float(form.grams_field.text.strip())
            dt = datetime.strptime(
                form.datetime_field.text.strip(), "%Y-%m-%d %H:%M"
            )
            food = self.db.food_by_name(food_name)
            if not food:
                raise ValueError("Alimento no encontrado (verifique nombre exacto)")
            self.db.add_schedule(food[0], hopper, grams, int(dt.timestamp()))
            self.sched_dialog.dismiss()
            _toast("Programado")
            self._refresh_schedule_ui()
        except Exception as e:
            traceback.print_exc()
            _toast(f"Error: {e}")

    def _send_schedule(self, food_id, food_name, hopper_idx, grams):
        try:
            cmd = f"DISPENSE:{hopper_idx}:{int(round(grams))}"
            ok, msg = self.bt.send(cmd)
            if ok:
                food = self.db.get_food(food_id)
                _, name, gpp, cpp = food
                kcal = self.db.calories_for_grams(grams, gpp, cpp)
                self.db.add_history(name, hopper_idx, grams, kcal, int(time()))
            return ok
        except Exception as e:
            traceback.print_exc()
            _toast(f"Error enviando programación: {e}")
            return False

    # ---------------- Historial ----------------
    def _refresh_history_ui(self):
        history_scr = self.sm.get_screen("history")
        items = self.db.history_last_7_days(int(time()))
        rv = history_scr.ids.hist_rv
        rv.data = []
        for name, hopper, grams, kcal, ts in items:
            dt = datetime.fromtimestamp(ts).strftime("%Y-%m-%d %H:%M")
            rv.data.append(
                {
                    "headline_text": f"{name} · {grams:.0f} g  (≈ {kcal:.0f} kcal)",
                    "supporting_text": f"{dt}  —  Tolva {hopper}",
                }
            )


if __name__ == "__main__":
    AppMain().run()