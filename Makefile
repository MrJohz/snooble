all:
	@echo "test         - run test commands"
	@echo "test-cruel   - run test commands with pep8 and flakes"
	@echo "clean        - get rid of spare files"

test:
	py.test snooble tests

test-cruel:
	py.test --pep8 --flakes snooble tests

clean:
	rm .coverage

.PHONY: all test test-cruel clean
