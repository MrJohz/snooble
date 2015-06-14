all:
	@echo "test         - run test commands"
	@echo "clean        - get rid of spare files"

test:
	py.test tests snooble

clean:
	rm .coverage

.PHONY: test clean
