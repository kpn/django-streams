# This Makefile requires the following commands to be available:
# * python3.11
# * docker
# * poetry (installation guide: https://python-poetry.org/docs/#installing-with-the-official-installer)

# Kafka related
service=kafka
partitions=1
replication-factor=1
tests=src/tests

.PHONY: migrations
migrations:
	@poetry run python manage.py makemigrations
	@echo 'Done!'

.PHONY: migrate
migrate:
	@poetry run python manage.py migrate --noinput
	@echo 'Done!'

REVISION:
	echo "$$(git branch | grep '*' | cut -d ' ' -f 2) $$(git describe --tags --always)" > REVISION
.PHONY: collectstatic
collectstatic:
	@poetry run python manage.py collectstatic --noinput

restart:
	docker-compose restart ${service}

# Removes old containers, free's up some space
remove-containers:
	# Try this if this fails: docker rm -f $(docker ps -a -q)
	docker-compose rm --force -v

###################
# Run application #
###################
devserver:
	@poetry run python manage.py runserver 0.0.0.0:8000

#####################
# Streaming Related #
#####################
.PHONY: worker
worker:
	@poetry run python manage.py worker
	@echo 'Done!'

kafka-cluster:
	docker-compose up

stop-kafka-cluster:
	docker-compose stop
	@$(MAKE) remove-containers

.PHONY: create-topic
create-topic:
	docker-compose exec kafka kafka-topics --create --bootstrap-server localhost:9092 --replication-factor ${replication-factor} --partitions ${partitions} --topic ${topic-name}

.PHONY: delete-topic
delete-topic:
	docker-compose exec kafka kafka-topics --delete --bootstrap-server localhost:9092 --topic ${topic-name}

.PHONY: list-topics
list-topics:
	docker-compose exec kafka kafka-topics --list --bootstrap-server localhost:9092

.PHONY: send-event
send-event:
	docker-compose exec kafka kafka-console-producer --broker-list kafka:9092 --topic $(topic-name) $(event)

.PHONY: consume-topic
consume-topic:
	docker-compose exec kafka kafka-console-consumer --bootstrap-server kafka:9092 --topic $(topic-name)

.PHONY: dev-topics
dev-topics:
	@$(MAKE) create-topic replication-factor=1 partitions=1 topic-name="django-streams--hello-kpn"
	@$(MAKE) create-topic replication-factor=1 partitions=1 topic-name="django-streams--hello-kpn-enriched"

.PHONY: delete-topics
delete-dev-topics:
	@$(MAKE) delete-topic topic-name="django-streams--hello-kpn"
	@$(MAKE) delete-topic topic-name="django-streams--hello-kpn-enriched"
