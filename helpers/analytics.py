from helpers.utilities import get_int
from helpers.helpergui import AddedGUI
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.window import WindowTypes
import bs4
import configparser
import time
import csv
import ast
import threading


def get_columns(key="ebook"):
    """Gets the columns being used to construct the SQL query."""
    sql_columns = []
    overall_section = ""
    if key == "ebook":
        sql_columns = [
            {
                "Key": "Bibliographic Details",
                "Cols": [
                    "Author",
                    "Earliest Possible Publication Year",
                    "Title",
                    "Publisher",
                    "MMS Id",
                    "ISBN",
                    "Edition",
                    "Material Type",
                    "Resource Type",
                ],
            },
            {"Key": "Edition Simplified", "Cols": ["Edition Simplified (Num)"]},
        ]
        overall_section = "Digital Inventory"

    elif key == "access":
        sql_columns = [
            {
                "Key": "Bibliographic Details",
                "Cols": ["MMS Id"],
            },
            {
                "Key": "Representation Access Rights",
                "Cols": ["Access Right Name", "Access Right Desc"],
            },
        ]
        overall_section = "Digital Inventory"

    elif key == "physical":
        sql_columns = [
            {
                "Key": "Bibliographic Details",
                "Cols": [
                    "Author",
                    "Title",
                    "ISBN",
                    "Resource Type",
                    "MMS Id",
                    "Earliest Possible Publication Year",
                ],
            },
            {
                "Key": "Physical Item Details",
                "Cols": [
                    "Material Type",
                    "Num of Items (In Repository)",
                    "Temporary Physical Location in Use",
                ],
            },
            {
                "Key": "Holdings Details",
                "Cols": ["Holdings Lifecycle", "Suppressed from Discovery"],
            },
            {"Key": "Edition Simplified", "Cols": ["Edition Simplified (Num)"]},
            {"Key": "Location", "Cols": ["Location Name"]},
            {"Key": "Temporary Location", "Cols": ["Temporary Location Name"]},
        ]
        overall_section = "Physical Items"

    elif key == "e-inventory":
        sql_columns = [
            {"Key": "Bibliographic Details", "Cols": ["MMS Id", "Title"]},
            {
                "Key": "Electronic Collection",
                "Cols": ["Electronic Collection Public Name"],
            },
        ]
        overall_section = "E-Inventory"
    # isbn_list = [9781478651123, 9780357900161, 9781544342337, 9781394152100]

    elif key == "public":
        sql_columns = [
            {"Key": "Bibliographic Details", "Cols": ["MMS Id", "Title"]},
            {
                "Key": "Portfolio",
                "Cols": ["Portfolio Public Note"],
            },
        ]
        overall_section = "E-Inventory"
    return overall_section, sql_columns


def get_col_len(cols):
    """Returns the total number of columns within the SQL query."""
    total = 0
    for group in cols:
        total += len(group["Cols"])
    return total


def get_table(driver):
    """Grabs the table on the Alma Analytics Results page."""
    while True:
        loading = check_element(driver, "ProgressIndicatorDiv", 1)
        if loading:
            continue

        res_error = check_element(driver, "ErrorInfo", 1)
        table_get = check_element(driver, "PTChildPivotTable", 1)

        if table_get:
            table = driver.find_element(By.CLASS_NAME, "PTChildPivotTable")
            html = table.get_attribute("innerHTML")
            lxml = bs4.BeautifulSoup(html, "lxml")
            tr_list = lxml.find_all("tr")
            return tr_list
        elif res_error:
            return []


# TODO
# may need further testing
def pull_one_search(driver, mms_list):
    """Opens a OneSearch tab to double check that the MMS ID exists within Primo.
    Takes a list and returns a list, though only used with single IDs right now."""
    search_link = "https://search.library.oregonstate.edu/discovery/search?query=any,contains,%&tab=Everything&search_scope=OSU_Everything_Profile&vid=01ALLIANCE_OSU:OSU&lang=en&offset=0"
    # 991019530001865 example id for testing
    base_window = driver.current_window_handle
    driver.switch_to.new_window(WindowTypes.TAB)

    result_list = []

    for mms in mms_list:
        found = True
        check = 0
        new_link = search_link.replace("%", f"{mms}")
        driver.get(new_link)

        # if the element with no results found is present
        # appends false, otherwise, appends true
        while True:
            try:
                WebDriverWait(driver, 3).until(
                    EC.presence_of_element_located((By.CLASS_NAME, "md-headline"))
                )
                found = False
                # print(search_box)
                break
            except Exception as err:
                # print(err)
                if check == 1:
                    break
                check += 1

        result_list.append(found)

    driver.close()
    driver.switch_to.window(base_window)
    return result_list


def pull_data(driver, bib_section, bib_value, sql_key):
    """Given a section, value, and specific SQL template, grabs the
    relevant data that is desired."""
    section, sql_cols = get_columns(key=f"{sql_key}")
    sql = setup_sql(section, sql_cols, f"{bib_section}")
    sql = sql.replace("%", f"%{bib_value}%")
    input_sql(driver, sql)
    tr_list = get_table(driver)

    if tr_list == []:
        return []

    cutoff = 3 + get_col_len(sql_cols)
    tr_list = tr_list[cutoff:]

    return_list = []
    # storing entries for empty portions
    store_dict = {}

    # storing order for indexing
    store_list = []
    for dict in sql_cols:
        for col in dict["Cols"]:
            store_list.append(col)

    for tr in tr_list:
        for dict in sql_cols:
            for col in dict["Cols"]:
                store_dict[col] = ""
        td_list = tr.find_all("td")
        for td in td_list:
            try:
                td_id = td["id"]
                td_text = td.get_text()
                id_list = td_id.split("_")
                cat_id = get_int(id_list[5])
                column = store_list[cat_id]
                store_dict[column] = td_text
            except Exception as err:
                print(err)
        return_list.append(store_dict.copy())

    return return_list


def input_sql(driver, text=""):
    """Helper function that inputs the given text into the SQL input box."""
    click_element(driver, "td", "title", "Edit SQL, XML and other technical details")
    click_element(driver, "a", "title", "New Analysis")

    while True:
        try:
            sql_box = WebDriverWait(driver, 5).until(
                EC.presence_of_element_located((By.ID, "idNewSimpleSqlRequestInput"))
            )
            break
        except Exception as err:
            print("waiting for open sql box")

    sql_box.clear()
    sql_box.send_keys(text)

    click_element(driver, "a", "name", "SSRDOk")

    # returning in case it is needed at some point, can change/remove this
    return sql_box


def check_element(driver, class_name, timer):
    """Helper function that checks for an element with the given class name."""
    try:
        WebDriverWait(driver, timer).until(
            EC.presence_of_element_located((By.CLASS_NAME, f"{class_name}"))
        )
        return True
    except Exception as err:
        return False


def click_element(driver, tag, selector, detail):
    """Helper function to click on an element given an HTML tag, CSS selector, and value."""
    while True:
        try:
            button = WebDriverWait(driver, 5).until(
                EC.element_to_be_clickable(
                    (By.CSS_SELECTOR, f"{tag}[{selector}='{detail}']")
                )
            )
            button.click()
            return
        except Exception as err:
            print(err)


def process_new_isbn(driver, title, state):
    """Helper function to find what ISBN we do own for a particular book."""
    check_list = pull_one_search(driver, [title])
    if check_list[0] is False:
        print(f"{title} not found on OneSearch.")
        return None

    sql_section, sql_columns = get_columns(state)
    sql_statement = setup_sql(sql_section, sql_columns)

    old = f' WHERE "Bibliographic Details"."ISBN"'
    new = f'WHERE UPPER("Bibliographic Details"."Title")'
    sql_statement.replace(old, new)
    sql_text = sql_statement.replace("'%'", f"UPPER('{title}')")
    input_sql(driver, sql_text)
    tr_list = get_table(driver)

    if tr_list == []:
        print(f"{title} not in Analytics.")
        return None

    cutoff = 3 + get_col_len(sql_columns)
    tr_list = tr_list[cutoff:]

    eval_list = []

    # storing entries for empty portions
    store_dict = {}
    # storing order for indexing
    store_list = []
    for dict in sql_columns:
        for col in dict["Cols"]:
            store_dict[col] = ""
            store_list.append(col)

    for tr in tr_list:
        td_list = tr.find_all("td")
        for td in td_list:
            try:
                td_id = td["id"]
                td_text = td.get_text()
                id_list = td_id.split("_")
                cat_id = get_int(id_list[5])
                column = store_list[cat_id]
                store_dict[column] = td_text
            except Exception as err:
                print(err)

        eval_list.append(store_dict.copy())

    # maybe pass in more information later to validate
    # for material in eval_list:

    if eval_list:
        return eval_list[0]
    else:
        return None


def process_analytics(analytics_driver, isbn):
    """Fully processes a given ISBN number and pulling all the data from Alma + processing it."""
    year = None
    data = {}

    print_list = pull_data(analytics_driver, "ISBN", isbn, "physical")
    ebook_list = pull_data(analytics_driver, "ISBN", isbn, "ebook")
    for listing in print_list:
        try:
            num_items = get_int(listing["Num of Items (In Repository)"])
            suppressed = get_int(listing["Suppressed from Discovery"])

            if num_items is None:
                continue
            if suppressed is None:
                suppressed = 0
            if suppressed >= num_items or num_items <= 0:
                continue

            copy_count = num_items - suppressed
            book_type = listing["Resource Type"].replace("Book - ", "")
            mms_id = listing["MMS Id"]
            link = f"https://search.library.oregonstate.edu/permalink/01ALLIANCE_OSU/19c134f/alma{mms_id}"

            if mms_id.strip() == "":
                continue

            check_list = pull_one_search(analytics_driver, [mms_id])
            if check_list[0] is False:
                print(
                    f"Missing from Primo (PHYSICAL); skipping. {mms_id} : num:{num_items} supp:{suppressed}"
                )
                continue

            # tracking physical location
            location = listing["Location Name"]
            temp_loc = listing["Temporary Location Name"]
            temp_loc_inuse = listing["Temporary Physical Location in Use"]
            if temp_loc_inuse == "Yes":
                temp_loc_inuse = True
            else:
                temp_loc_inuse = False

            if temp_loc_inuse:
                location = temp_loc

            if location == "Valley Reserves Suppressed":
                continue

            if year is None:
                year = listing["Earliest Possible Publication Year"]

            if mms_id not in data:
                data[mms_id] = {
                    "Types": [book_type],
                    "Copies": [copy_count],
                    "Users": [0],
                    "CDL": [False],
                    "Link": link,
                    "Year": year,
                    "Location": location,
                }
            else:
                if book_type not in data[mms_id]["Types"]:
                    data[mms_id]["Types"].append(book_type)
                    data[mms_id]["Copies"].append(copy_count)
                    data[mms_id]["Users"].append(0)
                    data[mms_id]["CDL"].append(False)
                else:
                    type_idx = data[mms_id]["Types"].index(book_type)
                    data[mms_id]["Copies"][type_idx] += copy_count

                if year is not None:
                    data[mms_id]["Year"] = year

                if location != "" and data[mms_id]["Location"] == "":
                    data[mms_id]["Location"] = location

        except Exception as err:
            print("Print book processing error.")
            print(err)

    for listing in ebook_list:
        try:
            book_type = listing["Resource Type"].replace("Book - ", "")
            if book_type != "Electronic":
                continue
            mms_id = listing["MMS Id"]
            link = f"https://search.library.oregonstate.edu/permalink/01ALLIANCE_OSU/19c134f/alma{mms_id}"
            if year is None:
                year = listing["Earliest Possible Publication Year"]

            if mms_id.strip() == "":
                continue

            check_list = pull_one_search(analytics_driver, [mms_id])
            if check_list[0] is False:
                print(f"Missing from Primo (EBOOK); skipping. {mms_id}")
                continue

            # TODO
            # double check this implementation
            access_platform = ""
            e_collection_list = pull_data(
                analytics_driver, "MMS Id", mms_id, "e-inventory"
            )
            for collection in e_collection_list:
                if collection["Electronic Collection Public Name"]:
                    access_platform = collection["Electronic Collection Public Name"]

            access_list = pull_data(analytics_driver, "MMS Id", mms_id, "access")
            access_name = ""
            access_desc = ""
            for access in access_list:
                if access["Access Right Name"]:
                    access_name = access["Access Right Name"]
                if access["Access Right Desc"]:
                    access_desc = access["Access Right Desc"]

            cdl = False
            if access_name:
                if "CDL" in access_name:
                    cdl = True

            users = -1
            if access_desc:
                if "Allows" in access_desc:
                    temp = access_desc.split(" ")
                    users = get_int(temp[1])

            if users == -1:
                note_list = pull_data(analytics_driver, "MMS Id", mms_id, "public")
                for note in note_list:
                    if note["Portfolio Public Note"]:
                        note_text = note["Portfolio Public Note"]
                        upper_text = note_text.upper()
                        # looking at all the analytics entries, this is what cuts the most out w/o cutting any off
                        compare = "Connect to this resource online".upper()
                        if compare in upper_text:
                            if "unlimited".upper() in upper_text:
                                users = "unlimited"
                            elif "multiple".upper() in upper_text:
                                users = "multiple"
                            else:
                                process_list = upper_text.split("(")
                                for section in process_list:
                                    if "user".upper() in section:
                                        users = get_int(section.split(" ")[0])

            # adding a failstate to ensure these values are marked as unknown
            # and can be easily removed via find & replace
            if users == -1:
                users = "?"

            if mms_id not in data:
                data[mms_id] = {
                    "Types": [book_type],
                    "Copies": [0],
                    "Users": [users],
                    "CDL": [cdl],
                    "Link": link,
                    "Platform": access_platform,
                    "Year": year,
                }
            else:
                if book_type not in data[mms_id]["Types"]:
                    data[mms_id]["Types"].append(book_type)
                    data[mms_id]["Copies"].append(0)
                    data[mms_id]["Users"].append(users)
                    data[mms_id]["CDL"].append(cdl)
                else:
                    type_idx = data[mms_id]["Types"].index(book_type)
                    data[mms_id]["Users"][type_idx] += users

                if year is not None:
                    data[mms_id]["Year"] = year

                if access_platform != "" and data[mms_id]["Platform"] == "":
                    data[mms_id]["Platform"] = access_platform

        except Exception as err:
            print("Ebook error")
            print(err)

        # if pd.isna(ed):
        #     ed = get_edition_string(analytics_dict['Edition Simplified (Num)'])

    return data


def setup_analytics(gui=False):
    """Sets up the Selenium web browser driver to perform all analytics functions."""
    full_config = configparser.ConfigParser()
    full_config.read("config.ini")
    config = full_config["Alma"]
    link = config["AnalyticsLink"]
    query = config["QueryPage"]

    driver = webdriver.Chrome()
    driver.get(link)

    # TODO
    # if done with other stuff, can add click events here to speed up
    # automated portion

    def context_window(text_list):
        gui_window = AddedGUI(title="Analytics Helper")
        for text in text_list:
            gui_window.add_label(text)
        gui_window.add_button("Done", gui_window.root.destroy)
        gui_window.root.mainloop()

    if not gui:
        print("Log into Alma. Navigate to analytics section.")
    else:
        texts = ["Log into Alma."]
        ui_thread = threading.Thread(target=lambda t=texts: context_window(t))
        ui_thread.start()

    break_check = False
    while not break_check:
        try:
            WebDriverWait(driver, 5).until(
                EC.presence_of_element_located((By.CLASS_NAME, "recentLinks"))
            )
            driver.find_element(By.CLASS_NAME, "recentLinks")
            break_check = True
        except Exception as err:
            print("Awaiting Alma log-in")

    if not gui:
        print("Navigate to analytics section -> access analytics")
    else:
        texts = ["Go to Analytics.", "Then press 'Access Analytics'."]
        ui_thread = threading.Thread(target=lambda t=texts: context_window(t))
        ui_thread.start()

    while True:
        time.sleep(3)
        if len(driver.window_handles) > 1:
            driver.switch_to.window(driver.window_handles[-1])
            break

    time.sleep(2)
    curr_url = driver.current_url
    q_idx = curr_url.index("?")
    q_url = f"{curr_url[:q_idx]}{query}"
    driver.get(q_url)

    return driver


def setup_sql(sql_section, sql_list, bib_section="ISBN"):
    """Helper function to turn the SQL categories and lists into a full single query."""
    sql = "SELECT"
    idx = 0
    for dict in sql_list:
        section = dict["Key"]
        for col in dict["Cols"]:
            sql += f' "{section}"."{col}" saw_{idx},'
            idx += 1
    sql += f' FROM "{sql_section}" WHERE "Bibliographic Details"."{bib_section}"'
    sql += """ LIKE '%' """
    return sql


def export_analytics(path, info):
    """Exports the analytics data into a CSV."""
    with open(path, "w", newline="") as csvfile:
        csvwriter = csv.writer(csvfile)
        for isbn in info:
            csvwriter.writerow([f"{isbn}"] + [f'{info[isbn]["Data"]}'])


def import_analytics(path):
    """Imports the stored data from the analytics CSV."""
    info = {}
    with open(path, newline="") as csvfile:
        csvreader = csv.reader(csvfile)
        for row in csvreader:
            info[row[0]] = {"Data": ast.literal_eval(row[1])}

    return info
