import sqlite3
import json
import os
from dotenv import load_dotenv

class InitDatabase:
    def __init__(self):
        load_dotenv()
        self.json_path = os.getenv("JSON_FILE")
        self.db_path = os.getenv("DB_FILE")
    
    def table_reset(self):
        with sqlite3.connect(self.db_path) as connect:
            cursor = connect.cursor()
            cursor.execute("DROP TABLE IF EXISTS file_inventory")
            cursor.execute('DELETE FROM sqlite_sequence WHERE name="file_inventory"')
            connect.commit()

    def init_database(self):
        with sqlite3.connect(self.db_path) as connect:
            cursor = connect.cursor()

            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS file_inventory (
                           id INTEGER PRIMARY KEY AUTOINCREMENT,
                           shelfmark TEXT UNIQUE,
                           exist BOOLEAN,
                           type TEXT,
                           type_confirmed BOOLEAN,
                           location TEXT,
                           size INTEGER,
                           file_count INTEGER
                           )
                    """
            )
            connect.commit()

    def import_data(self):
        with open(self.json_path, "r") as json_file:
            data = json.load(json_file)

        with sqlite3.connect(self.db_path) as connect:
            cursor = connect.cursor()

            for item in data["inventory"]:

                file_type = None
                if "film" in item:
                    file_type = "film"
                else:
                    file_type = "mag"

                connect.execute(
                    """
                    INSERT OR REPLACE INTO file_inventory (
                                shelfmark, 
                                exist, 
                                type, 
                                type_confirmed, 
                                location,
                                size,
                                file_count
                                )
                                VALUES (?, ?, ?, ?, ?, ?, ?)
                            """,
                    (
                        item["shelfmark"],
                        False,
                        file_type,
                        False,
                        "",
                        0,
                        0,
                    ),
                )
                connect.commit()


class DatabaseManager:
    def __init__(self, location, file):
        load_dotenv()

        self.db_path = os.getenv("DB_FILE")
        self.location = location
        self.file = file
        # self.init_database()


    def shelfmark_check(self):
        if self.file.endswith(".dpx"):
            shelfmark = os.path.basename(self.file).split(".")[0][:-8]
            format_type = "film"
        else:
            shelfmark = os.path.basename(self.file).split(".")[0]
            format_type = "mag"

        with sqlite3.connect(self.db_path) as connect:
            cursor = connect.cursor()
            cursor.execute(
                """
                SELECT * FROM file_inventory
                WHERE shelfmark = ?
            """,
                (shelfmark,),
            )

            record = cursor.fetchone()
            if record:
                cursor.execute(
                    """
                    UPDATE file_inventory
                    SET exist = ?,
                        location = ?,
                        type_confirmed = CASE
                            WHEN type = ? THEN TRUE
                            ELSE type_confirmed
                        END
                    WHERE shelfmark = ?
                """,
                    (True, self.location, format_type, shelfmark),
                )
                connect.commit()

    
    # def confirm_format_type(self):


def main():
    dbm = DatabaseManager(
        db_path="inventory.db",
        location="/path/to/file",
        file="BL_C1979-4701_s1_f1_v1.wav",
    )
    # dbm.table_reset() # reset db
    dbm.init_database() # initialise db
    # dbm.import_data(json_path="data/_preserved_sm_data.json") # import json data
    dbm.shelfmark_check()


# if __name__ == "__main__":
    # main()
