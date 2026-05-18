install:
	uv venv --python 3.12
	uv sync --extra docs --extra dev --extra simulation

rm-samples:
	rm -rf ihp/samples

dev: install
	curl -sf https://raw.githubusercontent.com/doplaydo/pdk-ci-workflow/main/templates/.pre-commit-config.yaml -o .pre-commit-config.yaml
	uv run pre-commit install

update-pre:
	pre-commit autoupdate

tech:
	python install_tech.py

test:
	uv run pytest -s

test-force: install
	uv run pytest -s --force-regen

git-rm-merged:
	git branch -D `git branch --merged | grep -v \* | xargs`

release:
	git push
	git push origin --tags

build:
	rm -rf dist
	pip install build
	python -m build

gmsh:
	sudo apt-get update
	sudo apt-get install -y python3-gmsh gmsh libglu1-mesa libxi-dev libxmu-dev libglu1-mesa-dev libosmesa6 libegl1

docs-clean: gmsh
	rm -rf docs/_build

docs: docs-clean
	uv run python .github/write_cells.py
	uv run jb build docs

docs-serve: docs
	python -m http.server -d docs/_build/html 8000

mask:
	python ubcpdk/samples/test_masks.py

.PHONY: drc doc docs docs-clean docs-serve install build
