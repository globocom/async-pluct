
clean:
	@find . -iname "*.pyc" -delete

deps:
	@pip install -r requirements_test.txt

setup: deps

test: clean
	@flake8 async_pluct/
	@nosetests --with-coverage --cover-package=async_pluct --cover-branches --cover-erase

