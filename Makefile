.PHONY: install lint format test run-api clean

install:
	pip install -r requirements.txt

lint:
	ruff check .

format:
	black .

test:
	pytest

run-api:
	uvicorn API.main:app --reload

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
