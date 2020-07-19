build:
	docker build -t joanfont/grissom .

push:
	docker push joanfont/grissom

mongo:
	docker-compose up -d mongo

shell:
	docker-compose run --rm --entrypoint ipython python
