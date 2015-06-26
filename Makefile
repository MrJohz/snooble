all:
	@echo "test               - run test commands"
	@echo "test-cruel         - run test commands with pep8 and flakes"
	@echo "clean              - get rid of spare files"
	@echo "clean-cassettes    - remove stored VCR cassettes (tests will require auth)"

test:
	py.test snooble tests

test-cruel:
	py.test --pep8 --flakes snooble tests

clean:
	rm .coverage

clean-cassettes:
	rm -rf tests/cassettes

.PHONY: all test test-cruel clean clean-cassettes
