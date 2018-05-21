"""Player functions, includes player progression"""


###############
# Specialties #
###############

FIGHTER = dict([
	("name", "Fighter"),
	("exp_mult", 1.0),
	("description", "The Fighter excels are armed combat and wears enemies down through a combination of ranged and melee moves")
	])

SWORDMASTER = dict([
	("name", "Swordmaster"),
	("exp_mult", 0.9),
	("description", "Using a variety of swords the swordmaster slices and dices their way to victory")
	])


class Race:

	def __init__(name):
		self.name = name
