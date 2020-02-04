all:
	gcc -fprofile-arcs -ftest-coverage main.cpp -o testcase

run: txt xml html sonarqube json

txt:
	# pass

xml:
	# pass

html:
	./testcase
	$(GCOVR) -d --html-details -o coverage.html

sonarqube:
	# pass

json:
	# pass

clean:
	rm -f testcase
	rm -f *.gc*
	rm -f coverage.txt coverage.xml coverage*.html sonarqube.xml
