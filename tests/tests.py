# test 0x01 : parse [oshi no ko] title from shonenjumpplus website
# parser work with free chapters only [if you want parse all than 
# 	you need share your cookie with authorization token where all 
# 	chapters are avalible :D]

from shonenjumpparser import shonenjump_parser

def oshinoko():
	shonenjump_parser("https://shonenjumpplus.com/episode/13933686331661632099", "/Users/humac/Downloads", "oshinoko")
	print("Parsing is over")


# "https://shonenjumpplus.com/episode/13933686331661632099" [4856001361175439438]