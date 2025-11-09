import sqlite3

DB_NAME = "app.db"

DEFAULT_FOODS = [
    ("Arroz", 100.0, 130.0),
    ("Avena", 100.0, 389.0),
    ("Frijol", 100.0, 347.0),
]

class DB:
    def __init__(self, path=DB_NAME):
        self.conn = sqlite3.connect(path, check_same_thread=False)
        self.conn.execute("PRAGMA foreign_keys=ON")
        self._migrate()

    def _migrate(self):
        cur = self.conn.cursor()
        cur.execute(
            "CREATE TABLE IF NOT EXISTS foods("
            "id INTEGER PRIMARY KEY AUTOINCREMENT,"
            "name TEXT UNIQUE NOT NULL,"
            "grams_per_portion REAL NOT NULL,"
            "calories_per_portion REAL NOT NULL"
            ");"
        )
        cur.execute(
            "CREATE TABLE IF NOT EXISTS schedules("
            "id INTEGER PRIMARY KEY AUTOINCREMENT,"
            "food_id INTEGER NOT NULL,"
            "hopper_index INTEGER NOT NULL,"
            "grams REAL NOT NULL,"
            "when_ts INTEGER NOT NULL,"
            "executed INTEGER NOT NULL DEFAULT 0,"
            "FOREIGN KEY(food_id) REFERENCES foods(id) ON DELETE CASCADE"
            ");"
        )
        cur.execute(
            "CREATE TABLE IF NOT EXISTS history("
            "id INTEGER PRIMARY KEY AUTOINCREMENT,"
            "food_name TEXT NOT NULL,"
            "hopper_index INTEGER NOT NULL,"
            "grams REAL NOT NULL,"
            "calories REAL NOT NULL,"
            "ts INTEGER NOT NULL"
            ");"
        )
        self.conn.commit()

        cur.execute("SELECT COUNT(*) FROM foods;")
        if cur.fetchone()[0] == 0:
            cur.executemany(
                "INSERT OR REPLACE INTO foods(name, grams_per_portion, calories_per_portion) VALUES(?,?,?)",
                DEFAULT_FOODS
            )
            self.conn.commit()

    def list_foods(self):
        cur = self.conn.cursor()
        cur.execute("SELECT id, name, grams_per_portion, calories_per_portion FROM foods ORDER BY name;")
        return cur.fetchall()

    def upsert_food(self, name, grams_per_portion, calories_per_portion, food_id=None):
        cur = self.conn.cursor()
        if food_id is None:
            cur.execute(
                "INSERT OR REPLACE INTO foods(name, grams_per_portion, calories_per_portion) VALUES(?,?,?)",
                (name, float(grams_per_portion), float(calories_per_portion))
            )
        else:
            cur.execute(
                "UPDATE foods SET name=?, grams_per_portion=?, calories_per_portion=? WHERE id=?",
                (name, float(grams_per_portion), float(calories_per_portion), int(food_id))
            )
        self.conn.commit()

    def get_food(self, food_id):
        cur = self.conn.cursor()
        cur.execute("SELECT id, name, grams_per_portion, calories_per_portion FROM foods WHERE id=?", (int(food_id),))
        return cur.fetchone()

    def food_by_name(self, name):
        cur = self.conn.cursor()
        cur.execute("SELECT id, name, grams_per_portion, calories_per_portion FROM foods WHERE name=?", (name,))
        return cur.fetchone()

    @staticmethod
    def calories_for_grams(grams, grams_per_portion, calories_per_portion):
        if grams_per_portion <= 0:
            return 0.0
        return (grams / grams_per_portion) * calories_per_portion

    @staticmethod
    def grams_for_calories(calories, grams_per_portion, calories_per_portion):
        if calories_per_portion <= 0:
            return 0.0
        return (calories / calories_per_portion) * grams_per_portion

    def add_schedule(self, food_id, hopper_index, grams, when_ts):
        cur = self.conn.cursor()
        cur.execute(
            "INSERT INTO schedules(food_id, hopper_index, grams, when_ts) VALUES(?,?,?,?)",
            (int(food_id), int(hopper_index), float(grams), int(when_ts))
        )
        self.conn.commit()

    def list_schedules(self):
        cur = self.conn.cursor()
        cur.execute(
            "SELECT s.id, f.name, s.hopper_index, s.grams, s.when_ts, s.executed, s.food_id "
            "FROM schedules s JOIN foods f ON f.id = s.food_id ORDER BY s.when_ts ASC;"
        )
        return cur.fetchall()

    def mark_executed(self, sched_id):
        cur = self.conn.cursor()
        cur.execute("UPDATE schedules SET executed=1 WHERE id=?", (int(sched_id),))
        self.conn.commit()

    def add_history(self, food_name, hopper_index, grams, calories, ts):
        cur = self.conn.cursor()
        cur.execute(
            "INSERT INTO history(food_name, hopper_index, grams, calories, ts) VALUES(?,?,?,?,?)",
            (food_name, int(hopper_index), float(grams), float(calories), int(ts))
        )
        self.conn.commit()

    def history_last_7_days(self, now_ts):
        cur = self.conn.cursor()
        seven_days_ago = int(now_ts) - 7*24*3600
        cur.execute(
            "SELECT food_name, hopper_index, grams, calories, ts FROM history WHERE ts >= ? ORDER BY ts DESC;",
            (seven_days_ago,)
        )
        return cur.fetchall()
