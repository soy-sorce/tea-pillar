SHELL := /usr/bin/env bash

.PHONY: model-check model-build-push model-deploy model-deploy-all

model-check:
	cd model && ruff check src && mypy src

model-build-push:
	bash scripts/deploy_ML/build_and_push_model.sh $(ARGS)

model-deploy:
	bash scripts/deploy_ML/deploy_vertex_model.sh $(ARGS)

model-deploy-all:
	bash scripts/deploy_ML/deploy_model_to_vertex.sh $(ARGS)
