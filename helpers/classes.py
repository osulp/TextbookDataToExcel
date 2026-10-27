import pandas as pd
from helpers.utilities import get_replace_header, get_int
from helpers.utilities import get_campus


class Book:
    """Object that stores relevant book information to be used to format and
    configure a dataframe. Takes in a dictionary to construct the base
    object. See sheetmaker.py for the book_info dictionary structure."""

    def __init__(self, info):
        # bookstore information
        self.courses = [info["Course"]]
        self.sections = [
            [[info["Section"], info["Instructor"], info["Email"], info["Enroll"][0]]]
        ]
        self.sec_size = [1]
        self.isbns = [info["ISBN"]]
        self.title = info["Title"]
        self.author = info["Author"]
        self.edition = info["Edition"]
        self.publisher = info["Publisher"]
        self.requirement = info["Req"]
        self.requisition = info["RequiDate"]
        self.comment = info["Comment"]

        # analytics information
        self.analytics = info["Analytics"]

        camp_name = get_campus(info["Enroll"][1])
        if camp_name is not None:
            self.campuses = [camp_name]
        else:
            self.campuses = []

        self.corvallis_enroll = 0
        self.ecampus_enroll = 0
        self.other_enroll = 0

        if info["Enroll"][1] == "C":
            self.corvallis_enroll = info["Enroll"][0]

        elif info["Enroll"][1][0] == "D":
            self.ecampus_enroll = info["Enroll"][0]

        else:
            self.other_enroll = info["Enroll"][0]

        self.total_enroll = info["Enroll"][0]

    def add_course(self, course, section, instructor, email, enroll):
        """Adds course information to book object."""
        self.courses.append(course)
        self.sections.append([[section, instructor, email, enroll[0]]])
        self.sec_size.append(1)
        self.add_enroll(enroll[1], enroll[0])

    def add_section(self, course, section, instructor, email, enroll):
        """Adds section information to book object."""
        try:
            idx = self.courses.index(course)
        except ValueError as err:
            print(f"Course Index not found: {err}")
        self.sections[idx].append([section, instructor, email, enroll[0]])
        self.sec_size[idx] += 1
        self.add_enroll(enroll[1], enroll[0])

    def add_isbn(self, isbn):
        """Adds an ISBN number to the book."""
        self.isbns.append(isbn)

    def add_enroll(self, campus, amt):
        """Adds enrollment information to the book."""
        if campus == "C":
            self.corvallis_enroll += amt
        elif campus[0] == "D":
            self.ecampus_enroll += amt
        else:
            self.other_enroll += amt

        self.total_enroll += amt

        camp_name = get_campus(campus)
        if camp_name not in self.campuses and camp_name is not None:
            self.campuses.append(camp_name)

    def add_required(self):
        '''Changes requirement status to "Required."'''
        self.requirement = "Required"


def get_max_index(len_list):
    """Gets a list of indices of the largest courses in order based on number of sections."""
    output = []
    temp = len_list.copy()
    while max(temp) > 0:
        # append the index of the largest course
        output.append(temp.index(max(temp)))
        # set that course size to 0 before going to the next
        temp[output[-1]] = 0
    return output


def get_max_courses(book_list):
    """Gets the total number of course headers that need to be added."""
    max_len = 0
    for book in book_list:
        max_len = max(len(book.courses), max_len)
    return max_len


def get_max_sections_list(book_list, course_amt):
    """Gets the values for how many section columns to put per course numbering."""
    sec_len = []
    for idx in range(course_amt):
        sec_len.append(0)
        for book in book_list:
            try:
                next_largest = sorted(book.sec_size, reverse=True)[idx]
                sec_len[idx] = max(next_largest, sec_len[idx])
            except BaseException:
                # no more to check for the given book
                pass
    return sec_len


def process_book(book_list, book_dict):
    """Processed incoming book information and creates / adds book
    information to the main list of book objects."""
    book = None
    for search_book in book_list:
        if book_dict["Title"] == search_book.title:
            book = search_book
            break

    if book is not None:

        # isbn
        isbn_found = False
        for num in book.isbns:
            if book_dict["ISBN"] == num:
                isbn_found = True
                break

        if not isbn_found:
            book.add_isbn(book_dict["ISBN"])

        # requirement
        if book_dict["Req"] == "Required":
            book.add_required()
        elif book.requirement != "Required" and not pd.isna(book_dict["Req"]):
            if len(book_dict["Req"]) > 0:
                book.requirement = book_dict["Req"]

        # course
        course_found = False
        section_found = False
        for idx, code in enumerate(book.courses):
            if book_dict["Course"] == code:
                course_found = True
                for info in book.sections[idx]:
                    if book_dict["Section"] == info[0]:
                        section_found = True
                        break
                break

        if not course_found:
            book.add_course(
                book_dict["Course"],
                book_dict["Section"],
                book_dict["Instructor"],
                book_dict["Email"],
                book_dict["Enroll"],
            )

        elif not section_found and course_found:
            book.add_section(
                book_dict["Course"],
                book_dict["Section"],
                book_dict["Instructor"],
                book_dict["Email"],
                book_dict["Enroll"],
            )

    else:
        new_book = Book(book_dict)
        book_list.append(new_book)

    return book_list


def process_courses(book_list, headers, df):
    """Processes the max number of course columns needed, based on a list
    of Book objects, inserting the necessary columns into the dataframe."""
    max_len = get_max_courses(book_list)
    for idx in range(1, max_len + 1):
        df.insert(idx - 1, f"{headers[0].replace('$', f'{idx}')}", pd.Series([]))

    return max_len


def process_sections(book_list, headers, course_amt, df):
    """Processes the necessary number of section columns per course, based on a
    list of Book objects, inserts necessary columns into the dataframe."""
    sec_len = get_max_sections_list(book_list, course_amt)
    sec_added = 0
    for idx, num in enumerate(sec_len):
        for iter in range(1, num + 1):
            df.insert(
                1 + sec_added + idx,
                f"{get_replace_header(headers[1], idx + 1, iter)}",
                pd.Series([]),
            )
            df.insert(
                2 + sec_added + idx,
                f"{get_replace_header(headers[2], idx + 1, iter, 'Instructor')}",
                pd.Series([]),
            )
            df.insert(
                3 + sec_added + idx,
                f"{get_replace_header(headers[2], idx + 1, iter, 'Email')}",
                pd.Series([]),
            )
            df.insert(
                4 + sec_added + idx,
                f"{get_replace_header(headers[2], idx + 1, iter, 'Enroll')}",
                pd.Series([]),
            )
            sec_added += 4


def process_isbns(book_list, headers, head_order, df):
    """Processes the max number of ISBN columns needed from a
    list of Book objects, inserts necessary number into the dataframe."""
    max_len = 0
    for book in book_list:
        if len(book.isbns) > max_len:
            max_len = len(book.isbns)

    col_total = len(df.columns)
    head_len = len(head_order) - 1
    isbn_idx = head_order.index(f"{headers['ISBN']}")
    for num in range(2, max_len + 1):
        df.insert(
            col_total - (head_len - isbn_idx),
            f"{headers['ISBN'].replace('1', f'{num}')}",
            pd.Series([]),
        )
        col_total += 1


def import_data(book_list, format, main, df):
    """Master function that takes the list of Book objects, header dictionary/list,
    and a dataframe object and injects the dataframe with the book information."""
    for idx, book in enumerate(book_list):
        row = idx + 1
        df.loc[row, main["Title"]] = book.title
        df.loc[row, main["Author"]] = book.author
        df.loc[row, main["Edition"]] = book.edition
        df.loc[row, main["MaxEnroll"]] = book.total_enroll
        df.loc[row, main["Publisher"]] = book.publisher
        df.loc[row, main["Reqs"]] = book.requirement
        df.loc[row, main["ReqDate"]] = book.requisition
        df.loc[row, main["Comments"]] = book.comment

        # more error checking is needed here i think for nonetype that may be
        # passed in from prior steps

        phys_count = 0
        cdl_state = False
        year_state = None
        bnc_copies = 0

        for mms_id in book.analytics:
            for kdx, access in enumerate(book.analytics[mms_id]["Types"]):

                if access == "Physical":

                    # counting bnc copies and ensuring the rest are in Valley
                    # BIB
                    if book.analytics[mms_id]["Location"] == "Champinefu Lodge":
                        bnc_copies += get_int(book.analytics[mms_id]["Copies"][kdx])
                    if book.analytics[mms_id]["Location"] != "Valley BIB":
                        continue

                    # can remove if adding more physical numbered columns
                    if phys_count >= 2:
                        continue
                    df.loc[row, main[f"PrintMMSId{phys_count + 1}"]] = mms_id
                    df.loc[row, main[f"PrintLink{phys_count + 1}"]] = book.analytics[
                        mms_id
                    ]["Link"]
                    df.loc[row, main[f"PrintCopies{phys_count + 1}"]] = book.analytics[
                        mms_id
                    ]["Copies"][kdx]
                    phys_count += 1

                elif access == "Electronic":
                    df.loc[row, main["EbookMMSId"]] = mms_id
                    df.loc[row, main["EbookLink"]] = book.analytics[mms_id]["Link"]
                    df.loc[row, main["EbookUsers"]] = book.analytics[mms_id]["Users"][
                        kdx
                    ]
                    df.loc[row, main["EbookPlatform"]] = book.analytics[mms_id][
                        "Platform"
                    ]

                elif access == "Audiobook":
                    df.loc[row, main["AudioMMSId"]] = mms_id
                    df.loc[row, main["AudioLink"]] = book.analytics[mms_id]["Link"]

                if not cdl_state:
                    cdl_state = book.analytics[mms_id]["CDL"][kdx]

            if year_state is None:
                # maybe check for numbers marked as 0?
                year_state = book.analytics[mms_id]["Year"]

        if len(book.analytics) >= 1:
            df.loc[row, main["IsCDL"]] = cdl_state
            df.loc[row, main["Year"]] = year_state
            df.loc[row, main["BNCCopies"]] = bnc_copies

        for jdx in range(1, len(book.isbns) + 1):
            df.loc[row, main["ISBN"].replace("1", f"{jdx}")] = book.isbns[jdx - 1]

        campus_out = ""
        for num, jdx in enumerate(sorted(book.campuses)):
            if num != 0:
                campus_out += ", "
            campus_out += jdx
        df.loc[row, main["Campuses"]] = campus_out

        course_order = get_max_index(book.sec_size)
        for num, jdx in enumerate(course_order):
            df.loc[row, format[0].replace("$", f"{num + 1}")] = book.courses[jdx]
            for iter, kdx in enumerate(book.sections[jdx]):
                df.loc[row, get_replace_header(format[1], num + 1, iter + 1)] = kdx[0]
                df.loc[
                    row, get_replace_header(format[2], num + 1, iter + 1, "Instructor")
                ] = kdx[1]
                df.loc[
                    row, get_replace_header(format[2], num + 1, iter + 1, "Email")
                ] = kdx[2]
                df.loc[
                    row, get_replace_header(format[2], num + 1, iter + 1, "Enroll")
                ] = kdx[3]

    return df
