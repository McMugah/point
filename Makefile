install:
	pip install -r requirements.txt
test:
	pytest --cov=app tests/
format:
	isort ./app
run:
	python3 run.py
lint:
	pylint ./app
security:
	bandit ./app
