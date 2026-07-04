.PHONY: help build push deploy login clean test

# --- Configuration ----------------------------------------------------------
# Override these via environment variables or make arguments, e.g.:
#   make build IMAGE_NAME=ghcr.io/myuser/kniffel-tracker TAG=1.2.3

IMAGE_NAME ?= ghcr.io/$(GITHUB_USER)/kniffel-tracker
TAG ?= latest
FULL_IMAGE = $(IMAGE_NAME):$(TAG)

REMOTE_HOST ?= user@server.example.com
REMOTE_DIR ?= /opt/kniffel-tracker
REMOTE_COMPOSE_FILE = $(REMOTE_DIR)/docker-compose.yml

# --- Targets ----------------------------------------------------------------

help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-15s\033[0m %s\n", $$1, $$2}'

test: ## Run Django tests locally
	python manage.py test

build: ## Build the Docker image
	docker build -t $(FULL_IMAGE) .

login: ## Log in to GHCR.io locally (requires GITHUB_TOKEN in env)
	@echo "Logging in to GHCR.io as $(GITHUB_USER)..."
	@echo $(GITHUB_TOKEN) | docker login ghcr.io -u $(GITHUB_USER) --password-stdin

push: ## Push the Docker image to GHCR.io
	docker push $(FULL_IMAGE)

push-latest: ## Tag and push the image as 'latest' as well
	docker tag $(FULL_IMAGE) $(IMAGE_NAME):latest
	docker push $(IMAGE_NAME):latest

deploy: ## Deploy on remote server via SSH (pull image and restart container)
	@echo "Deploying $(FULL_IMAGE) to $(REMOTE_HOST)..."
	ssh $(REMOTE_HOST) "cd $(REMOTE_DIR) && \
		docker pull $(FULL_IMAGE) && \
		docker compose -f $(REMOTE_COMPOSE_FILE) up -d --force-recreate"

clean: ## Remove local Docker image
	docker rmi $(FULL_IMAGE) || true
