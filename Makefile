.PHONY: install lint typecheck test validate-data-smoke validate-data-full train-smoke train-full docker-train docker-serve verify-deploy

install:
	pip install -e ".[dev]"

lint:
	ruff check src tests
	ruff format --check src tests

typecheck:
	mypy src/mlops

test:
	MLFLOW_DISABLED=1 pytest

validate-data-smoke:
	python -m mlops.cli validate-data --mode smoke

validate-data-full:
	python -m mlops.cli validate-data --mode full

train-smoke:
	MLOFLOW_DISABLED=1 python -m mlops.cli train --config configs/smoke.yaml

train-full:
	python -m mlops.cli train --config configs/full.yaml

docker-train:
	docker build -f docker/Dockerfile.train -t mlops-train .

docker-serve:
	docker build -f docker/Dockerfile.serve -t mlops-serve .

verify-deploy:
	docker compose -f docker/docker-compose.verify.yml up --build --abort-on-container-exit
