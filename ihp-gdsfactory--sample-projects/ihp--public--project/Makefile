install:
	uv sync --extra docs --extra dev

dev: install

update-pre:
	pre-commit autoupdate

tech:
	python install_tech.py

test:
	uv run pytest -s

test-force:
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

.PHONY: drc doc install build
