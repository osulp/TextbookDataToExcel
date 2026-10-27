from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.window import WindowTypes
import time
import bs4
import configparser
import csv
from helpers.utilities import get_state, get_directory
from helpers.helpergui import AddedGUI


def str_clean(value):
    """Removes special characters and whitespace from a string."""
    original = value
    new_str = ""
    first = True
    while new_str is not original:
        if first:
            first = False
        else:
            original = new_str
        new_str = original.strip()
        new_str = new_str.replace("&nbsp;", "")
        new_str = new_str.replace("  ", " ")
        new_str = new_str.replace("\t", "")
        new_str = new_str.replace("\n", "")
    return new_str


def get_page_soup(driver, url):
    """Pulls the current page HTML into a more workable format."""
    driver.get(url)
    html_content = driver.page_source
    page = bs4.BeautifulSoup(html_content, "lxml")
    return page


def get_link(link, term, subject, code, section):
    """Function to replace some of the template words to help with modularity."""
    link = link.replace("TERM", f"{term}")
    link = link.replace("SUBJECT", f"{subject}")
    link = link.replace("CODE", f"{code}")
    link = link.replace("SECTION", f"{section}")
    return link


# TODO
# long queries cause requests to be too large, in turn causing server overload
# probably leave this alone for now then...?
def get_prices(driver, table):
    """This would in theory grab the lowest price of a given row of bookstore information.
    For now, this will go unused as the direct access to the price comparison is
    rate limited, meaning it would not be worth doing due to time."""

    seperator = "%2C"
    id_template = "TERM__SUBJECT__CODE__SECTION"
    store_link = "https://osubeaverstore.verbacompare.com/comparison?id="

    link_list = []

    master_link = f"{store_link}"
    table_size = len(table)
    course_letter = "A"
    for idx, row in enumerate(table):
        isbn = row[8].replace("-", "").strip()
        if isbn == "" or isbn is None:
            continue

        term = row[0]
        department = row[1]
        dep_arr = department.split(":")
        subj_code = dep_arr[0].strip()
        letter = subj_code[0]
        subj_num = row[2]
        section = row[3]

        if letter != course_letter:
            link_list.append(master_link[:-3])
            master_link = f"{store_link}"
            course_letter = letter

        master_link += get_link(id_template, term, subj_code, subj_num, section)
        if idx + 1 < table_size:
            master_link += seperator

    base_window = driver.current_window_handle
    driver.switch_to.new_window(WindowTypes.TAB)
    price_table = {}

    for link in link_list:
        driver.get(link)
        while True:
            try:
                WebDriverWait(driver, 5).until(
                    EC.presence_of_element_located((By.CLASS_NAME, "css_button"))
                )
                button = driver.find_elements(By.CLASS_NAME, "css_button")
                button[0].click()
                break
            except Exception as err:
                print(err)

        material_dict = {}
        time.sleep(1)
        try:
            WebDriverWait(driver, 5).until(
                EC.presence_of_element_located((By.CLASS_NAME, "item"))
            )
            materials = driver.find_elements(By.CLASS_NAME, "item")
            # book_found = False
            main_div = None
            for material in materials:
                html = material.get_attribute("innerHTML")
                lxml = bs4.BeautifulSoup(html, "lxml")
                td_list = lxml.find_all("td")
                mat_isbn = td_list[3].get_text
                material_dict[mat_isbn] = material

            for row in table:
                isbn = row[8].replace("-", "").strip()
                if isbn not in material_dict or row[8] in price_table:
                    continue
                main_div = material_dict[isbn]
                main_div.click()
                # TODO
                # this has been partially implemented but it cannot handle the number of
                # requests this script would like to make, check other TODO or documentation
                # this needs to pull the used and new price points from the beaverstore page
                # https://osubeaverstore.verbacompare.com/comparison?id=2026-Summer__AEC__411__400
                html = main_div.get_attribute("innerHTML")
                lxml = bs4.BeautifulSoup(html, "lxml")
                price_list = lxml.find_all(class_="price")
                minimum = float("inf")
                for idx, price in enumerate(price_list):
                    price_list[idx] = price.strip().replace("$", "")
                    price_list[idx] = round(float(price_list[idx]), 2)
                    if price_list[idx] < minimum:
                        minimum = price_list[idx]

                price_table[row[8]] = f"${minimum}"

        except Exception as err:
            print(err)

    driver.close()
    driver.switch_to.window(base_window)
    return price_table


def pull_textbook_data(gui=False):
    """Pulls textbook data from the given webpage and returns
    the output table."""

    # configure this script using the .ini file
    full_config = configparser.ConfigParser()
    full_config.read("config.ini")
    config = full_config["Textbook"]
    output = get_state(config["Output"])
    # whether or not to skip lines with 'SEE CANVAS AND/OR INSTRUCTOR FOR
    # COURSE MATERIALS - NO COST' in them
    nocost_skip = get_state(config["NoCostSkip"])
    save_file = get_state(config["Save"])
    textbk_path = get_directory("Save", config)
    # custom_term = [config["CustomNum"], config["CustomName"]]

    # gets chrome tab
    driver = webdriver.Chrome()

    # the following bit automatically checks for the captcha completion by
    # determining whether or not there is a readable table in the html, in
    # which the captcha page does not
    print("Awaiting CAPTCHA completion.")

    list_link = "https://beavs.osubeaverstore.com/Textbooks.asp"
    driver.get(list_link)
    exit_check = False

    while not exit_check:
        captcha_html = driver.page_source
        captcha_page = bs4.BeautifulSoup(captcha_html, "lxml")
        if captcha_page.find_all("td"):
            exit_check = True
            print("CAPTCHA passed!")
        time.sleep(2)

    # grabs html content and gets csv fields ready
    html_content = driver.page_source
    table_export = []
    curr_page = bs4.BeautifulSoup(html_content, "lxml")
    terms = []

    # if gui true, overwrite custom config
    if gui:

        chosen_term = None

        def set_term_val(value):
            nonlocal chosen_term
            chosen_term = value

        gui_terms = []
        skip_check = 0
        for td in curr_page.find_all("td"):
            # skipping other td
            if skip_check == 0:
                skip_check = 1
                continue
            skip_check = 0
            for option in td.find_all("option"):
                # skipping non option
                if skip_check == 0:
                    skip_check = 1
                    continue
                gui_terms.append([option["value"], option.text])
            break

        gui_window = AddedGUI(title="Term Choice")
        gui_window.add_label("Which term would you like to collect data for?")
        for choice in gui_terms:
            gui_window.add_button(
                f"{choice[1]}",
                lambda c=choice: [set_term_val(c), gui_window.root.destroy()],
            )
            print(choice[1])
            print(choice)
        gui_window.root.mainloop()

        print("this has been passed")
        terms = [chosen_term]
        print(terms)

    print(f"Searching through set terms: {terms}")

    # iterates through every term
    for term in terms:

        curr_page = get_page_soup(
            driver, f"https://beavs.osubeaverstore.com/Textbooks.asp?TermID={term[0]}"
        )

        departments = []

        for num, tr in enumerate(curr_page.find_all("tr")):
            if num == 0:
                continue

            for num2, option in enumerate(tr.find_all("option")):
                if num2 == 0:
                    continue

                # appends the department information for each term in case it
                # changes over time
                departments.append([option["value"], option.text])

        if output:
            print(f"Departments found for {term[1]}.")

        # goes through each department
        for department in departments:
            curr_page = get_page_soup(
                driver, f"https://beavs.osubeaverstore.com/Textbooks.asp?TermID={
                    term[0]}&DeptID={
                    department[0]}"
            )

            # for all the tables
            for num, table in enumerate(curr_page.find_all("table")):

                # if it is the first one, go to the next table (bypassing the
                # header)
                if num == 0:
                    continue

                # in the body of all of these tables
                for tbody in table.find_all("tbody"):

                    # in each row
                    for row in tbody.find_all("tr"):

                        row_skip = 0
                        # holds text for the row itself
                        row_text = []

                        term_app = str_clean(term[1])
                        dep_app = str_clean(department[1])
                        row_text.append(f"{term_app}")
                        row_text.append(f"{dep_app}")

                        # for each cell in the row
                        for cell in row.find_all("td"):

                            text = str_clean(cell.text)
                            if (
                                text
                                == "SEE CANVAS AND/OR INSTRUCTOR FOR COURSE MATERIALS - NO COST "
                                and nocost_skip
                            ):
                                row_skip = 1
                                break
                            row_text.append(text)

                        # append the row to the master matrix
                        if row_skip == 0:
                            # if at some point it would be desirable to add in book pricing
                            # this function doesn't work as is, but i stopped progress on it
                            # seeing as the compare site has rate limiting, which is fair
                            # otherwise, it would be best to simply link to the compare site
                            # in the sheet if anything i think
                            # row_text.append(STORE LINK HERE)
                            table_export.append(row_text)

            # logging text
            dpt_txt = str_clean(f"{department[1]}")
            if output:
                print(f"{dpt_txt} complete.")

        # formatting output
        if output:
            print("\n")

    # price_table = get_prices(driver, table_export)
    # for row in table_export:
    #     if row[8] in price_table:
    #         row.append(price_table[row[8]])

    # open an output csv file and then write the header into it before writing
    # every list element (row data) as a row in the csv file
    if save_file:
        with open(textbk_path, "w", newline="") as csvfile:
            csvwriter = csv.writer(csvfile)
            # csvwriter.writerow(fields)
            csvwriter.writerows(table_export)

    return table_export


def pull_info(path):
    """Pulls info from the given path to import as the bookstore data."""
    table_export = []
    with open(path, newline="") as csvfile:
        csvreader = csv.reader(csvfile)
        for row in csvreader:
            table_export.append(row)

    return table_export
