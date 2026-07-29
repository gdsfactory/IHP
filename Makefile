install:
	uv venv --python 3.12
	uv sync --extra docs --extra dev --extra simulation

rm-samples:
	rm -rf ihp/samples

dev: install
	gh api "repos/doplaydo/pdk-ci-workflow/contents/templates/.pre-commit-config.yaml?ref=main" --header "Accept: application/vnd.github.raw+json" > .pre-commit-config.yaml
	uv run pre-commit clean
	uv run pre-commit install

update-pre:
	pre-commit autoupdate

tech:
	python install_tech.py

vacask-models:
	python scripts/convert_vacask_models.py


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
	rm -rf docs/_build docs/palace_demo_cpw.md docs/palace_demo_microstrip.md docs/examples/

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
	mkdir -p docs/examples

notebooks:
	@if [ "$$(uname -s)" = "Linux" ]; then sudo apt-get install -y --no-install-recommends libglu1-mesa libgl1 libegl1 libosmesa6 2>/dev/null; fi
	VTK_DEFAULT_RENDER_WINDOW_OFFSCREEN=1 uv run --extra docs --extra simulation jupyter nbconvert --to notebook --execute \
		--ExecutePreprocessor.timeout=600 \
		--output-dir /tmp/ihp-notebooks \
		docs/palace_demo_cpw.ipynb docs/palace_demo_microstrip.ipynb
	uv run --extra docs jupyter nbconvert --to markdown \
		--output-dir docs \
		/tmp/ihp-notebooks/palace_demo_cpw.ipynb \
		/tmp/ihp-notebooks/palace_demo_microstrip.ipynb
	uv run python docs/hooks.py docs/palace_demo_cpw.md docs/palace_demo_microstrip.md
	mkdir -p docs/examples
	uv run --extra docs jupyter nbconvert --to notebook --execute \
		--ExecutePreprocessor.timeout=600 \
		--output-dir /tmp/ihp-notebooks \
		examples/design_examples/spice_to_yml/spice_to_yml.ipynb \
		examples/design_examples/spice_and_gds_to_yml/spice_and_gds_to_yml.ipynb
	uv run --extra docs jupyter nbconvert --to markdown \
		--output-dir docs/examples \
		/tmp/ihp-notebooks/spice_to_yml.ipynb \
		/tmp/ihp-notebooks/spice_and_gds_to_yml.ipynb
	uv run python docs/hooks.py docs/examples/spice_to_yml.md docs/examples/spice_and_gds_to_yml.md
	uv run --extra docs jupyter nbconvert --to markdown --execute \
		--ExecutePreprocessor.timeout=600 \
		--output-dir docs/examples \
		--output lna_160ghz \
		examples/design_examples/ihp_160g_lna/design_data/factory/lna_notebook.ipynb
	uv run python docs/hooks.py docs/examples/lna_160ghz.md

docs: cp-docs cells notebooks
	uv run --extra docs zensical build -f docs/zensical.toml

docs-serve: cp-docs notebooks
	uv run --extra docs zensical serve -f docs/zensical.toml -a localhost:8080

update-changelog:
	claude -p "remove links and make a user friendly changelog from @CHANGELOG.md to @docs/changelog.md"

.PHONY: drc drc-sample doc docs docs-pdf build update-changelog notebooks
