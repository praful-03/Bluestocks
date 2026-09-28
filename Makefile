.PHONY: all load ratios test report dashboard api clean help

PYTHON ?= .venv/Scripts/python.exe
PYTEST ?= .venv/Scripts/pytest.exe

all: load test

# Day 05: Full ETL load for all 12 files into nifty100.db
load:
	$(PYTHON) db/loader.py

# Sprint 2 target: Compute financial ratios
ratios:
	$(PYTHON) -c "print('Ratio engine (Sprint 2)')"

# Run unit and integration tests
test:
	$(PYTHON) -m pytest tests/ -v

# Generate reports and documentation
report:
	$(PYTHON) -c "print('Report generation')"

# Launch Streamlit dashboard
dashboard:
	streamlit run src/dashboard/app.py

# Launch FastAPI server
api:
	uvicorn src.api.main:app --reload --port 8000

# Clean temporary build and cache files
clean:
	python -c "import shutil, pathlib; [shutil.rmtree(p, ignore_errors=True) for p in pathlib.Path('.').rglob('__pycache__')]; [shutil.rmtree(p, ignore_errors=True) for p in pathlib.Path('.').rglob('.pytest_cache')]"

help:
	@echo "Available targets:"
	@echo "  load       : Execute ETL pipeline to load 12 source files into nifty100.db"
	@echo "  ratios     : Compute financial ratios and KPIs"
	@echo "  test       : Run all pytest unit and integration tests"
	@echo "  report     : Generate data quality and platform reports"
	@echo "  dashboard  : Launch the Streamlit dashboard"
	@echo "  api        : Start the FastAPI application server"
	@echo "  clean      : Remove temporary and cache artifacts"
