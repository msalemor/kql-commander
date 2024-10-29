.PHONY: default, clean

default:
	@echo "Nada"

clean:
	rm -rf static
	mkdir static
	touch static/.gitkeep

build-ui: clean
	cd frontend && bun run build
	cp -r frontend/dist/* static

run-ui:
	@echo "Run UI"	
	cd frontend && bun run dev