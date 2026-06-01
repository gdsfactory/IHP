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

test-gfp-projects:
	cd ihp-gdsfactory--sample-projects/ihp--public--project && uv run --directory $(CURDIR) gfp test

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

docs-clean:
	rm -rf docs/_build

mask:
	python ubcpdk/samples/test_masks.py

docs-pdf:
	uv run python .github/write_cells.py
	cp CHANGELOG.md docs/changelog.md
	uv run mkdocs build -f mkdocs-pdf.yml

cells:
	uv run python .github/write_cells.py

cp-docs:
	cp README.md docs/index.md
	cp CHANGELOG.md docs/changelog.md

docs: cp-docs cells
	uv run --extra docs zensical build -f docs/zensical.toml

docs-serve: cp-docs cells
	cp CHANGELOG.md docs/changelog.md
	uv run --extra docs zensical serve -f docs/zensical.toml -a localhost:8080

.PHONY: drc drc-sample doc docs docs-pdf build
