.PHONY: all run run-backend run-frontend

all: run

run:
	@echo Starting services...
	@start cmd /k "cd src\backend && call venv\Scripts\activate && python main.py"
	@start cmd /k "cd src\frontend && npm run dev"
	@echo Services started. Backend: http://localhost:5000, Frontend: http://localhost:5173

run-backend:
	cd src\backend && call venv\Scripts\activate && python main.py

run-frontend:
	cd src\frontend && npm run dev
