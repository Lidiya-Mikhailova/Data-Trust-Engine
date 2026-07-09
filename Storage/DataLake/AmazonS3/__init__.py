from Storage.interfaces import AbstractDataLake


class S3DataLake(AbstractDataLake):
    async def write(self, key: str, data: bytes) -> None:
        ...

    async def read(self, key: str) -> bytes:
        ...

    async def delete(self, key: str) -> None:
        ...

    async def list(self, prefix: str) -> list[str]:
        ...

    async def exists(self, key: str) -> bool:
        ...


__all__ = ["S3DataLake"]
