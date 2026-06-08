UV := uv run python

.PHONY: all pipeline setup download preprocess cluster classify \
        dashboard train figures report pdf clean help

all: help

setup:
	$(UV) src/00_setup.py

download:
	$(UV) src/01_download.py

preprocess:
	$(UV) src/02_preprocess.py

cluster:
	$(UV) src/03_clustering.py

classify:
	$(UV) src/04_classification.py

figures:
	$(UV) src/07_report_figures.py

pdf:
	typst compile --root . report/ieee_report.typ report/ieee_report.pdf

pipeline:
	$(UV) src/02_preprocess.py
	$(UV) src/03_clustering.py
	$(UV) src/04_classification.py
	$(UV) src/07_report_figures.py
	typst compile --root . report/ieee_report.typ report/ieee_report.pdf

dashboard:
	$(UV) src/06_dashboard.py

train:
	@echo "──────────────────────────────────────────────────"
	@echo "  Entrenamiento requiere 3 terminales:"
	@echo "  A: cd showdown && node pokemon-showdown start --no-security"
	@echo "  B: make dashboard"
	@echo "  C: $(UV) src/05_train_agent.py"
	@echo "──────────────────────────────────────────────────"

clean:
	rm -f report/ieee_report.pdf

help:
	@echo "Targets:"
	@echo "  make pipeline   — corre pasos 02→08 + pdf completo"
	@echo "  make setup      — 00_setup: instala deps y clona Showdown"
	@echo "  make download   — 01_download: descarga gen8rb.parquet"
	@echo "  make preprocess — 02_preprocess: feature engineering"
	@echo "  make cluster    — 03_clustering: K-Means"
	@echo "  make classify   — 04_classification: XGBoost"
	@echo "  make figures    — 07_report_figures: figuras del informe"
	@echo "  make pdf        — typst: compila ieee_report.pdf"
	@echo "  make dashboard  — 06_dashboard: FastAPI puerto 9000"
	@echo "  make train      — instrucciones para entrenar agente RL"
	@echo "  make clean      — elimina ieee_report.pdf"
