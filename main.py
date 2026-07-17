import sys
import configparser
from helpers.utilities import get_input, get_state
from helpers.modes import start_mode
from helpers.gui import start_app
from helpers.sheetmaker import make_excel_sheet

# TODO
# This is a list of improvements that I am aware may be able to be added
# However, due to time constraints or lack of information are left for later

# - try / except blocks around data entry code
#     things like analytics.py could use more error checking to prevent
#     runtime errors to prevent loss of data and time

# - refactoring / reduction in overhead code times
#     there is unoptimized solutions and code purely for the case of
#     making this project functional by the necessary date
#     example of this is exporting after each round of analytics pulling

# - adding in better modularity + options
#     there are not many print debug statements, nor direct debugging
#     in general; not that this is necessary, but it is nice
#     other options could include allowing ISBN-less bookstore listings
#     to be recorded, but lots of the options are kinda left as is

# - resolving leftover TODO statements in the various scripts
#     not all of these are serious needs, requirements, or fixes
#     as much as they are probably spots i have left notes of
#     what COULD be done or what hasn't been fully tested

# - adding testcases for selenium functions using hidden github values
#     could still login using headless functionality and secret key values

# - adding in cost comparison that works without querying the site too many times

# - improving documentation, comments, and overall code structure

# - cross referencing our own ISBN values from the bookstore ISBN values
#     sometimes we own a different book than what the bookstore has per class
#     but it is the same book, in which case this could use an automatic cross
#     referencing function to automatically pull those values via titles

config = configparser.ConfigParser()
config.read("config.ini")
main_cfg = config["Main"]
use_gui = get_state(main_cfg["gui"])

if use_gui:
    start_app()
else:
    print("Select mode:")
    input_text = """1. Create new Excel sheet (From Scratch w/ Cache)
    2. Update .csv files (Updating Script Cache)
    3. Create email Excel sheet (PowerAutomate)
    4. Update Excel sheet (Updating Sheet w/ Cache)
    Input: """
    mode_input = get_input(min=1, max=4, text=input_text)

    if mode_input != 1:
        start_mode(mode_input)
        sys.exit(1)  # quit out after alt use

    make_excel_sheet()
