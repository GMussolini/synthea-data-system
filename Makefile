.PHONY: help build up down restart logs test clean seed

# Variables
DOCKER_COMPOSE = docker-compose
PYTHON = python3
PIP = pip3

# Colors for output
RED = \033[0;31m
GREEN = \033[0;32m
YELLOW = \033[1;33m
NC = \033[0m # No Color

help: ## Show this help message
	@echo "$(GREEN)Patient Management System - Available Commands$(NC)"
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "$(YELLOW)%-15s$(NC) %s\n", $$1, $$2}'

install: ## Install dependencies locally
	@echo "$(GREEN)Installing Python dependencies...$(NC)"
	$(PIP) install -r requirements.txt
	@echo "$(GREEN)Dependencies installed!$(NC)"

build: ## Build Docker images
	@echo "$(GREEN)Building Docker images...$(NC)"
	$(DOCKER_COMPOSE) build
	@echo "$(GREEN)Build complete!$(NC)"

up: ## Start all services
	@echo "$(GREEN)Starting services...$(NC)"
	$(DOCKER_COMPOSE) up -d
	@echo "$(GREEN)Services started!$(NC)"
	@echo "$(YELLOW)Waiting for services to be ready...$(NC)"
	@sleep 10
	@echo "$(GREEN)Services are ready!$(NC)"
	@echo ""
	@echo "$(GREEN)Access points:$(NC)"
	@echo "  API Gateway:     http://localhost:8000"
	@echo "  Auth Service:    http://localhost:8001"
	@echo "  Patient Service: http://localhost:8002"
	@echo "  Search Service:  http://localhost:8003"
	@echo "  API Docs:        http://localhost:8000/docs"

down: ## Stop all services
	@echo "$(RED)Stopping services...$(NC)"
	$(DOCKER_COMPOSE) down
	@echo "$(GREEN)Services stopped!$(NC)"

restart: ## Restart all services
	@echo "$(YELLOW)Restarting services...$(NC)"
	@make down
	@make up

logs: ## Show logs from all services
	$(DOCKER_COMPOSE) logs -f

logs-auth: ## Show logs from auth service
	$(DOCKER_COMPOSE) logs -f auth-service

logs-patient: ## Show logs from patient service
	$(DOCKER_COMPOSE) logs -f patient-service

logs-search: ## Show logs from search service
	$(DOCKER_COMPOSE) logs -f search-service

test: ## Run all tests
	@echo "$(GREEN)Running tests...$(NC)"
	$(DOCKER_COMPOSE) exec patient-service pytest -v
	@echo "$(GREEN)Tests complete!$(NC)"

test-unit: ## Run unit tests only
	@echo "$(GREEN)Running unit tests...$(NC)"
	$(DOCKER_COMPOSE) exec patient-service pytest tests/unit -v

test-integration: ## Run integration tests only
	@echo "$(GREEN)Running integration tests...$(NC)"
	$(DOCKER_COMPOSE) exec patient-service pytest tests/integration -v

test-coverage: ## Run tests with coverage report
	@echo "$(GREEN)Running tests with coverage...$(NC)"
	$(DOCKER_COMPOSE) exec patient-service pytest --cov=. --cov-report=html --cov-report=term
	@echo "$(GREEN)Coverage report generated in htmlcov/$(NC)"

seed: ## Seed database with sample data
	@echo "$(GREEN)Seeding database with sample data...$(NC)"
	$(DOCKER_COMPOSE) exec patient-service python scripts/seed_data.py --all
	@echo "$(GREEN)Database seeded!$(NC)"

seed-users: ## Create test users only
	@echo "$(GREEN)Creating test users...$(NC)"
	$(DOCKER_COMPOSE) exec patient-service python scripts/seed_data.py --users
	@echo "$(GREEN)Test users created!$(NC)"

seed-patients: ## Create sample patients only
	@echo "$(GREEN)Creating sample patients...$(NC)"
	$(DOCKER_COMPOSE) exec patient-service python scripts/seed_data.py --patients 50
	@echo "$(GREEN)Sample patients created!$(NC)"

clean: ## Clean up containers, volumes, and cache
	@echo "$(RED)Cleaning up...$(NC)"
	$(DOCKER_COMPOSE) down -v
	@find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	@find . -type f -name "*.pyc" -delete 2>/dev/null || true
	@find . -type f -name ".coverage" -delete 2>/dev/null || true
	@rm -rf htmlcov/ 2>/dev/null || true
	@rm -rf .pytest_cache/ 2>/dev/null || true
	@echo "$(GREEN)Cleanup complete!$(NC)"

db-migrate: ## Run database migrations
	@echo "$(GREEN)Running database migrations...$(NC)"
	$(DOCKER_COMPOSE) exec patient-service alembic upgrade head
	@echo "$(GREEN)Migrations complete!$(NC)"

db-reset: ## Reset database (WARNING: destroys all data)
	@echo "$(RED)WARNING: This will destroy all data!$(NC)"
	@echo "Press Ctrl+C to cancel, or wait 5 seconds to continue..."
	@sleep 5
	$(DOCKER_COMPOSE) exec postgres psql -U postgres -c "DROP DATABASE IF EXISTS patient_db;"
	$(DOCKER_COMPOSE) exec postgres psql -U postgres -c "CREATE DATABASE patient_db;"
	@make db-migrate
	@echo "$(GREEN)Database reset complete!$(NC)"

format: ## Format code with black
	@echo "$(GREEN)Formatting code...$(NC)"
	black auth-service/ patient-service/ search-service/ tests/
	@echo "$(GREEN)Code formatted!$(NC)"

lint: ## Run linting checks
	@echo "$(GREEN)Running linting checks...$(NC)"
	flake8 auth-service/ patient-service/ search-service/ tests/ --max-line-length=120
	@echo "$(GREEN)Linting complete!$(NC)"

check: ## Run format and lint checks
	@make format
	@make lint

shell-auth: ## Open shell in auth service container
	$(DOCKER_COMPOSE) exec auth-service /bin/bash

shell-patient: ## Open shell in patient service container
	$(DOCKER_COMPOSE) exec patient-service /bin/bash

shell-search: ## Open shell in search service container
	$(DOCKER_COMPOSE) exec search-service /bin/bash

shell-db: ## Open PostgreSQL shell
	$(DOCKER_COMPOSE) exec postgres psql -U postgres -d patient_db

status: ## Show status of all services
	@echo "$(GREEN)Service Status:$(NC)"
	@$(DOCKER_COMPOSE) ps

quick-start: ## Quick start: build, start, and seed
	@make build
	@make up
	@sleep 5
	@make seed
	@echo ""
	@echo "$(GREEN)🚀 System is ready!$(NC)"
	@echo ""
	@echo "$(YELLOW)Test credentials:$(NC)"
	@echo "  Admin:  username=admin, password=admin123"
	@echo "  User:   username=user, password=user123"
	@echo "  Doctor: username=doctor, password=doctor123"
	@echo ""
	@echo "$(YELLOW)API Documentation:$(NC) http://localhost:8000/docs"

dev: ## Start development environment
	@make quick-start
	@make logs