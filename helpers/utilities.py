import os
import configparser
import pandas as pd
from openpyxl.styles import Alignment
from requests.structures import CaseInsensitiveDict


def get_int(value):
    """Gets int value, returns None if empty."""
    output = None

    if type(value) is str and not pd.isna(value):
        if not value.strip() == "":
            if not any(char.isalpha() for char in value):
                value = value.replace(" ", "")
                output = int(value)
    elif type(value) is float and not pd.isna(value):
        output = int(value)
    elif type(value) is int and not pd.isna(value):
        output = value

    return output


def get_clean(cleaner, name):
    """Uses cleaner and input to remove every phrase in cleaner
    from the input."""
    name = name.title()
    name = name.strip()
    for phrase in cleaner:
        name = name.replace(phrase.title(), "")
    name = name.strip()

    # making letters lowercase after '
    if "'" in name:
        name_len = len(name)
        idx = -2
        idx_list = []
        while not (idx == -1 or idx == name_len - 1):
            # print(f'{idx} {name}')
            if idx != -2:
                idx_list.append(idx)
                idx = name.find("'", idx + 1, name_len)
            else:
                idx = name.find("'")
            # print(idx)

        # preventing other issues with specific letters
        letter_check = ["S", "L", "T", "M"]
        for kdx in idx_list:
            # print(f'{name[kdx]} {name[kdx] in letter_check}')
            if name[kdx + 1] in letter_check:
                temp_list = list(name)
                temp_list[kdx + 1] = name[kdx + 1].lower()
                name = "".join(temp_list)

    temp = name
    new_name = ""
    first = True
    while new_name is not temp:
        if first:
            first = False
        else:
            temp = new_name
        new_name = temp.strip()
        new_name = new_name.replace("&nbsp;", "")
        new_name = new_name.replace("  ", " ")
        new_name = new_name.replace("\t", "")
        new_name = new_name.replace("\n", "")

    prior = ""
    for jdx, letter in enumerate(new_name):
        if jdx == 0:
            prior = letter
            continue
        if prior == " ":
            new_name = list(new_name)
            new_name[jdx] = new_name[jdx].upper()
            new_name = "".join(new_name)
        prior = letter

    return f"{new_name}"


def get_state(config):
    """Provide a config T/F option, returns False if "False"."""
    if config == "False":
        return False
    else:
        return config


def get_directory(directory, config):
    """Provide a directory and config object, returns a formatted path."""
    curr_dir = os.path.dirname(__file__)
    if config[f"{directory}Dir"] is not None:
        path = os.path.join(
            curr_dir, config[f"{directory}Dir"], config[f"{directory}File"]
        )
    else:
        path = os.path.join(curr_dir, config[f"{directory}File"])

    return path


def get_filepath(name, home=True):
    """Gets the OS path for a given file."""
    curr_dir = os.path.dirname(__file__)
    if home:
        path = os.path.join(curr_dir, "..", name)
    else:
        path = os.path.join(curr_dir, name)
    return path


def get_letter(num):
    """Converts a number into a spreadsheet letter column.
    i.e. 2 -> B, 26 -> Z, 27 -> AA, 28 -> AB, etc."""
    result = ""
    secondary = 0
    while num > 26:
        secondary += 1
        num -= 26

    if secondary > 0:
        result += get_letter(secondary)
    result += chr(ord("A") + num - 1)
    return result


def get_edition_string(num):
    """Takes the current working row and checks it for the
    edition number, creating a string for it."""

    edition_num = str(num) if pd.isna(num) is False else None
    if edition_num == "":
        edition_num = None
    th_list = ["4", "5", "6", "7", "8", "9", "0"]

    if edition_num is not None:
        if edition_num[-1] == "1":
            # special case for 11, 12, 13
            if len(edition_num) > 1:
                if edition_num[-2] == "1":
                    edition_num += "th"
                else:
                    edition_num += "st"

            else:
                edition_num += "st"

        elif edition_num[-1] == "2":
            if len(edition_num) > 1:
                if edition_num[-2] == "1":
                    edition_num += "th"
                else:
                    edition_num += "nd"
            else:
                edition_num += "nd"

        elif edition_num[-1] == "3":
            if len(edition_num) > 1:
                if edition_num[-2] == "1":
                    edition_num += "th"
                else:
                    edition_num += "rd"
            else:
                edition_num += "rd"

        elif edition_num[-1] in th_list:
            edition_num += "th"

        # edition_num += ' Edition'

    return edition_num


def get_format_headers():
    """Provides the spreadsheet format headers for courses,
    sections, and additional information. Moved here for
    ease of updating for both scripts."""

    # formatting headers : course num(0), section num(1), instructor/email(2)
    # $ -> course number, & -> section number, ^ -> "instructor/email"
    course_header = "Course $"
    section_header = course_header + ", Section &"
    instructor_header = section_header + ", ^"
    format_headers = [course_header, section_header, instructor_header]
    return format_headers


def get_replace_header(header, course_num, section_num="", add_info=""):
    """Given a header and additional information, formats the header
    correctly, based on the format headers."""
    new_header = header
    new_header = new_header.replace("$", f"{course_num}")
    new_header = new_header.replace("&", f"{section_num}")
    new_header = new_header.replace("^", add_info)
    return new_header


def get_split_course(course):
    """Takes course such as MTH251 and returns [MTH, 251].
    Aids in formatting and providing direct links."""

    for k, char in enumerate(course):
        if char.isdigit():
            output = [course[:k], course[k:]]
            return output


def get_input(min=0, max=0, text=""):
    """Gets an input w/ error checking. If no min or max is set, it will parse strings."""
    if not (min == 0 and max == 0):
        while True:
            try:
                num = get_int(input(text))
                if num < min or num > max:
                    raise ValueError("Out of range")
                else:
                    return num
            except BaseException:
                print("Out of range / invalid input.")
    else:
        while True:
            try:
                output = str(input(text))
                return output
            except BaseException:
                print("Invalid input.")


def get_enabled(text=""):
    """Gets an input w/ error checking, returns True or False."""
    while True:
        try:
            state = input(text)
            if state == "n" or state == "y":
                break
            else:
                raise ValueError("Incorrect input.")
        except BaseException:
            print("Incorrect input.")
    if state == "n":
        return False
    else:
        return True


def get_sheet_headers():
    """Gets the header names and dictionary."""
    # modify the headers.ini file to update header names or order
    # this can be done via the GUI

    config = configparser.ConfigParser()
    config.read("helpers/ini/headers.ini")
    header_dict = CaseInsensitiveDict()
    header_list = []

    names = config["Names"]
    order = config["Order"]

    for key in names:
        header_dict[key] = names[key]

    orderkeys = order["OrderKey"].split("-")
    for orderkey in orderkeys:
        header_list.append(header_dict[orderkey])

    return header_dict, header_list


def get_config_headers():
    """Gets the config file reading for the headers.ini file."""
    config = configparser.ConfigParser()
    config.read("helpers/ini/headers.ini")
    return config


def get_string_cleaners():
    """Gets the cleaner lists for authors and book titles."""
    # these phrases will all be removed from each book title to prevent
    # duplicates
    book_clean = [
        "(Cei)",
        "(Loose-Leaf)",
        "Loose-Leaf",
        "Ebook - Lifetime Duration",
        "Ebook(5 Yr Access)",
        "Ebook (Lifetime)",
        "Ebook (180 days)",
        "Ebook (150 days)",
        "Ebook (120 days)",
        "Ebook - Lifetime Access",
        "Ebook -Lifetime Access",
        "Ebook - Lifetime",
        "Ebook - 180Days",
        "Etext W/Connect Access Code",
        "[Qr]",
        "[Nbs]",
        "(Cei)",
        "(Ll)",
        "W/1 Term Access Code Pkg",
        "W/1 Year Access Code Pkg",
        "W/2 Year Access Code Pkg",
        "1 Term Access Code",
        "1 Year Access Code",
        "2 Year Access Code",
        "Ebook",
        "(5Th Edition)",
        "Update Etext W/ Achieve",
        "W/Achieve  Pkg.",
        "- No Cost",
        "(3Rd Edition)",
        "(5 Yr Access)",
    ]
    author_clean = ["(2)", "(3)", "(digital)", "-[Qr Code]", "[Qr Code}", "(Nio)"]
    return book_clean, author_clean


def get_row_info(row, key):
    """Gets info within a row given a key. Checks for blank information."""
    headers, head_list = get_sheet_headers()
    result = row[headers[f"{key}"]] if not pd.isna(row[headers[f"{key}"]]) else ""
    return result


def get_campus(campus):
    """Returns the full campus name for the letter."""
    result = None
    if campus == "C":
        result = "Corvallis"
    elif campus[0] == "D":
        result = "Ecampus"
    elif campus == "Z":
        result = "International"
    elif campus == "L":
        result = "LaGrande"
    elif campus == "N":
        result = "Newport"
    elif campus == "B":
        result = "Cascades"
    elif campus == "PDX" or campus == "H":
        result = "Portland"
    return result


def set_col_format(col, num_format, worksheet):
    """This takes a column letter plus some flags and then
    processes the intended style calculations for it."""
    width = 0
    for idx, cell in enumerate(worksheet[col]):
        length = len(f"{cell.value}")
        if length > width:
            width = length
        if idx != 0:
            cell.alignment = Alignment(horizontal="left")
            if num_format:
                cell.number_format = "0"
    if width < 6:
        width = 6
    worksheet.column_dimensions[col].width = width + 4
