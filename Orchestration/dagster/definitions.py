from dagster import Definitions

from Orchestration.dagster.assets import get_assets
from Orchestration.dagster.jobs import get_jobs
from Orchestration.dagster.schedules import get_schedules

defs = Definitions(
    assets=get_assets(),
    jobs=get_jobs(),
    schedules=get_schedules(),
)
