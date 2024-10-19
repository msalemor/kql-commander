.PHONY: default, clean

default:
	@echo "Nada"

clean:
	cp static/index.html .
	rm -rf static
	mkdir static
	cp index.html static/.
	rm index.html

build-ui: clean
	cd frontend && bun run build
	cp -r frontend/dist/* static