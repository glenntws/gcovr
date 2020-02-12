all:
	gcc -fprofile-arcs -ftest-coverage main.cpp -o testcase

run: txt xml html sonarqube json

txt:
	# pass

xml:
	# pass

html:
	./testcase
	$(GCOVR) --decisions --html-details -o coverage.html

sonarqube:
	# pass

json:
	./testcase
	$(GCOVR) --decisions --json -o coverage.json

clean:
	rm -f testcase
	rm -f *.gc*
	rm -f coverage.txt coverage.xml coverage*.html coverage.json sonarqube.xml
