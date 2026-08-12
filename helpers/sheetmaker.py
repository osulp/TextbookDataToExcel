import pandas as pd
import configparser
from openpyxl import Workbook
from warnings import simplefilter

from helpers.bookstore import pull_textbook_data, pull_info
from helpers.utilities import get_int, get_clean, get_state, get_directory
from helpers.utilities import get_format_headers, get_enabled
from helpers.utilities import get_sheet_headers, get_string_cleaners
from helpers.classes import process_book, process_courses
from helpers.classes import process_sections, process_isbns, import_data
from helpers.enrollment import get_enrollment_data
from helpers.output import write_to_sheet
from helpers.grabber import setup_grabber, get_email
from helpers.grabber import email_exporter, email_importer
from helpers.analytics import setup_analytics
from helpers.analytics import export_analytics, import_analytics
from helpers.analytics import process_analytics


def make_excel_sheet(open_outlook=None, open_alma=None, gui_class=None):
    """Creates an excel sheet of all the data collected for textbook purchasing processing."""
    simplefilter(action="ignore", category=pd.errors.PerformanceWarning)
    simplefilter(action="ignore", category=FutureWarning)

    full_config = configparser.ConfigParser()
    full_config.read("config.ini")
    config = full_config["Main"]
    bookstore_cfg = full_config["Textbook"]
    enroll_cfg = full_config["Enroll"]
    grabber_cfg = full_config["Grabber"]
    analytics_cfg = full_config["Alma"]

    remove_duplicates = get_state(config["RemoveDuplicates"])
    remove_see_canvas = get_state(config["RemoveSeeCanvas"])

    pre_pull = get_state(bookstore_cfg["Import"])
    enroll_pull = get_state(enroll_cfg["Enabled"])

    if gui_class is not None:
        gui_use = True
    else:
        gui_use = False

    if open_outlook is None:
        grabber_enabled = get_enabled("Log into Outlook and pull email values? (y/n): ")
    else:
        grabber_enabled = open_outlook
    save_emails = get_state(grabber_cfg["Save"])
    import_emails = get_state(grabber_cfg["Import"])

    if open_alma is None:
        analytics_enabled = get_enabled(
            "Log into Alma and collect analytics data? (y/n): "
        )
    else:
        analytics_enabled = open_alma
    save_analytics = get_state(analytics_cfg["Save"])
    import_ana = get_state(analytics_cfg["Import"])

    enroll_path = get_directory("Input", enroll_cfg)
    output_path = get_directory("Output", config)
    textbk_path = get_directory("Save", bookstore_cfg)
    emails_path = get_directory("Save", grabber_cfg)
    analytics_path = get_directory("Save", analytics_cfg)

    # calling textbook data gatherer script / pulling prepulled data
    if pre_pull:
        try:
            textbook_table = pull_info(textbk_path)
        except BaseException:
            textbook_table = pull_textbook_data()
    else:
        textbook_table = pull_textbook_data()

    if import_emails:
        try:
            emails = email_importer(emails_path)
        except BaseException:
            emails = {}
    else:
        emails = {}

    # enrollment data
    if enroll_pull:
        try:
            emails, enrolls = get_enrollment_data(enroll_path, emails)
        except BaseException:
            enrolls = {}
    else:
        enrolls = {}

    # analytics storage
    if import_ana:
        try:
            analytics_store = import_analytics(analytics_path)
        except BaseException:
            analytics_store = {}
    else:
        analytics_store = {}

    # names & order of the headers
    head_names, main_headers = get_sheet_headers()

    # formatting headers : course num (0), section num (1), instructor/email (2)
    # $ -> course number, & -> section number, ^ -> "instructor/email"
    format_headers = get_format_headers()

    # decoupling -- presuming we are only doing a single term at a time
    sheet_term = textbook_table[1][0]

    # this is just to match the naming scheme
    # i.e. bookstore stores it as "2026-Spring"; LEAD stores it as "Spring26"
    # this basically takes any string "XYZK-Season" -> "SeasonZK"
    sheet_term = sheet_term.split("-")
    sheet_term = sheet_term[1] + sheet_term[0][2:]

    # these phrases will all be removed from each book title to prevent
    # duplicates
    book_clean, author_clean = get_string_cleaners()

    dataframe = pd.DataFrame()

    for header in main_headers:
        dataframe[f"{header}"] = []
        # force header frame dtype to be object
        dataframe[f"{header}"] = dataframe[f"{header}"].astype(object)

    book_list = []

    if grabber_enabled:
        grabber_driver = setup_grabber(gui_use)
        # grabber_thread = start_thread()

    if analytics_enabled:
        analytics_driver = setup_analytics(gui_use)

    for row in textbook_table:
        if remove_duplicates:
            title = get_clean(book_clean, row[5])
            author = get_clean(author_clean, row[7])
        else:
            title = str(row[5].title().strip())
            author = str(row[7].title().strip())

        canvas = "See Canvas And/Or Instructor For Course Materials"
        if remove_see_canvas and title == canvas:
            continue

        ed = get_int(row[6])

        department = row[1]
        dep_arr = department.split(":")
        subj_code = dep_arr[0].strip()
        course_code = f"{subj_code}{row[2]}".strip()

        section = get_int(row[3])
        if section is None:
            continue

        instructor = row[4]
        isbn = row[8].replace("-", "").strip()
        if isbn == "":
            isbn = None

        publisher = row[9].title().strip()
        requirement = row[10].title().strip()
        comment = row[12].strip()
        requisition = row[13].strip()

        # sku is unused as of now
        sku = row[11]

        email = ""
        if instructor in emails:
            email = emails[f"{instructor}"]

        # aiming to have an alternative means of checking empty results with outlook
        # this nearly matches what we would manually do
        if email == "" and grabber_enabled:
            email = get_email(instructor, grabber_driver)
            emails[f"{instructor}"] = email
            print(email)

        enroll = [0, "N/A"]
        if f"{course_code}" in enrolls:
            if f"{section}" in enrolls[f"{course_code}"]:
                enroll = enrolls[f"{course_code}"][f"{section}"]

        # bandaid fix
        # if no isbn, not a book as far as im looking at right now
        if pd.isna(isbn) or isbn is None:
            continue
        # and this is a troublemaker, removing any titles with this for now
        if title == "Lab Component Package(Not Avail @ Beaver Store)":
            continue

        # next step is hooking in alma anayltics here
        # each book needs one check box as well as some other boxes
        # cross reference with most recent winter sheet that is in use
        # can update book names off of primo
        if not pd.isna(isbn):
            if f"{isbn}" in analytics_store and (analytics_enabled or import_ana):
                data = analytics_store[f"{isbn}"]["Data"]
            elif analytics_enabled:
                data = process_analytics(analytics_driver, analytics_store, isbn)
                analytics_store[f"{isbn}"] = {"Data": data}

        book_info = {
            "Title": title,
            "Author": author,
            "Edition": ed,
            "Instructor": instructor,
            "Email": email,
            "Course": course_code,
            "Section": section,
            "Enroll": enroll,
            "ISBN": isbn,
            "Publisher": publisher,
            "Req": requirement,
            "RequiDate": requisition,
            "Comment": comment,
            "Analytics": data,
        }

        book_list = process_book(book_list, book_info)

    if save_emails:
        email_exporter(emails_path, emails)

    if save_analytics:
        export_analytics(analytics_path, analytics_store)

    max_courses = process_courses(book_list, format_headers, dataframe)
    process_sections(book_list, format_headers, max_courses, dataframe)
    process_isbns(book_list, head_names, main_headers, dataframe)
    dataframe = import_data(book_list, format_headers, head_names, dataframe)

    workbook = Workbook()
    write_to_sheet(dataframe, sheet_term, workbook, head_names)
    workbook.save(output_path)
    print("Sheet exported.")
