

s: stats
stats:
	python3 temps.py stats --hours-per-day 7.4

n: n-stats
n-stats:
	python3 temps.py stats --hours-per-day 7.4 --not-today

p: parsable-stats
parsable-stats:
	python3 temps.py stats --hours-per-day 7.4 --porcelain


s-for-january:
	python3 temps.py stats -f arch/2021_01 --hours-per-day 7.4


a: arrive
arrive:
	python3 temps.py arrive

q: quit
quit:
	python3 temps.py quit

save:
	git add temps
	git commit -m "saving"

t:
	tail temps
	nvim  ~/Documents/temps/temps
