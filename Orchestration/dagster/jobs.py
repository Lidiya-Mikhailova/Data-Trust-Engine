from dagster import JobDefinition

_jobs: list[JobDefinition] = []


def get_jobs() -> list[JobDefinition]:
    return list(_jobs)


def register_job(job: JobDefinition) -> None:
    _jobs.append(job)
