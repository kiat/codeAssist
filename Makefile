.PHONY: install test clean
install:
	@echo "Installing backend dependencies..."
	@pip install -r ./backend/requirements.txt
	@echo "Backend dependencies installed."
	@echo "Installing frontend dependencies..."
	@cd ./frontend && npm install
	@echo "Frontend dependencies installed."

test: test-backend test-frontend  ## Run all tests

test-backend:                     ## Backend unit / integration tests
	@echo "Running backend tests..."
	@cd ./backend && PYTHONPATH=. pytest
	@echo "Backend tests passed."

test-frontend:                    ## Front-end Jest tests
	@echo "Running frontend tests..."
	@cd ./frontend && npm test --silent
	@echo "Frontend tests passed."

clean:
	@echo "Cleaning up..."
	@find . -name "*.pyc" -delete
	@find . -name "__pycache__" -delete
	@find . -name ".coverage" -delete
	@find . -type d -name ".pytest_cache" -exec rm -rf {} +
	@rm -rf ./backend/.coverage
	@echo "Cleanup complete."