from dagster import ScheduleDefinition

_schedules: list[ScheduleDefinition] = []


def get_schedules() -> list[ScheduleDefinition]:
    return list(_schedules)


def register_schedule(schedule: ScheduleDefinition) -> None:
    _schedules.append(schedule)
