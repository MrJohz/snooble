all:
	@echo "test         - run test commands"
	@echo "clean        - get rid of spare files"

test:
	py.test snooble tests

test-cruel:
	py.test --pep8 --flakes snooble tests

clean:
	rm .coverage

.PHONY: test clean
