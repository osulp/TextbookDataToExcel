# Master Textbook PrePurchasing Excel Script
Hello! This script aims to consolidate many projects that have been spun up to reduce amounts of manual data entry hours in regards to textbook data management as well as prepurchasing workflows. The hope is that this will remain functional, updateable / modifiable, as well as compatible with prior implementations of workflows.

The guide about how to use and setup this script will focus on the GUI portion of the implementations. There is a CLI version available, but it will not be updated and maintained as closely.

As a forewarning, this is a very large script, split across several files to help with data flow and readability.

## Getting Started
This script requires having Google Chrome and Python installed.

To download the script, navigate to the [Latest Release](releases/latest). Download the ZIP file.

Setting up the script is fairly easy, but it requires some data to be loaded beforehand. A CORE report of the desired term must be exported into a csv file and placed within `helpers/csv/` as `enrollment.csv`. This directory and file name requirement can be changed in `config.ini`, but is not required whatsoever.

To finish setup, run `install.bat` or install the listed Python packages under `helpers/requirements.txt`.

## Main Menu
From the main menu of the script, there are four primary options to engage with.

1. New Sheet
2. Gather Data
3. Create Emails
4. Sheet Update

It is recommended that the user performs `Gather Data` -> `Bookstore Data` prior to starting other actions, presuming the `bookstore.csv` file is not already populated.

### Create Sheet
This will take the user through a set of options of whether to gather information from Outlook and Alma Analytics. These are not required, but there will be large amounts of missing information if `emails.csv` and `analytics.csv` are not populated prior.

After the script is done processing through the set of books from `bookstore.csv`, it will output `output.xlsx` into the main folder.

### Gather Data
This option provides three further options to the user.

1. Email Data
2. Bookstore Data
3. Analytics Data

With email and analytics data, they will update their respective csv file after each piece of information is pulled, making it safe to close out while in the middle of using it if they are only able to be performed in bits at a time. Just ensure that the user presses `Yes` to importing prior information.

Generally, the workflow of this section would be `Bookstore Data` first to gather relevant books, then `Email Data` to ensure that all the professor emails are on hand, followed by `Analytics Data` to let it run in the background and gather the necessary license, MMS ID, etc. information. Once all three of these have been run for a term, a full sheet can be created from the Main Menu.

### Create Emails
After an Excel sheet has been properly processed, assessed, and reviewed, this section aims to make it easy to create and update emails. Place your Excel file in the home directory of the script (next to `run.bat`). Put the name into the first textbox, as well as the worksheet name in the lower box. 

Press `Export Sheet` and it will output an `email_output.xlsx` file to be used with PowerAutomate. Additionally, the sheet that was used as input will be updated to now have dates listed on emails that were created with the specific batch.

If some emails are made erroneously, simply scan through the Excel sheet and remove the dates on the respective rows for `Date Emailed`. 

### Sheet Update
This option provides three further options to the user.

1. Update Emails
2. Update Analytics
3. Update Enrollment

Sometimes a workable Excel sheet needs to be made before all the data is present. In this case, it can be tough to update information after the fact, to help with this, similar to how it reads the input sheet for creating emails, it will read the sheet and combine it with any case of missing information from `emails.csv`, `analytics.csv`, and `enrollment.csv`.

## Email Text
If the text contained within the emails that get sent out to professors needs to be updated, this is where those pieces can be updated at. It can also be modified directly with the `emails.ini` file within `helpers/ini`.

## Header Names
If at any point it is of interest to change what the actual header names are inside the main Excel sheet, this is the easiest way of updating them. Modify the corresponding name and click `Save to File`.

## Adv. Options
This is just a GUI version of interacting with and modifying `config.ini`. A lot of these are leftover development options. The `documentation.md` file will have an explanation of what each value and setting does, but it is not important or entirely relevant to using the script, just can make it a little less painful when setup correctly for each use case.
