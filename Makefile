
.PHONY: release
release: test doc-check
	bumpversion --verbose $${PART:-patch}
	git push
	git push --tags


.PHONY: doc-check
doc-check:
	./setup.py checkdocs


.PHONY: test
test:
	tox
