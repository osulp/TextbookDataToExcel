import pandas as pd

# from openpyxl.utils.dataframe import dataframe_to_rows


# C- Oregon State - Corvallis, DR-Ecampus-Dist Ed Intermediate,
# DZ-Ecampus-Distance Ed Internatl, DI-Ecampus-Distance Education-LD,
# DB-Ecampus-Distance Education-UD, Z-International Sites, L-LaGrande/EOU,
# N-Newport/HMSC, B-Oregon State - Cascades, PDX-Oregon State - Portland,
# H-Portland/OHSU
def get_enrollment_data(dir, instructor_dict={}):
    """Pulls all the necessary data out of the enrollment CSV file."""
    df = pd.read_csv(dir, skiprows=3)
    enrollment_dict = {}

    for idx, course in enumerate(df["COURSE_IDENTIFICATION"]):

        # course & section details
        section = df["OFFERING_NUMBER"][idx]
        campus = df["CAMPUS"][idx]
        # course_type = df['SCHEDULE_DESC'][idx]
        max_enroll = df["MAXIMUM_ENROLLMENT"][idx]

        if course not in enrollment_dict:
            enrollment_dict[f"{course}"] = {f"{section}": [max_enroll, campus]}
        elif section not in enrollment_dict[f"{course}"]:
            enrollment_dict[f"{course}"][f"{section}"] = [max_enroll, campus]
        else:
            print(
                "I don't think these cases exist (Multiple enrollments for course and section)"
            )

        # instructor things
        instructor = df["PRIMARY_INSTRUCTOR"][idx]
        email = df["INTERNET_ADDRESS"][idx]
        # inst_num = df['INSTRUCTOR_COUNT'][idx]

        if not pd.isna(email):
            instructor_dict[f"{instructor}"] = email

    return instructor_dict, enrollment_dict
