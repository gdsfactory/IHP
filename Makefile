install:
	uv sync --extra docs --extra dev --extra simulation

all:
	uv run python ihp/samples/all_cells.py

rm-samples:
	rm -rf ihp/samples

dev: install

update-pre:
	pre-commit autoupdate

tech:
	python install_tech.py

test:
	uv run pytest -s

test-ports:
	uv run pytest -s tests/test_cells.py::test_optical_port_positions

test-force:
	uv run pytest -s --update-gds-refs --force-regen

git-rm-merged:
	git branch -D `git branch --merged | grep -v \* | xargs`

release:
	git push
	git push origin --tags

build:
	rm -rf dist
	pip install build
	python -m build

docs:
	uv run python .github/write_cells.py
	uv run jb build docs

mask:
	python ubcpdk/samples/test_masks.py

.PHONY: drc doc docs install build
