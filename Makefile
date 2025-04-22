.PHONY: install test clean
install:
	@echo "Installing backend dependencies..."
	@pip install -r ./backend/requirements.txt
	@echo "Backend dependencies installed."
	@echo "Installing frontend dependencies..."
	@cd ./frontend && npm install
	@echo "Frontend dependencies installed."

test:
	@echo "Running backend tests..."
	@cd ./backend && export PYTHONPATH=. && pytest
	@echo "Backend tests passed."

clean:
	@echo "Cleaning up..."
	@find . -name "*.pyc" -delete
	@find . -name "__pycache__" -delete
	@find . -name ".coverage" -delete
	@find . -type d -name ".pytest_cache" -exec rm -rf {} +
	@rm -rf ./backend/.coverage
	@echo "Cleanup complete."