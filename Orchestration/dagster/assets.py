from dagster import AssetsDefinition

_assets: list[AssetsDefinition] = []


def get_assets() -> list[AssetsDefinition]:
    return list(_assets)


def register_asset(asset: AssetsDefinition) -> None:
    _assets.append(asset)
