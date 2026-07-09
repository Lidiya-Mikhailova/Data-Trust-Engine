from Storage.interfaces import AbstractObservabilityDB


class SQLiteObservabilityDB(AbstractObservabilityDB):
    async def store(self, collection: str, record: dict) -> str:
        ...

    async def query(self, collection: str, filters=None) -> list[dict]:
        ...

    async def delete(self, collection: str, record_id: str) -> bool:
        ...


__all__ = ["SQLiteObservabilityDB"]
