
test:
	uv run pytest -v tdm/tests/integration_tests/*  -x

make build:
	uv run pyinstaller --name tdm --onefile --specpath bin/ --noconfirm tdm/__main__.py
	uv run pyinstaller --distpath bin/ bin/tdm.spec
	rm bin/tdm.spec
	rm -rf dist
	rm -rf build




