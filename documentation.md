# Documentation File
The goal of this file is to provide a higher level overview of how this script works to help identify issues, improvements, as well as future maintainability.
## At a Glance
There are two primary methods that this script runs through: The CLI version and the GUI version. The CLI version is more or less function complete in how I intend for it to function and operate, though it still has some rough edges, especially in a user interaction factor. The GUI version is what will continue to receive updates and more improvements over time. These two versions can be toggled between in the `config.ini` file.

## Overall Flow
There are four primary functions this whole script sets out to do and maintain as of writing this. These four things are:
1. Creating an Excel sheet from data from a couple of different sources, being the bookstore list for the books, Alma Open Access Analytics, Outlook for emails to help contact professors, and CORE enrollment reports to aid in decision making
2. Creating and formatting emails to compile into an Excel sheet to be fed into PowerAutomate, as well as updating the main Excel sheet with what emails have already been created
3. Updating cached/previously collected information that is stored in CSV files in a modular way to keep time and attention required as low as possible
4. Updating the main Excel sheet with newly scraped data in the case that there is previously missing data that was added to any of the sources

Points 3 and 4 mainly touch on helping facilitate data collection and updating at later points and as such are not the most intensive or directly important parts of the script. On top of all this, this script has two primary modes with some functions being strictly for one or the other, while others simply have a toggle or require no user input / interaction. These two modes are the CLI and GUI mode, but as of now, the GUI option and implementations are the standard. On top of this, `utilties.py` are helper functions used across the whole project.

### Creating an Excel Sheet
To understand the overall process for creating an Excel sheet, it would be best to look inside `sheetmaker.py` as that is the core of that function in how it interacts with everything else. In short, we start with books from the bookstore that was scraped using the `bookstore.py` functions. This gets saved for later to speed up processing time as `bookstore.csv`. These books are processed via `classes.py`, broken down for their components and their ISBN is searched against a couple of different facets in `analytics.py` to pull all the relevant data for them, publication year, access type, internal identification numbers, etc. These bookstore entries also come with names of instructors alongside class codes, this information is passed onto `grabber.py` to pull the instructor email, which is saved to `emails.csv` once pulled. After all this data is processed, everything from `analytics.csv`, `emails.csv`, and `enrollment.csv` is compiled into the output Excel sheet. The `enrollment.csv` data is read via the `enrollment.py` script. Header names are taken from `headers.ini`

### Email Formatting
As far as email formatting, it reads directly from the output Excel sheet from the prior step, or at least a sheet that uses matches formatting. It takes in information such as the instructor name, email, course information with section numbers, as well as the basic book information to format links. All of this is conducted within `emails.py`. It then updates the main Excel sheet with which emails have been formatted and presumably sent. Some of the language is taken from the `emails.ini` file.

### Updating CSV Files
Updating is done via the `modes.py` script to make function calls to the other parts of the project as they need to. These functions all export to their respective csv files as well.

### Updating the Main Excel Sheet
Updates the main excel sheet using the csv file information if new data gets scraped, also managed through `modes.py`.

## main.py
This file serves as the starting point for the whole script. If the GUI mode is activated, it will start the GUI from `gui.py`, otherwise, it will take an input from the user and pass it over to `sheetmaker.py` if you're making a new sheet or to `modes.py` if you're using the other features.

## analytics.py
Anything related to handling data from Alma gets handled through this script. Between setting up the browser, parsing the HTML, and handling inputs for things such as the SQL.
### get_columns
This function is where all the information related to generating SQL templates is stored. I found it much easier to track things in lists of dictionaries, with each dictionary containing a "Key" value for the section of the database it is searching, as well as "Cols" or columns which stores a list of the values that are listed under the associated "Key" value. Giving this function different values while calling returns different templates for different purposes. Due to how some listings do not appear while some columns are present, some of these are broken up into really small pieces.
### get_col_len
Returns the total number of columns within the SQL template. This helps with tracking how many columns need to be searched across while reading the tables within Alma analytics.
### get_table
Handles reading and parsing out the table information from the Alma screen.
### pull_one_search
Takes a list of MMS IDs and returns a list of the same size of `True` or `False`. False indicates that NO OneSearch listings appeared under the MMS ID search, while True indicates that something did return. This aids in finding out which MMS IDs and listings are still in circulation.
### pull_data
Given some data, this function automates creating a SQL statement and pulling data from the database.
### input_sql
Automates opening the SQL input window in Alma and inputting the given text.
### check_element
Aids in automating checking whether a given HTML element is present on the page, to know when it is okay to move to the next step.
### click_element
A template for telling the web driver what to click given some details about the specific HTML element.
### process_new_isbn
UNFINISHED and UNUSED; This function would ideally be used to find what ISBNs we do own for particular books from the bookstore, where a different ISBN is provided.
### process_analytics
Function that interacts with the other scripts to aid in pulling the analytics data given the web driver. Contains all the logic for how to process each set of information.
### setup_analytics
Creates and sets up the web browser to be prepared for automation tasks.
### setup_sql
Given a set of keys and columns to read, creates a complete SQL statement to use.
### export_analytics
Exports the data to a given csv file path.
### import_analytics
Imports the data from the given csv file path.

## bookstore.py
Most of this code is pulled from the original bookstore data puller that was made to automate getting bookstore data. It will have the user pass a CAPTCHA and then have them select data to pull from to get the specific term of textbook data they are interested in.
### str_clean
Removes certain special characters and whitespace from strings, aids in standardizing book titles.
### get_page_soup
Uses the BS4 library to grab a given URL, take the HTML contents and turn it into a workable form of data.
### get_link
Helper function to reduce number of replace statements later, simply helps create a link to use for price comparisons.
### get_prices
UNFINISHED and UNUSED; If there were to be a cost analysis function, this is what it would be, but the volume of books makes it a little too difficult to query this webserver as much as we would like to so it remains commented out.
### pull_textbook_data
The master information pulling function for the bookstore data.
### pull_info
Imports data from the bookstore csv file, mainly used by other parts of the program.

## classes.py
Stores the frameworks and methods for interacting with storing and processing book related data.
### Book (Class)
- **Constructor**

Creating an object requires a dictionary of a couple different values: Related course, section, instructor name and email, enrollment information, the ISBN, book title, author, edition, publisher, requirements state, requisition date, the bookstore comment, and the Alma Analytics data for the given book. The constructor will parse out the information to make it more easily accessible for processing later.
- **add_course**

When another entry for a book is found that already exists as an object, the new course information gets added via this function.
- **add_section**

Similar to the course entry, but instead adding a section to an existing course within an existing book.
- **add_isbn**

Adding ISBN values for different variants of the same book.
- **add_enroll**

Putting in additional enrollment information into the book to track all the campuses and possible enrollment values.
- **add_required**

If at any point a bookstore listing has the book as "Required", it sets the book to that status using this function.
### get_max_index
Finds the index of the course with the most sections within it in order to aid in reducing column count, as well as ensuring the largest courses are always first (leftmost).
### get_max_courses
Gets the total number of course sections to have (the number of courses the book with the most courses has).
### get_max_sections_list
Finds the number of sections needed for each course section. As an example, if we have two books, one book has 3 course with 10, 5, and 3 sections respectively ([10, 5, 3]), the other has 2 courses, one with 7 sections, the other with 6 sections ([7, 6]), then this function finds we need Course 1 to have 10 section slots, Course 2 to have 6, and Course 3 to have 3.
### process_book
Takes the preset information about a book and checks against all books so far to ensure that it does not already exist, otherwise it adds it to the master list.
### process_courses
Uses the prior get_max_courses function in order to create the headers and add them to the dataframe.
### process_sections
Uses the prior get_max_sections_list function in order to create the individual section headers and adds them to the dataframe.
### process_isbns
This function both finds the max number of ISBN columns required and puts the necessary columns into the dataframe.
### import_data
Imports all the data from the master book object list and imports it into the dataframe once it is ready to go.

## emails.py
Handles compiling and creating Excel sheets for PowerAutomate emails.
### Book (Class)
This class is a very tiny version of the other class that just takes in some basic information for the purposes of emails.
- **Constructor**

Takes the title, author, edition, year published, and access information.
### Instructor (Class)
- **Constructor**

Takes in the instructor name, email, as well as course, section, and book information per section.
- **add_book**

Adds books to a given course section for each professor.
### update_excel
Updates the main sheet with marking off what emails have been successfully created.
### create_email_excel
Processes all the Instructor data to create the table to be used to write it into an Excel sheet.
### write_to_excel
Writes the email data to an Excel sheet to be used with PowerAutomate.

## enrollment.py
Handles pulling the relevant data from the enrollment csv file in order to get the maximum enrollment values.
### get_enrollment_data
Processes the format of the given CORE report enrollment file, returning campus and enrollment information.

## grabber.py
Deals with setting up and handling pulling data from the Outlook browser to get emails for individual professors.
### process_name
Handles iterating through the names that are shown and put into the Outlook window to grab emails.
### process_suggestion
Helps with grabbing the information from the top of the suggestion box.
### get_email
Grabs the first email from the suggestion box.
### setup_grabber
Starts up and initializes the browser to work with to pull data from Outlook.
### grabber_gui
GUI variation of the implementation across this file. Functions are created in different versions and variants to utilize smaller GUI windows and threading to ensure no issues occur.
- **set_email_store**

Setter function to aid in providing button functionality to the helper GUI.
- **run_process_suggestion**

Smaller form process_suggestion function to pull the raw HTML from the page to find the suggestion box.
- **run_check_ui**

Creates a smaller GUI window to provide instructions on setting up the web window.
- **run_check_web**

Checks if the user has created the email composition window.
- **run_suggestion_ui**

Provides the user with options to select from that were in the suggestion box.
- **run_get_email**

Processes the suggestion box into names and emails.
### email_importer
Imports prior email information into a dictionary.
### email_exporter
Exports email information into a csv file with name email pairs.

## gui.py
This hosts all of the primary interactive GUI for the user.
### GUI (Class)
- **Constructor**

This constructor takes in a TKinter root GUI window. Sets up the various facets of the window, including names and sizing.
- **reset_main**

Resets the main window to a blank screen. Best used before adding elements.
- **build_main**

Constructs the main screen with all the relevant buttons and functions.
- **build_emails**

Creates the email window to modify the language used in the automated script.
- **build_headers**

Creates the header window to change the names of the headers.
- **build_advanced**

Creates the advanced options window.
- **build_sheet_outlook**

Subscreen for asking the user if they would like to open Outlook prior to creating an Excel sheet.
- **build_sheet_alma**

Subscreen for asking the user if they would like to open Alma prior to creating an Excel sheet.
- **build_sheet_final**

Final function to run to initialize creating an Excel sheet from scratch and resetting the main screen.
- **build_import_csv**

Subscreen to ask if the user wants to import prior csv information for any updating service through the script.
- **start_analytics_csv**

Function to start pulling data from Alma.
- **start_bookstore_csv**

Function to start pulling data from the bookstore.
- **start_grabber_csv**

Function to start pulling data from Outlook for the emails.
- **start_mode**

Handles the main window inputs.
- **write_cfg**

Writes information back to the main configuration file.
- **write_headers**

Writes the information from the header tab back into `headers.ini`.
- **write_emails**

Writes the template information to the `emails.ini` config file.
### start_app
Starts the main GUI application.

## helpergui.py
This is a much slimmer and simpler version of the main GUI class, to be something much more modular and additive.
### AddedGUI (Class)
- **Constructor**

Takes a title for the window, otherwise just sets the base components.
- **reset**

Resets the window information.
- **add_label**

Adds a text label to the window.
- **add_button**

Adds a button to the window with a passable command.

## modes.py
Aids in handling the various functions of the script, modularizing individual pieces into useful functions.
### start_mode
Takes a flag from the CLI main file on which mode to start.
### csv_mode
Submenu to select which csv file to update.
### email_mode
Starts the email creation portion of the script.
### update_mode
Submenu to select which information to update the Excel sheet with.
### emails_csv
Opens Outlook to update the emails csv file.
### analytics_csv
Updates the analytics csv file.
### enrollment_update
Updates missing or empty enrollment information on the Excel sheet.
### analytics_update
Updates empty portions within the analytics portion of the Excel sheet.
### emails_update
Updates the email columns on the Excel sheet.
### get_import
Asks the user if they would like to import prior csv information.

## output.py
This script has a single function: outputting an Excel sheet! This is where formatting and such gets handled (i.e. color, column sizing, etc.)
### write_to_sheet
Handles all the formatting and information regarding how colors and columns get processed.

## sheetmaker.py
Performs all of the functions related to creating new sheets from scratch.
### make_excel_sheet
Works with other portions of the script to update, finalize, and format an Excel sheet to completion.

## utilties.py
This script hosts helpful functions that might be purposeful in multiple places around the various helper and main scripts. On top of this, it also helps to host hard coded data that is not necessary to keep in a configuration file (such as header values!). The organization is to help cut down on lines of code in other places, as well as keep information consistency so updating one variable does update it in all relevant places when needed.
### get_int
Takes a value, gets an integer out of it if it can, otherwise returns None.
### get_clean
Removes preset phrases and terms from the names of books and authors to reduce the number of duplicate listings.
### get_state
Takes strings of "True" or "False" and converts them to bool values.
### get_directory
Takes a string and the config file to pull it from to get a directory.
### get_filepath
Given a direct file path, it will grab the direct path to the file given.
### get_letter
Utilized to convert number of columns into the letter code.
### get_edition_string
Converts a number to have the "st", "nd", "rd", and "th" at the end.
### get_format_headers
Gets the headers and information for the columns with course, section, and instructor infromation.
### get_replace_header
Takes the format headers and automatically replaces the information out from them given the course number, section number, and the added information at the end.
### get_split_course
Splits course codes into individual components of subject and number.
### get_input
Gets an input between a set number range with a text to display to the user.
### get_enabled
Asks the user "y/n" for True or False.
### get_sheet_headers
Returns the headers for the columns that are stored in the config file.
### get_config_headers
Returns the config file read directly from the configuration parser.
### get_string_cleaners
Gets the list of things to parse out of the titles from the bookstore to clean them and consolidate titles and authors.
### get_row_info
Given a row from the dataframe and a key to access it, it error checks against blank information and reads it.
### get_campus
Gets the full campus name given the letter code for the individual campus.
### set_col_format
Sets the formatting to a uniform format for the Excel sheet.

## CSV Storage
In order to store all the data in a way that is accessible, quick, and aids in subsequent run times, all pulled data is compiled into `.csv` files, each with their own format. This makes it so we don't have to re-run the bookstore scraper, email grabber, or analytics scraper again every single time we wish to do something.
### analytics.csv
After parsing all the data from Alma, it is stored in this csv file to be used later.

Data is formatted as following:
ISBN, {'MMS Id': {'Types': [str], 'Copies': [int], 'Users': [int], 'CDL': [bool], 'Link': str}, ... }
### bookstore.csv
This data is all the raw information taken from the bookstore page, stored to be used later.

Data is formatted as following:
Term, Course Subject, Course Number, Section Number, Instructor, Title, Edition, Author, ISBN, Publisher, Requirement, SKU, Comments, Requisition Date
### emails.csv
Each time an instructor name is paired to an email, it is saved to this file to be used later.

Data is formatted as following:
Instructor Name, Email
### enrollment.csv
This is just a CORE report exported as a csv for all courses in the desired term. This must be done outside of the script itself.

## Config Files
### config.ini
Primary settings for the script, though some of these are redundant / only used by one half of the script.
### emails.ini
Holds all the template lines for emailing professors.
### headers.ini
Holds all the names of the headers as well as their relation to the internal variable name.