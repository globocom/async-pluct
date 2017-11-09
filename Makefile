BUMP := 'patch'

clean:
	@find . -iname "*.pyc" -delete

deps:
	@pip install -r requirements_test.txt

setup: deps

test: clean
	@flake8 async_pluct/
	@nosetests --with-coverage --cover-package=async_pluct --cover-branches --cover-erase

patch:
	@$(eval BUMP := 'patch')

minor:
	@$(eval BUMP := 'minor')

major:
	@$(eval BUMP := 'major')

bump:
	@bumpversion ${BUMP}

release:
	@python setup.py -q sdist upload -r globo
	@git push
	@git push --tags

