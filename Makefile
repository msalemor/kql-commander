default:
	@echo "Nada"

clean:
	cp static/index.html .
	rm -rf static
	mkdir static
	cp index.html static/.
	rm index.html