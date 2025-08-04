NS = local
VERSION ?= latest

#change this from docker to podman depending on your use case
CONTAINER_ENGINE=docker

VOLUMES = \
 -v $(PWD):/app

REPO = wrangler-demo
NAME = wrangler-demo

INSTANCE = default

ENV = \
	-e AWS_DEFAULT_REGION=ap-northeast-1 \


VOLUMES= \
  -v $(HOME)/.aws:/root/.aws:ro \
  -v $(PWD):/app:ro



.PHONY: build shell rm


build:
	$(CONTAINER_ENGINE) build --no-cache -t $(NS)/$(REPO):$(VERSION) ./demos

shell: build
	source .env
	$(CONTAINER_ENGINE) run --rm --name $(NAME)-$(INSTANCE) -i -t $(PORTS) $(VOLUMES) $(ENV) $(NS)/$(REPO):$(VERSION) /bin/bash

inspect: build
	$(CONTAINER_ENGINE) run --rm --name $(NAME)-$(INSTANCE) -i -t $(PORTS) $(ENV) $(NS)/$(REPO):$(VERSION) /bin/bash

rm:
	$(CONTAINER_ENGINE) rm $(NAME)-$(INSTANCE)