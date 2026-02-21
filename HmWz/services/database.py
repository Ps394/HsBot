
import os
import logging
import aiosqlite
from contextlib import asynccontextmanager
from typing import Tuple, Optional

class Database:
    def __init__(self,*, folder: str = "data", filename: str = "data.db") -> None:
        """
        Initialisiert die Datenbankverbindung und erstellt den Ordner für die Datenbankdatei, falls dieser nicht existiert.

        :param folder: Der Ordner, in dem die Datenbankdatei gespeichert werden soll. Standardmäßig "data".
        :type folder: str
        :param filename: Der Name der Datenbankdatei. Standardmäßig "data.db".
        :type filename: str
        """
        os.makedirs(folder, exist_ok=True)
        self.file = os.path.join(folder, filename)
        self.logger = logging.getLogger(__name__)

    @asynccontextmanager
    async def connect(self):
        """
        Stellt eine asynchrone Verbindung zur SQLite-Datenbank her und sorgt dafür, dass die Verbindung ordnungsgemäß geschlossen wird.
         
         :return: Ein aiosqlite.Connection-Objekt, das für Datenbankoperationen verwendet werden kann.
         :rtype: aiosqlite.Connection
         :raises Exception: Wenn ein Fehler bei der Herstellung der Verbindung auftritt, wird die Ausnahme protokolliert und erneut ausgelöst.
        """
        database = None
        try:
            database = await aiosqlite.connect(self.file)
            await database.execute("PRAGMA foreign_keys = ON;")
            await database.execute("PRAGMA journal_mode = WAL;")
            await database.execute("PRAGMA synchronous = NORMAL;")
            database.row_factory = aiosqlite.Row
            yield database
        except Exception as e:
            self.logger.exception(f"Database connection error: {e}")
            raise
        finally:
            if database:
                await database.close()

    async def execute(self, query: str, params: Tuple = ()) -> aiosqlite.Cursor:
        """
        Führt eine SQL-Abfrage aus, die keine Ergebnisse zurückgibt (z.B. INSERT, UPDATE, DELETE).
        
        :param query: Die SQL-Abfrage, die ausgeführt werden soll.
        :type query: str
        :param params: Die Parameter für die SQL-Abfrage. Standardmäßig ein leeres Tupel.
        :type params: Tuple
        :return: Ein aiosqlite.Cursor-Objekt, das das Ergebnis der Abfrage enthält.
        :rtype: aiosqlite.Cursor
        :raises Exception: Wenn ein Fehler bei der Ausführung der Abfrage auftritt, wird die Ausnahme protokolliert und erneut ausgelöst.
        """
        async with self.connect() as connection:
            await connection.execute(query, params)
            await connection.commit()
            
    async def fetch_all(self, query: str, params: Tuple = ()) -> Tuple[aiosqlite.Row, ...]:
        """
        Führt eine SQL-Abfrage aus, die mehrere Ergebnisse zurückgibt (z.B. SELECT) und gibt diese als Tupel von aiosqlite.Row-Objekten zurück.

        :param query: Die SQL-Abfrage, die ausgeführt werden soll.
        :type query: str
        :param params: Die Parameter für die SQL-Abfrage. Standardmäßig ein leeres Tupel.
        :type params: Tuple
        :return: Ein Tupel von aiosqlite.Row-Objekten, die die Ergebnisse der Abfrage enthalten.
        :rtype: Tuple[aiosqlite.Row, ...]
        :raises Exception: Wenn ein Fehler bei der Ausführung der Abfrage auftritt, wird die Ausnahme protokolliert und erneut ausgelöst.
        """
        async with self.connect() as connection:
            async with connection.execute(query, params) as cursor:
                return await cursor.fetchall()
    
    async def fetch_one(self, query: str, params: Tuple = ()) -> Optional[aiosqlite.Row]:
        """
        Führt eine SQL-Abfrage aus, die ein einzelnes Ergebnis zurückgibt (z.B. SELECT) und gibt dieses als aiosqlite.Row-Objekt zurück.

        :param query: Die SQL-Abfrage, die ausgeführt werden soll.
        :type query: str
        :param params: Die Parameter für die SQL-Abfrage. Standardmäßig ein leeres Tupel.
        :type params: Tuple
        :return: Ein aiosqlite.Row-Objekt, das das Ergebnis der Abfrage enthält, oder None, wenn kein Ergebnis gefunden wurde.
        :rtype: Optional[aiosqlite.Row]
        :raises Exception: Wenn ein Fehler bei der Ausführung der Abfrage auftritt, wird die Ausnahme protokolliert und erneut ausgelöst.
        """
        async with self.connect() as connection:
            async with connection.execute(query, params) as cursor:
                return await cursor.fetchone()

