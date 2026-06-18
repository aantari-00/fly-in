ADD = git add .
COMMIT = git commit -m "fly_in"
PUSH = git push

all:
	@$(ADD)
	@$(COMMIT)
	@$(PUSH)
