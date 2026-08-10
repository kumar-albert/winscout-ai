.PHONY: help install build test clean run

help:
	@echo "Available commands:"
	@echo "  make install  - Install dependencies"
	@echo "  make build    - Build the project"
	@echo "  make test     - Run tests"
	@echo "  make clean    - Clean build artifacts"
	@echo "  make run      - Run the application"

pre-requisites:
	curl -LsSf https://astral.sh/uv/install.sh | sh

install:
	uv sync

run:
	uv run python3 main.py
