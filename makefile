.PHONY: help install build test clean run chat

help:
	@echo "Available commands:"
	@echo "  make install  - Install dependencies"
	@echo "  make build    - Build the project"
	@echo "  make test     - Run tests"
	@echo "  make clean    - Clean build artifacts"
	@echo "  make run      - Run one-shot health check"
	@echo "  make chat     - Interactive chat with the agent"

pre-requisites:
	curl -LsSf https://astral.sh/uv/install.sh | sh

install:
	uv sync

run:
	uv run python3 main.py

chat:
	uv run python3 main.py --chat
