##
## EPITECH PROJECT, 2024
## imageCompressor
## File description:
## Makefile
##

BINARY_PATH 	:=	$(shell stack path --local-install-root)
NAME 			= 	imageCompressor

all:
	stack build --ghc-options=-O2
	cp $(BINARY_PATH)/bin/$(NAME)-exe ./$(NAME)

clean:
	stack clean

fclean: clean
	rm -f $(NAME)

re: fclean all

tests: all
	cd AUX/benchmark && python3 bench.py -C conf.toml
	cd ../..

testsRe: fclean tests

.PHONY: all clean fclean re tests testsRe