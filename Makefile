init:
	pip install -r requirements.txt

test:
	./test_adventuregame.py

.PHONY: init test
