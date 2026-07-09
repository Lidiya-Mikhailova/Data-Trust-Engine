from Storage.interfaces import AbstractWarehouse


class BigQueryWarehouse(AbstractWarehouse):
    async def load(
        self, table: str, data: list[dict], schema=None
    ) -> int:
        ...

    async def query(self, sql: str, params=None) -> list[dict]:
        ...

    async def truncate(self, table: str) -> None:
        ...

    async def table_exists(self, table: str) -> bool:
        ...


__all__ = ["BigQueryWarehouse"]
