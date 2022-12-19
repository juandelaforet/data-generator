#!/usr/bin/python

"""
START OF IMPORT SECTION
"""

import sys
import os
import csv
import time
import datetime
import random
import copy
import logging
import ConfigParser
import json
import elasticsearch
import elasticsearch.helpers

"""
END OF IMPORT SECTION
"""

"""
VERSION : 1.4
AUTHOR  : John Smith
"""
CODE_VERSION = "1.4"
VERSION_DATE = "10/02/2018"
print ("\n\nVERSION = " + CODE_VERSION + "\n\nVERSION_DATE = " + VERSION_DATE + "\n\n")


"""
START OF CONSTANTS AND GLOBALS SECTION
"""

FILENAME_DATE_FORMAT = '%Y%m%d_%H%M%S'
EVENT_DATE_FORMAT = '%Y-%m-%dT%H:%M:%S.000Z'

CONFIG_FILENAME = './generate_dates.ini'

feed_headers = {"AD": ["event_time",
                       "badge_number",
                       "location",
                       "terminal",
                       "outcome",
                       "session_id",
                       "pki_details",
                       "event_type"],
                "DOORS": ["event_time",
                          "badge_number",
                          "location",
                          "door",
                          "outcome",
                          "event_type"],
                "PRINT": ["event_time",
                          "badge_number",
                          "location",
                          "printer",
                          "printer_type",
                          "document_name",
                          "pages",
                          "size",
                          "marking",
                          "session_id",
                          "event_type",
                          "outcome"],
                "ENDPOINTS": ["event_time",
                              "badge_number",
                              "location",
                              "terminal",
                              "device_id",
                              "device_name",
                              "device_type",
                              "serial_number",
                              "capacity",
                              "capacity_units",
                              "event_type",
                              "session_id",
                              "outcome"],
                "PHONES": ["event_time",
                           "badge_number",
                           "event_type",
                           "phone",
                           "from_number",
                           "to_number",
                           "duration",
                           "outcome"],
                "EMAILS": ["event_time",
                           "badge_number",
                           "event_type",
                           "subject",
                           "recipient_list",
                           "size",
                           "session_id",
                           "marking"],
                "CIRCUS": ["event_time",
                           "badge_number",
                           "event_type",
                           "session_id",
                           "outcome"],
                "STRUCTURE": ["event_time",
                              "badge_number",
                              "event_type",
                              "session_id",
                              "outcome"],
                "VOYAGER": ["event_time",
                            "badge_number",
                            "event_type",
                            "session_id",
                            "outcome"]}

elk_user_locations_dict = dict()
elk_user_terminals_dict = dict()
elk_user_phones_dict = dict()
users = dict()
terminals_list = list()
citrix_servers_list = list()
citrix_sessions_list = list()
phones_list = list()
locations_list = list()
email_bodies_list = list()
match_terms_list = list()
doors_list = list()
printers_list = list()
devices_list = list()
badge_list = list()
pki_details_list = list()
circus_operations_list = list()
structure_operations_list = list()
voyager_operations_list = list()


def read_config_value(config_file, section_name, option_name):
    """
    Does what it says on the tin really. Reads from a given config file and returns
    the value of an option in a particular section.
    This function is only out of sequence as it's used to set up various configuration
    "constants" later in the code.
    """

    try:
        Config = ConfigParser.ConfigParser()
        Config.read(config_file)

        for sects in Config.sections():
            if sects.upper() == section_name.upper():
                for options in Config.options(sects):
                    if options.upper() == option_name.upper():
                        return Config.get(sects, options)
    except Exception as e:
        logger.error('Problem reading configuration file')
        logger.debug(str(e))

    return ''


ref_data_directory = read_config_value(CONFIG_FILENAME,
                                       "DirectoryNames",
                                       "ReferenceDataDirectory")

output_directory = read_config_value(CONFIG_FILENAME,
                                     "DirectoryNames",
                                     "OutputDirectory")

ES_HOST = read_config_value(CONFIG_FILENAME,
                            "ElasticConfig",
                            "ConnectionDetails")

REQUEST_BODY = read_config_value(CONFIG_FILENAME,
                                 "ElasticConfig",
                                 "RequestBody")

max_recipients = int(read_config_value(CONFIG_FILENAME,
                                       "DataOptions",
                                       "MaxEmailRecipients"))

noise_factor = int(read_config_value(CONFIG_FILENAME,
                                     "DataOptions",
                                     "Noise"))

"""
END OF CONSTANTS AND GLOBALS SECTION
"""

"""
START OF GLOBAL FUNCTIONS ETC. SECTION
"""


def return_new_session_id():
    """
    Returns a new (randomly generated) session ID to link events for a single IT-based session.
    """

    return ("SESSION_ID_" + datetime.datetime.today().strftime(FILENAME_DATE_FORMAT) +
            "_" + str(random.randint(1000, 9999)))


"""
These may seem like a weird set of constants to declare however it means that the
values will be consistent throughout the code and will be checked by the interpreter
rather than relying on string comparison to hard-coded "strings"
"""
FAILURE = "FAILURE"
SUCCESS = "SUCCESS"
DENIED = "DENIED"


def RandomChance(chance_level):
    """
    This function returns a boolean True if a value is randomly chosen depending on the parameter
    supplied.
        "HIGH"   : 1 in 3
        "MEDIUM" : 1 in 20
        "LOW"    : 1 in 100
        "RARE"   : 1 in 10000
    """

    if chance_level.upper() == "HIGH":
        random_outcome = random.randint(1, 3)
        random_chooser = 2
    elif chance_level.upper() == "MEDIUM":
        random_outcome = random.randint(1, 20)
        random_chooser = 10
    elif chance_level.upper() == "LOW":
        random_outcome = random.randint(1, 100)
        random_chooser = 50
    elif chance_level.upper() == "RARE":
        random_outcome = random.randint(1, 10000)
        random_chooser = 5000
    else:
        return False

    if random_outcome == random_chooser:
        return True
    else:
        return False


def return_random_outcome():
    """
    Random outcomes for chance-related stuff.
    """

    if RandomChance("HIGH"):
        return SUCCESS
    else:
        if RandomChance("HIGH"):
            return FAILURE
        else:
            return DENIED


def return_success_or_failure():
    """
    Effectively a bit of a coin-toss for chance-related stuff.
    """

    if RandomChance("HIGH"):
        return SUCCESS
    else:
        return FAILURE


def return_random_marking():
    """
    Returns a random protective marking for documents, emails etc.
    """

    random_outcome = random.randint(1, 3)

    if (random_outcome == 1):
        return "OFFICIAL"
    elif (random_outcome == 2):
        return "SECRET"
    elif (random_outcome == 3):
        return "TOP SECRET"
    else:
        return "UNKNOWN"


def return_random_sentiment():
    """
    The rudimentary 'stub' ready for some production of sentiment-based content
    """

    random_sentiment = random.randint(1, 3)

    if (random_sentiment == 1):
        return "POSITIVE"
    elif (random_sentiment == 2):
        return "NEGATIVE"
    else:
        return "NEUTRAL"


def return_random_email_body_reference(sentiment):
    """
    return_random_email_body_reference(sentiment)
    """

    while True:

        random_entry = random.randint(0, len(email_bodies_list) - 1)

        if email_bodies_list[random_entry][0] == sentiment.upper():
            return email_bodies_list[random_entry]


def return_random_email_subject(sentiment):
    """
    return_random_email_subject(sentiment)
    """

    return "This is a " + sentiment.upper() + " email subject : ref=" + str(return_random_email_body_reference(sentiment.upper())[1])


def create_event_output(feed, event, event_time):
    """
    Creates a CSV output file for each event, given the feed name, event details and event_time.
    Uses the feed_headers dictionary to both provide the header values but also check that the
    correct number of values has been supplied in the event details.
    """

    try:
        if (event[0] is not None):
            today = datetime.datetime.today()

            """
            The minus one below takes into account the event_time field which is supplied as a separate parameter
            """

            if ((len(feed_headers[feed]) - 1) != len(event)):
                logger.error("Number of values does not equal number of columns for the feed!")
                return False

            filename = (output_directory + "/" +
                        feed + "/" +
                        feed + "_" +
                        today.strftime(FILENAME_DATE_FORMAT) + "_" +
                        str(random.randint(1, 999)) + ".csv")

            with open(filename, 'wb') as csvfile:
                csv.register_dialect('event_format', delimiter=',', quotechar='"', quoting=csv.QUOTE_NONNUMERIC)
                event_writer = csv.writer(csvfile, 'event_format')
                logger.debug("Creating CSV for feed " + str(feed))
                event_writer.writerow(feed_headers[feed])
                event_writer.writerow([event_time.strftime(EVENT_DATE_FORMAT)] + event)

            return True
        else:
            logger.error("No badge number supplied in event details!")
            return False

    except Exception as create_event_ex:
        logger.error("Exception raised in the create_event routine!")
        logger.debug(str(create_event_ex))


"""
END OF GLOBAL FUNCTIONS ETC. SECTION
"""


"""
START OF LOGGING SETUP SECTION
"""

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
handler = logging.FileHandler(read_config_value(CONFIG_FILENAME, "FileNames", "LogFile"))


if read_config_value(CONFIG_FILENAME, "DevelopmentOptions", "LoggingLevel").upper() == "INFO":
    handler.setLevel(logging.INFO)
elif read_config_value(CONFIG_FILENAME, "DevelopmentOptions", "LoggingLevel").upper() == "ERROR":
    handler.setLevel(logging.ERROR)
elif read_config_value(CONFIG_FILENAME, "DevelopmentOptions", "LoggingLevel").upper() == "CRITICAL":
    handler.setLevel(logging.CRITICAL)
else:
    handler.setLevel(logging.INFO)

formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)

"""
END OF LOGGING SETUP SECTION
"""


"""
START OF ELASTICSEARCH SETUP SECTION
"""

ES_host = read_config_value(CONFIG_FILENAME, "ElasticConfig", "ConnectionHost")
ES_port = int(read_config_value(CONFIG_FILENAME, "ElasticConfig", "ConnectionPort"))

"""
END OF ELASTICSEARCH SETUP SECTION
"""


"""
START OF CLASSES DEFINITION
"""


class Person:
    """
    Definition of the Person class.
    """

    def __init__(self, first_name, middle_names, surname):
        """
        The Person Class constructor.
        """
        self.__first_name = first_name
        self.__middle_names = middle_names
        self.__surname = surname

    def setDateOfBirth(self, birth_date):
        """
        Setter method for a Person's data of birth.
        """
        self.__birth_date = birth_date

    def getFirstName(self):
        """
        getFirstName(self)
        """
        return self.__first_name

    def displayDetails(self):
        """
        Display method for a Person's data.
        """
        logger.debug("First Name   : " + str(self.__first_name))
        logger.debug("Middle Names : " + str(self.__middle_names))
        logger.debug("Surname      : " + str(self.__surname))

    def setSmoker(self):
        """
        Set the flag to indicate that this person is a smoker (for pattern of life purposes).
        """
        self.__smoker = True

    def setNonSmoker(self):
        """
        Set the flag to indicate that this person is a non-smoker (for pattern of life purposes).
        """
        self.__smoker = False

    def getSmoker(self):
        """
        Return the flag to indicate whether this person is a smoker or not (for pattern of life purposes).
        """
        return self.__smoker


class Employee(Person):
    """
    Base class for all employees
    """

    def __init__(self, badge_number, first_name, middle_names, surname):
        """
        The Employee Class constructor.
        """

        Person.__init__(self, first_name, middle_names, surname)

        self.__badge_number = badge_number
        self.__in_building = False
        self.__logged_in = False
        self.__logged_into_phone = False
        self.__logged_into_circus = False
        self.__logged_into_structure = False
        self.__logged_into_voyager = False
        self.__can_login_circus = False
        self.__can_login_structure = False
        self.__can_login_voyager = False
        self.__team_name = None
        self.__joined_team = None
        self.__team_history = list()
        self.__main_location = None
        self.__current_location = None
        self.__current_terminal = None
        self.__current_phone = None
        self.__phone_number = None
        self.__pki_details = None
        self.__current_session_id = None

    def setCanLoginCircus(self):
        """
        setCanLoginCircus(self)
        """

        self.__can_login_circus = True

    def setCanLoginStructure(self):
        """
        setCanLoginStructure(self)
        """

        self.__can_login_structure = True

    def setCanLoginVoyager(self):
        """
        setCanLoginVoyager(self)
        """

        self.__can_login_voyager = True

    def getCanLoginCircus(self):
        """
        getCanLoginCircus(self)
        """

        return self.__can_login_circus

    def getCanLoginStructure(self):
        """
        getCanLoginStructure(self)
        """

        return self.__can_login_structure

    def getCanLoginVoyager(self):
        """
        getCanLoginVoyager(self)
        """

        return self.__can_login_voyager

    def hasCurrentSession(self):
        """
        hasCurrentSession(self)
        """

        if self.__current_session_id is None:
            return False
        else:
            return True

    def setSessionId(self):
        """
        setSessionId(self)
        """
        if self.__current_session_id is not None:
            logger.info("Sessing session ID when one is already set??")

        self.__current_session_id = return_new_session_id()

        return self.__current_session_id

    def getSessionId(self):
        """
        getSessionId(self)
        """

        return self.__current_session_id

    def isLoggedIntoPhone(self):
        """
        isLoggedIntoPhone(self)
        """

        return self.__logged_into_phone

    def isInBuilding(self):
        """
        isInBuilding(self)
        """

        return self.__in_building

    def isLoggedIn(self):
        """
        isLoggedIn(self)
        """

        return self.__logged_in

    def isLoggedIntoCircus(self):
        """
        isLoggedIntoCircus(self)
        """

        return self.__logged_into_circus

    def loginPhone(self, phone, event_time):
        """
        loginPhone(self, phone, event_time)
        """

        self.__current_phone = phone
        self.__logged_into_phone = True
        phone.loginPhone(self.__badge_number, self.__phone_number, event_time)

    def logoutPhone(self, event_time):
        """
        logoutPhone(self, event_time)
        """

        self.__current_phone.logoutPhone(event_time)
        self.__current_phone = None
        self.__logged_into_phone = False

    def getPhone(self):
        """
        getPhone(self)
        """

        return self.__current_phone

    def checkPKIPermissions(self, application):
        """
        checkPKIPermissions(self, application)
        """

        try:
            if application.upper() == "CIRCUS":
                return self.getCanLoginCircus()
            if application.upper() == "VOYAGER":
                return self.getCanLoginVoyager()
            if application.upper() == "STRUCTURE":
                return self.getCanLoginStructure()
        except Exception as cPP_ex:
            logger.error("Exception raised in checkPKIPermissions")
            logger.debug(str(cPP_ex))

        return False

    def loginCircus(self, outcome, event_time):
        """
        loginCircus(self, outcome, event_time)
        """

        if outcome == SUCCESS:
            self.__logged_into_circus = True

        if self.__current_session_id is None:
            current_session = "N/A"
        else:
            current_session = self.__current_session_id

        create_event_output("CIRCUS", [self.__badge_number,
                                       "LOGIN",
                                       current_session,
                                       outcome], event_time)

    def performCircusOperation(self, operation, outcome, event_time):
        """
        performCircusOperation(self, operation, outcome, event_time)
        """

        create_event_output("CIRCUS", [self.__badge_number,
                                       operation,
                                       self.__current_session_id,
                                       outcome], event_time)

    def logoutCircus(self, event_time):
        """
        logoutCircus(self, event_time)
        """

        self.__logged_into_circus = False

        if self.__current_session_id is None:
            current_session = "N/A"
        else:
            current_session = self.__current_session_id

        create_event_output("CIRCUS", [self.__badge_number,
                                       "LOGOUT",
                                       current_session,
                                       SUCCESS], event_time)

    def isLoggedIntoStructure(self):
        """
        isLoggedIntoStructure(self)
        """

        return self.__logged_into_structure

    def loginStructure(self, outcome, event_time):
        """
        loginStructure(self, outcome, event_time)
        """

        if outcome == SUCCESS:
            self.__logged_into_structure = True

        if self.__current_session_id is None:
            current_session = "N/A"
        else:
            current_session = self.__current_session_id

        create_event_output("STRUCTURE", [self.__badge_number,
                                          "LOGIN",
                                          current_session,
                                          outcome], event_time)

    def performStructureOperation(self, operation, outcome, event_time):
        """
        performStructureOperation(self, operation, outcome, event_time)
        """

        create_event_output("STRUCTURE", [self.__badge_number,
                                          operation,
                                          self.__current_session_id,
                                          outcome], event_time)

    def logoutStructure(self, event_time):
        """
        logoutStructure(self, event_time)
        """

        self.__logged_into_structure = False

        if self.__current_session_id is None:
            current_session = "N/A"
        else:
            current_session = self.__current_session_id

        create_event_output("STRUCTURE", [self.__badge_number,
                                          "LOGOUT",
                                          current_session,
                                          SUCCESS], event_time)

    def isLoggedIntoVoyager(self):
        """
        isLoggedIntoVoyager(self)
        """

        return self.__logged_into_voyager

    def loginVoyager(self, outcome, event_time):
        """
        loginVoyager(self, outcome, event_time)
        """

        if outcome == SUCCESS:
            self.__logged_into_voyager = True

        if self.__current_session_id is None:
            current_session = "N/A"
        else:
            current_session = self.__current_session_id

        create_event_output("VOYAGER", [self.__badge_number,
                                        "LOGIN",
                                        current_session,
                                        outcome], event_time)

    def performVoyagerOperation(self, operation, outcome, event_time):
        """
        performVoyagerOperation(self, operation, outcome, event_time)
        """

        create_event_output("VOYAGER", [self.__badge_number,
                                        operation,
                                        self.__current_session_id,
                                        outcome], event_time)

    def logoutVoyager(self, event_time):
        """
        logoutVoyager(self, event_time)
        """

        self.__logged_into_voyager = False

        if self.__current_session_id is None:
            current_session = "N/A"
        else:
            current_session = self.__current_session_id

        create_event_output("VOYAGER", [self.__badge_number,
                                        "LOGOUT",
                                        current_session,
                                        SUCCESS], event_time)

    def assignBadge(self, badge_number):
        """
        assignBadge(self, badge_number)
        """

        self.__badge_number = badge_number

    def assignTeam(self, team_name, event_time):
        """
        assignTeam(self, team_name, event_time)
        """

        if self.__team_name is not None:
            self.__team_list.append(self.__team_name, self.__joined_team, event_time)

        self.__team_name = team_name

        if event_time is not None:
            self.__joined_team = event_time

    def getCurrentTeam(self):
        """
        getCurrentTeam(self)
        """

        return self.__team_name

    def assignRiskScore(self, risk_score):
        """
        Set the risk score for an Employee
        """

        self.__risk_score = risk_score

    def getCurrentTerminal(self):
        """
        Return the current terminal in use by an Employee
        """

        return self.__current_terminal

    def getRiskScore(self):
        """
        Return the current risk score for an Employee
        """

        return self.__risk_score

    def setCurrentLocation(self, location):
        """
        setCurrentLocation(self, location)
        """

        self.__current_location = location
        self.__in_building = True

    def getCurrentLocation(self):
        """
        getCurrentLocation(self)
        """

        return self.__current_location

    def setCurrentTerminal(self, terminal):
        """
        setCurrentTerminal(self, terminal)
        """

        if terminal is not None:
            logger.debug("Setting to terminal : " + str(terminal.getTerminalName()))
        else:
            logger.debug("Setting to NULL terminal?!?")

        self.__current_terminal = terminal
        self.__logged_in = True

    def setMainLocation(self, main_location):
        """
        setMainLocation(self, main_location)
        """

        self.__main_location = main_location

    def getMainLocation(self):
        """
        getMainLocation(self)
        """

        return self.__main_location

    def setJobTitle(self, job_title):
        """
        setJobTitle(self, job_title)
        """

        self.__job_title = job_title

    def getJobTitle(self):
        """
        getJobTitle(self)
        """

        return self.__job_title

    def setEmailAddress(self, email):
        """
        setEmailAddress(self, email)
        """

        self.__email = email

    def getEmailAddress(self):
        """
        getEmailAddress(self)
        """

        return self.__email

    def sendEmail(self, event_time, recipient_list):
        """
        sendEmail(self, event_time, recipient_list)
        """

        try:
            create_event_output("EMAILS", [self.__badge_number,
                                           "EMAIL SENT",
                                           return_random_email_subject(return_random_sentiment()),
                                           recipient_list,
                                           random.randint(1, 50000),
                                           self.__current_session_id,
                                           return_random_marking()], event_time)
        except Exception as send_email_ex:
            logger.error("Exception raised in sendEmail method!")
            logger.info(str(send_email_ex))

    def createPhonecall(self, event_time, destination_phone):
        """
        createPhonecall(self, event_time, destination_phone)
        """

        try:
            random_call_duration = random.randint(1, 200)
    
            logger.info("Creating event in PHONES feed for user " +
                        str(self.__badge_number) +
                        " outgoing call from " + str(self.__phone_number) +
                        " to " + str(destination_phone.getCurrentNumber()))
    
            create_event_output("PHONES", [self.__badge_number,
                                           "OUTGOING CALL",
                                           self.__current_phone,
                                           self.__phone_number,
                                           destination_phone.getCurrentNumber(),
                                           random_call_duration,
                                           SUCCESS], event_time)
    
            logger.info("Creating corresponding event in PHONES feed for user " +
                        str(self.__badge_number) +
                        " incoming call to " +
                        str(destination_phone.getCurrentNumber()) +
                        " from " + str(self.__phone_number))
    
            create_event_output("PHONES", [self.__badge_number,
                                           "INCOMING CALL",
                                           destination_phone.getPhoneName(),
                                           destination_phone.getCurrentNumber(),
                                           self.__phone_number,
                                           random_call_duration,
                                           SUCCESS], event_time)
        except Exception as create_phonecall_ex:
            logger.error("Exception raised in createPhonecall method!")
            logger.info(str(create_phonecall_ex))

    def setPhoneNumber(self, phone_number):
        """
        setPhoneNumber(self, phone_number)
        """

        self.__phone_number = phone_number

    def getPhoneNumber(self):
        """
        getPhoneNumber(self)
        """

        return self.__phone_number

    def getBadgeNumber(self):
        """
        getBadgeNumber(self)
        """

        return self.__badge_number

    def getPKIDetails(self):
        """
        getPKIDetails(self)
        """

        return self.__pki_details

    def setPKIDetails(self, pki_details):
        """
        setPKIDetails(self, pki_details)
        """

        self.__pki_details = pki_details

    def setPatternOfLife(self, pattern_of_life):
        """
        setPatternOfLife(self, pattern_of_life)
        """

        self.__pattern_of_life = pattern_of_life

    def getPatternOfLife(self):
        """
        getPatternOfLife(self)
        """

        return self.__pattern_of_life

    def increaseRiskScore(self):
        """
        Increase the current risk score for an Employee by one
        """

        self.__risk_score += 1

        return self.__risk_score

    def decreaseRiskScore(self):
        """
        Decrease the current risk score for an Employee by one
        """

        if self.__risk_score >= 1:
            self.__risk_score -= 1
        else:
            logger.info("Attempt made to decrease Employee's risk score below zero.")

        return self.__risk_score

    def displayDetails(self):
        """
        Display method for an Employee's data.
        """

        logger.debug("Employee Details :-")
        logger.debug("Badge Number : " + str(self.__badge_number))
        """
        Need to identify the correct method of accessing the superclass member variables here.
        I'll do it eventually honest! It's probably Person.something or Super.something...

        logger.debug("First Name   : " + str(self.__first_name))
        logger.debug("Middle Names : " + str(self.__middle_names))
        logger.debug("Surname      : " + str(self.Person.__surname))
        """
        logger.debug("User in building? : " + str(self.__in_building))
        logger.debug("User logged in? : " + str(self.__logged_in))
        logger.debug("Logged into phone : " + str(self.__logged_into_phone))
        logger.debug("Logged into CIRCUS : " + str(self.__logged_into_circus))
        logger.debug("Logged into STRUCTURE : " + str(self.__logged_into_structure))
        logger.debug("Logged into VOYAGER : " + str(self.__logged_into_voyager))
        logger.debug("Main Location : " + str(self.__main_location))
        logger.debug("Current Location : " + str(self.__current_location))

        if self.__current_terminal is not None:
            logger.debug("Current Terminal : " + str(self.__current_terminal.getTerminalName()))
        else:
            logger.debug("Not logged into a terminal!?!")
            logger.debug(str(self.__current_terminal))

        if self.__current_phone is not None:
            logger.debug("Current phone : " + str(self.__current_phone))
        else:
            logger.info("No current phone.")

        logger.debug("Phone number : " + str(self.__phone_number))
        logger.debug("PKI details : " + str(self.__pki_details))

        if self.__team_name is not None:
            logger.debug("Team         : " + str(self.__team_name))
            logger.debug("Joined Team  : " + str(self.__joined_team))

    def swipeInEmployee(self, office, door, outcome, event_time):
        """
        Swipe in to an office through a specific door and with the supplied outcome
        e.g. Employee 123 swipes in at HQ Main Entrance and the outcome was a failed attempt

        Respond the same if the Office has door data apart from generating an event.
        """

        has_door_data = office_door_data_available(office)

        if (outcome.upper() == SUCCESS):
            self.__current_location = office
            self.__in_building = True

        if has_door_data:
            create_event_output("DOORS", [self.__badge_number,
                                          office,
                                          door,
                                          outcome,
                                          "SWIPEIN"], event_time)

    def swipeOutEmployee(self, office, door, outcome, event_time):
        """
        Swipe out of an office through a specific door and with the supplied outcome
        e.g. Employee 123 swipes out through HQ Main Entrance and the outcome was a successful attempt

        Respond the same if the Office has door data apart from generating an event.
        """

        has_door_data = office_door_data_available(office)

        if (outcome.upper() == SUCCESS):
            self.__current_location = None
            self.__in_building = False

        if has_door_data:
            create_event_output("DOORS", [self.__badge_number,
                                          office,
                                          door,
                                          outcome,
                                          "SWIPEOUT"], event_time)

    def loginEmployee(self, office, terminal, outcome, pki_details, event_time):
        """
        Login to a specified Terminal at a specified office and with the supplied outcome
        e.g. Employee 123 logs in at HQ Terminal HQ-1-1 and the outcome was a successful login
        """

        if outcome.upper() == SUCCESS:
            if terminal.getTerminalType() == "THIN":
                local_citrix_server = return_citrix_server(office)
                new_citrix_session = return_citrix_session(local_citrix_server)

                if new_citrix_session is not None:
                    new_citrix_session.assignSession(local_citrix_server, self.__badge_number, terminal)
                    self.__current_terminal = terminal
                    self.__logged_in = True
                    new_session_id = self.setSessionId()

                    create_event_output("AD", [self.__badge_number,
                                               office,
                                               terminal.getTerminalName(),
                                               outcome,
                                               new_session_id,
                                               pki_details,
                                               "LOGIN"], event_time)
                else:
                    create_event_output("AD", [self.__badge_number,
                                               office,
                                               terminal.getTerminalName(),
                                               FAILURE,
                                               "N/A",
                                               pki_details,
                                               "LOGIN"], event_time)
            else:
                self.__current_terminal = terminal
                self.__logged_in = True

                new_session_id = self.setSessionId()

                create_event_output("AD", [self.__badge_number,
                                           office,
                                           terminal.getTerminalName(),
                                           outcome,
                                           new_session_id,
                                           pki_details,
                                           "LOGIN"], event_time)
        else:
            # Not sure if technically these next two are right or not...?
            self.__current_terminal = None
            self.__logged_in = False
            self.__current_session_id = None

            create_event_output("AD", [self.__badge_number,
                                       office,
                                       terminal.getTerminalName(),
                                       outcome,
                                       "N/A",
                                       pki_details,
                                       "LOGIN"], event_time)

    def logoutEmployee(self, office, terminal, outcome, event_time):
        """
        Logout of a specified Terminal at a specified office and with the supplied outcome
        e.g. Employee 123 logs out of Terminal HQ-1-1 at HQ and the outcome was a successful logout
        """
        try:
            current_terminal_name = terminal.getTerminalName()

            if outcome.upper() == SUCCESS:
                if terminal.getTerminalType() == "THIN":
                    release_citrix_session(self.__badge_number, office, terminal)
                self.__current_terminal = None
                self.__logged_in = False
                self.__current_session_id = None

            if self.__current_session_id is None:
                current_session = "N/A"
            else:
                current_session = self.__current_session_id

            create_event_output("AD", [self.__badge_number,
                                       office,
                                       current_terminal_name,
                                       outcome,
                                       current_session,
                                       self.__pki_details,
                                       "LOGOUT"], event_time)
        except Exception as logout_emp_ex:
            logger.error("Exception raised in logoutEmployee")
            logger.debug(str(logout_emp_ex))


class Location:
    """
    The base class for a location
    """

    def __init__(self, address, latitude, longitude):
        """
        The Location Class constructor.
        """
        self.__address = address
        self.__latitude = latitude
        self.__longitude = longitude
        logger.debug("Setting lat/long to " + str(self.__latitude) + "," + str(self.__longitude))

    def setLatLong(self, latitude, longitude):
        """
        setLatLong(self, latitude, longitude)
        """

        self.__latitude = latitude
        self.__longitude = longitude

    def displayDetails(self):
        """
        Display method for a Location's details.
        """

        logger.debug("Location Details :-")
        logger.debug("Location Address : " + str(self.__address))


class Office(Location):
    """
    Class of an office location
    """

    def __init__(self, office_name, has_door_data, latitude, longitude):
        """
        The Office Class constructor.
        """

        Location.__init__(self, None, latitude, longitude)

        self.__office_name = office_name

        if has_door_data.upper() == "TRUE":
            self.__has_door_data = True
        else:
            self.__has_door_data = False

    def hasDoorData(self):
        """
        hasDoorData(self)
        """

        return self.__has_door_data

    def getLocationName(self):
        """
        getLocationName(self)
        """

        return self.__office_name

    def displayDetails(self):
        """
        Display method for an Office's details.
        """

        logger.debug("Office Details :-")
        logger.debug("Office Name      : " + str(self.__office_name))
        logger.debug("Location Address : " + str(self.__address))

        if self.__has_door_data:
            logger.debug("This office does have door log information")
        else:
            logger.debug("This office does NOT have door log information")

    def massExodous(self):
        """
        Evacuate a building without any swipe out events or logout events.
        """

        logger.debug("Evacuating everyone from office " + str(self.__office))


class CitrixServer:
    """
    The base class of a CITRIX Server
    """

    def __init__(self, server_name, office, max_sessions):
        """
        __init__(self, server_name, office, max_sessions)
        """

        self.__server_name = server_name
        self.__office = office
        self.__max_sessions = int(max_sessions)
        self.__session_list = list()

    def getAvailableSessions(self):
        """
        getAvailableSessions(self)
        """

        return (self.__max_sessions - len(self.__session_list))

    def getServerName(self):
        """
        getServerName(self)
        """

        return self.__server_name

    def getLocation(self):
        """
        getLocation(self)
        """

        return self.__office

    def assignSessionToServer(self, session_name, badge_number, terminal):
        """
        assignSessionToServer(self, session_name, badge_number, terminal)
        """

        self.__session_list.append([session_name, badge_number, terminal.getTerminalName()])

    def getAllocatedSessionsList(self):
        """
        getAllocatedSessionsList(self)
        """

        return self.__session_list

    def releaseSession(self, session_name):
        """
        releaseSession(self, session_name)
        """

        logger.debug("In CITRIX server release session method")

        for item, sessions in enumerate(self.__session_list):
            if sessions[0] == session_name:
                logger.debug("Length of session queue before deletion = " + str(len(self.__session_list)))
                del self.__session_list[item]
                return_citrix_session_by_name(session_name).releaseSession()
                logger.debug("Length of session queue after deletion = " + str(len(self.__session_list)))


class CitrixSession:
    """
    The base class of a CITRIX Session
    """

    def __init__(self, session_name, office, server_name):
        """
        __init__(self, session_name, office, server_name)
        """

        self.__server_name = server_name
        self.__session_name = session_name
        self.__assigned_user = None
        self.__office = office
        self.__assigned = False

    def getSessionName(self):
        """
        getSessionName(self)
        """

        return self.__session_name

    def getAssignedTerminal(self):
        """
        getAssignedTerminal(self)
        """

        return self.__assigned_terminal

    def getServerName(self):
        """
        getServerName(self)
        """

        return self.__server_name

    def getLocation(self):
        """
        getLocation(self)
        """

        return self.__office

    def isSessionAssigned(self):
        """
        isSessionAssigned(self)
        """

        return self.__assigned

    def assignSession(self, citrix_server, badge_number, terminal):
        """
        assignSession(self, citrix_server, badge_number, terminal)
        """

        citrix_server.assignSessionToServer(self.__session_name, badge_number, terminal)

        self.__assigned_user = badge_number
        self.__assigned_terminal = terminal
        self.__assigned = True

        return self.__session_name

    def releaseSession(self):
        """
        releaseSession(self)
        """

        self.__assigned_user = None
        self.__assigned_terminal = None
        self.__assigned = False


class Terminal:
    """
    The base class of a terminal
    terminal,location,type,ip_address,fqdn
    """

    def __init__(self, terminal_name, terminal_type, office, ip_address, fqdn):
        """
        __init__(self, terminal_name, terminal_type, office, ip_address, fqdn)
        """

        self.__terminal_name = terminal_name
        self.__terminal_type = terminal_type
        self.__office = office
        self.__ip_address = ip_address
        self.__fqdn = fqdn

    def setFQDN(self, fqdn):
        """
        setFQDN(self, fqdn)

        Set the FQDN of a network asset (Fully Qualified Domain Name)
        """
        self.__fqdn = fqdn

    def getFQDN(self):
        """
        getFQDN(self)

        Get the FQDN of a network asset (Fully Qualified Domain Name)
        """

        return self.__fqdn

    def setIPAddress(self, ip_address):
        """
        setIPAddress(self, ip_address)

        Set the IP Address of a network asset
        """

        self.__ip_address = ip_address

    def getIPAddress(self):
        """
        setIPAddress(self, ip_address)

        Get the IP Address of a network asset
        """

        return self.__ip_address

    def getTerminalType(self):
        """
        getTerminalType(self)
        """

        return self.__terminal_type

    def getTerminalName(self):
        """
        getTerminalName(self)
        """

        return self.__terminal_name

    def getLocation(self):
        """
        getLocation(self)
        """

        return self.__office

    def displayDetails(self):
        """
        Display method for a Terminal's details.
        """

        logger.debug("Terminal Details :-")
        logger.debug("Terminal Name : " + str(self.__terminal_name))
        logger.debug("Terminal Type : " + str(self.__terminal_type))
        logger.debug("Office        : " + str(self.__office))

        if self.__terminal_type == "THICK":
            logger.debug("IP Address    : " + str(self.__ip_address))
            logger.debug("FQDN          : " + str(self.__fqdn))


class Phone:
    """
    The base class of a phone
    """

    def __init__(self, phone_name, phone_type, office):
        """
        __init__(self, phone_name, phone_type, office)
        """
        self.__phone_name = phone_name
        self.__phone_type = phone_type
        self.__office = office
        self.__is_logged_in = False
        self.__current_user = None
        self.__current_phone_number = None

    def getPhoneType(self):
        """
        getPhoneType(self)
        """

        return self.__phone_type

    def getPhoneName(self):
        """
        getPhoneName(self)
        """

        return self.__phone_name

    def getCurrentNumber(self):
        """
        getCurrentNumber(self)
        """

        return self.__current_phone_number

    def loginPhone(self, badge_number, phone_number, event_time):
        """
        loginPhone(self, badge_number, phone_number, event_time)
        """

        try:
            self.__current_user = badge_number
            self.__is_logged_in = True
            self.__current_phone_number = phone_number
    
            logger.info("Generating phone login for phone " + self.__phone_name +
                        " as number " + self.__current_phone_number +
                        " by user " + self.__current_user)
    
            logger.debug("Creating LOGIN event in PHONES feed")
    
            create_event_output("PHONES", [badge_number,
                                           "LOGIN",
                                           self.__phone_name,
                                           phone_number,
                                           "N/A",
                                           0,
                                           SUCCESS], event_time)

        except Exception as login_phone_ex:
            logger.error("Exception raised in loginPhone method!")
            logger.info(str(login_phone_ex))

    def logoutPhone(self, event_time):
        """
        logoutPhone(self, event_time)
        """

        try:
            logger.info("Generating phone logout event for phone " + self.__phone_name +
                        " currently logged in as number " + self.__current_phone_number +
                        " from user " + self.__current_user)
    
            logger.debug("Creating LOGOUT event in PHONES feed")
    
            create_event_output("PHONES", [self.__current_user,
                                           "LOGOUT",
                                           self.__phone_name,
                                           self.__current_phone_number,
                                           "N/A",
                                           0,
                                           SUCCESS], event_time)
            self.__current_user = None
            self.__is_logged_in = False
            self.__current_phone_number = None

        except Exception as logout_phone_ex:
            logger.error("Exception raised in logoutPhone method!")
            logger.info(str(logout_phone_ex))

    def isLoggedIn(self):
        """
        isLoggedIn(self)
        """

        return self.__is_logged_in

    def getLocation(self):
        """
        getLocation(self)
        """

        return self.__office

    def displayDetails(self):
        """
        Display method for a Phone's details.
        """

        logger.debug("Phone Details :-")
        logger.debug("Phone Name   : " + str(self.__phone_name))
        logger.debug("Phone Type   : " + str(self.__phone_type))
        logger.debug("Office       : " + str(self.__office))

        if self.__is_logged_in:
            logger.debug("Current User : " + str(self.__current_user))
        else:
            logger.debug("Phone is currently not in use.")


class Asset:
    """
    The base class for an asset
    """

    def __init__(self, asset_tag, owner):
        """
        __init__(self, asset_tag, owner)
        """

        self.__asset_tag = asset_tag
        self.__owner = owner
        self.__has_owner = False

    def assignAssetTag(self, asset_tag):
        """
        assignAssetTag(self, asset_tag)
        """

        self.__asset_tag = asset_tag

    def assignOwner(self, owner):
        """
        assignOwner(self, owner)
        """

        self.__owner = owner
        self.__has_owner = True

    def hasOwner(self):
        """
        hasOwner(self)
        """

        return self.__has_owner

    def getOwner(self):
        """
        getOwner(self)
        """

        return self.__owner

    def displayDetails(self):
        """
        Display method for an Asset's details.
        """

        logger.debug("Asset Details :-")
        logger.debug("Asset Tag : " + str(self.__asset_tag))

        if self.__has_owner:
            logger.debug("Owner     : " + str(self.__owner))
        else:
            logger.debug("Device has no assigned owner.")


class Device(Asset):
    """
    The base class for devices
    """

    def __init__(self, device_id, device_name, device_type, serial_number, asset_tag, capacity, capacity_units):
        """
        __init__(self, device_id, device_name, device_type, serial_number, asset_tag, capacity, capacity_units)
        """

        Asset.__init__(self, asset_tag, None)

        self.__device_id = device_id
        self.__device_name = device_name
        self.__device_type = device_type
        self.__serial_number = serial_number
        self.__asset_tag = asset_tag
        self.__capacity = capacity
        self.__capacity_units = capacity_units
        self.__plugged_in = False
        self.__owner = None

    def getOwner(self):
        """
        getOwner(self)
        """

        return self.__owner

    def isPluggedIn(self):
        """
        isPluggedIn(self)
        """

        return self.__plugged_in

    def getDeviceType(self):
        """
        getDeviceType(self)
        """

        return self.__device_type

    def getDeviceName(self):
        """
        getDeviceName(self)
        """

        return self.__device_name

    def setDeviceName(self, device_name):
        """
        setDeviceName(self, device_name)
        """

        self.__device_name = device_name

        return self.__device_name

    def setCapacity(self, capacity):
        """
        setCapacity(self, capacity)
        """

        self.__capacity = capacity

    def getCapacity(self):
        """
        getCapacity(self)
        """

        return [self.__capacity, self.__capacity_units]

    def displayDetails(self):
        """
        Display method for a Device's details.
        """

        logger.debug("Device Details :-")
        logger.debug("Device ID        : " + str(self.__device_id))
        logger.debug("Device Name      : " + str(self.__device_name))
        logger.debug("Device Type      : " + str(self.__device_type))
        logger.debug("Serial No.       : " + str(self.__serial_number))
        logger.debug("Asset Tag        : " + str(self.__asset_tag))
        logger.debug("Capacity         : " + str(self.__capacity))
        logger.debug("Capacity (Units) : " + str(self.__capacity_units))

        if self.__has_owner:
            logger.debug("Owner            : " + str(self.__owner))
        else:
            logger.debug("Device has no assigned owner.")

    def plugIn(self, badge_number, office, terminal, outcome, event_time):
        """
        Plug a device into the network.
        """

        try:
            if outcome == SUCCESS:
                logger.info("Device " + str(self.__device_name) +
                            " has been plugged into the network by user " + str(badge_number))
                self.__plugged_in = True
            else:
                logger.info("Device " + str(self.__device_name) +
                            " has been plugged into the network by user " + str(badge_number) +
                            ", but the device was blocked!")

            if (int(badge_number) < 1000):
                session_id = users[badge_number].getSessionId()
            else:
                session_id = "N/A"
    
            create_event_output("ENDPOINTS", [badge_number,
                                              office,
                                              terminal.getTerminalName(),
                                              self.__device_id,
                                              self.__device_name,
                                              self.__device_type,
                                              self.__serial_number,
                                              self.__capacity,
                                              self.__capacity_units,
                                              "DEVICE PLUGGED IN",
                                              session_id,
                                              outcome], event_time)
        except Exception as plugin_ex:
            logger.error("Exception raised in device plug-in method!")
            logger.info(str(plugin_ex))

    def unPlug(self, badge_number, office, terminal, event_time):
        """
        Unplug a device from the network.
        """

        try:
            logger.info("Device " + str(self.__device_name) +
                        " has been unplugged from the network by user " + str(badge_number))

            self.__plugged_in = False

            if terminal is None:
                logger.debug("terminal_name is currently set to 'None'...")

            if isinstance(terminal, Terminal):
                terminal.getTerminalName()
            else:
                terminal_name = "Unknown"

            if (int(badge_number) < 1000):
                session_id = users[badge_number].getSessionId()
            else:
                session_id = "N/A"
    
            create_event_output("ENDPOINTS", [badge_number,
                                              office,
                                              terminal.getTerminalName(),
                                              self.__device_id,
                                              self.__device_name,
                                              self.__device_type,
                                              self.__serial_number,
                                              self.__capacity,
                                              self.__capacity_units,
                                              "DEVICE UNPLUGGED",
                                              session_id,
                                              SUCCESS], event_time)

        except Exception as unplug_device_ex:
            logger.error("Exception raised in device unplug method of the Device class!")
            logger.debug(str(unplug_device_ex))


class Door:
    """
    The base class for a door
    """

    def __init__(self, office, door_name, door_type):
        """
        __init__(self, office, door_name, door_type)
        """

        self.__office = office
        self.__door_name = door_name
        self.__door_type = door_type

    def getLocation(self):
        """
        getLocation(self)
        """

        return self.__office

    def getDoorName(self):
        """
        getDoorName(self)
        """

        return self.__door_name

    def displayDetails(self):
        """
        Display method for an office Door's details.
        """

        logger.debug("Door Details :-")
        logger.debug("Office    : " + str(self.__office))
        logger.debug("Door Name : " + str(self.__door_name))
        logger.debug("Door Type : " + str(self.__door_type))


class Floor:
    """
    The base class for a floor
    """

    def __init__(self, floor_name):
        """
        __init__(self, floor_name)
        """

        self.__floor_name = floor_name

    def displayDetails(self):
        """
        Display method for an office Floor's details.
        """

        logger.debug("Floor Details :-")
        logger.debug("Floor Name : " + str(self.__floor_name))


class UseCaseStep:
    """
    The base class for a use-case step
    """

    def __init__(self, step_number, action):
        """
        __init__(self, step_number, action)
        """

        self.__use_case_step_number = step_number
        self.__use_case_step_action = action
        self.__action_time = None
        self.__interval_in_minutes = 1

    def getActionTime(self):
        """
        getActionTime(self)
        """

        return self.__action_time

    def setActionTime(self, action_time):
        """
        setActionTime(self, action_time)
        """

        self.__action_time = action_time

    def setInterval(self, interval_in_minutes):
        """
        setInterval(self, interval_in_minutes)
        """

        self.__interval_in_minutes = interval_in_minutes

    def getInterval(self):
        """
        getInterval(self)
        """

        return self.__interval_in_minutes

    def getStepNumber(self):
        """
        getStepNumber(self)
        """

        return self.__use_case_step_number

    def getStepAction(self):
        """
        getStepAction(self)
        """

        return self.__use_case_step_action

    def displayDetails(self):
        """
        displayDetails(self)
        """

        logger.info("Step Number : " + str(self.__use_case_step_number))
        logger.info("Action      : " + str(self.__use_case_step_action))

        if self.__action_time is not None:
            logger.info("Action Time : " + str(self.__action_time))


class UseCase:
    """
    The base class for a use-case
    """

    def __init__(self, use_case_name):
        """
        __init__(self, use_case_name)
        """

        self.__use_case_name = use_case_name
        self.__use_case_step_list = list()
        self.__current_step = None
        self.__is_active = False
        self.__start_time = None
        self.__interval_in_minutes = 1
        self.__use_case_user = None
        self.__terminal = None
        self.__device = None
        self.__location = None
        self.__PKI_details = None
        self.__is_test_user = False

    def getUser(self):
        """
        getUser(self)
        """

        return self.__use_case_user

    def setUser(self, use_case_user):
        """
        setUser(self, use_case_user)
        """

        self.__use_case_user = use_case_user

    def getPKIDetails(self):
        """
        getPKIDetails(self)
        """

        return self.__PKI_details

    def setPKIDetails(self, PKI_details):
        """
        setPKIDetails(self, PKI_details)
        """

        self.__PKI_details = PKI_details

    def setTestUser(self):
        """
        setTestUser(self)
        """

        self.__is_test_user = True

    def isTestUser(self):
        """
        isTestUser(self)
        """

        return self.__is_test_user

    def getTerminal(self):
        """
        getTerminal(self)
        """

        return self.__terminal

    def setTerminal(self, terminal):
        """
        setTerminal(self, terminal)
        """

        self.__terminal = terminal

    def getDevice(self):
        """
        getDevice(self)
        """

        return self.__device

    def setDevice(self, device):
        """
        setDevice(self, device)
        """

        self.__device = device

    def getLocation(self):
        """
        getLocation(self)
        """

        return self.__location

    def setLocation(self, location):
        """
        setLocation(self, location)
        """

        self.__location = location

    def getUseCaseName(self):
        """
        getUseCaseName(self)
        """

        return self.__use_case_name

    def getStartTime(self):
        """
        getStartTime(self)
        """

        return self.__start_time

    def setStartTime(self, start_time):
        """
        setStartTime(self, start_time)
        """

        self.__start_time = start_time

    def isActive(self):
        """
        isActive(self)
        """

        return self.__is_active

    def getCurrentStep(self):
        """
        getCurrentStep(self)
        """

        return self.__current_step

    def getNextStep(self):
        """
        getNextStep(self)
        """

        try:
            for steps in self.__use_case_step_list:
    
                if self.__current_step is None:
                    steps.setActionTime((datetime.datetime.today() +
                                         datetime.timedelta(minutes=steps.getInterval())).strftime('%Y%m%d%H%M'))
                    self.__current_step = steps
    
                    return steps
                else:
                    if int(steps.getStepNumber()) == (int(self.__current_step.getStepNumber()) + 1):
                        increment = datetime.timedelta(minutes=steps.getInterval())
                        steps.setActionTime((datetime.datetime.today() + increment).strftime('%Y%m%d%H%M'))

                        self.__current_step = steps
    
                        logger.debug("Action Time set to : " + str(steps.getActionTime()))
    
                        return steps
    
            self.setComplete()

        except Exception as get_next_step_ex:
            logger.error("Exception raised in getNextStep method!")
            logger.info(str(get_next_step_ex))

        return None

    def setActive(self):
        """
        setActive(self)
        """

        self.__is_active = True
        self.__current_step = self.getNextStep()

    def setComplete(self):
        """
        setComplete(self)
        """

        self.__current_step = None
        self.__is_active = False

    def setInterval(self, interval_in_minutes):
        """
        setInterval(self, interval_in_minutes)
        """

        self.__interval_in_minutes = interval_in_minutes

    def getInterval(self):
        """
        getInterval(self)
        """

        return self.__interval_in_minutes

    def addStep(self, use_case_step):
        """
        addStep(self, use_case_step)
        """

        self.__use_case_step_list.append(use_case_step)

    def displayDetails(self):
        """
        displayDetails(self)
        """

        if self.__current_step is not None:
            logger.info("Current step : " + str(self.__current_step.getStepNumber()))

        for steps in self.__use_case_step_list:
            steps.displayDetails()


class UseCaseQueue:
    """
    The base class for a use-case queue
    """

    def __init__(self, queue_name):
        """
        __init__(self, queue_name)
        """

        self.__queue_name = queue_name
        self.__use_case_queue = list()

    def getQueueName(self):
        """
        getQueueName(self)
        """

        return self.__queue_name

    def generateJobId(self):
        """
        generateJobId(self)
        """

        return (self.__queue_name + "_" +
                datetime.datetime.today().strftime(FILENAME_DATE_FORMAT) + "_" +
                str(random.randint(1000, 9999)))

    def addUseCase(self, use_case):
        """
        addUseCase(self, use_case)
        """

        self.__use_case_queue.append([self.generateJobId(), use_case])

    def displayDetails(self):
        """
        displayDetails(self)
        """

        logger.info("Use Case Queue : " + str(self.__queue_name))

        for steps in self.__use_case_queue:
            logger.info("Queue Job ID : " + str(steps[0]))
            logger.info("Use Case     : " + str(steps[1].getUseCaseName()))
            logger.info("Use Case Steps :")

            steps[1].displayDetails()

    def getJobQueue(self):
        """
        getJobQueue(self)
        """

        return self.__use_case_queue


class PrintQueue:
    """
    The base class for a print queue
    """

    def __init__(self, queue_name):
        """
        __init__(self, queue_name)
        """

        self.__queue_name = queue_name
        self.__print_queue = list()

    def generateJobId(self):
        """
        generateJobId(self)
        """

        return (self.__queue_name + "_" +
                datetime.datetime.today().strftime(FILENAME_DATE_FORMAT) + "_" +
                str(random.randint(1000, 9999)))

    def getQueueName(self):
        """
        getQueueName(self)
        """

        return self.__queue_name

    def addQueueDocument(self, badge_number, event_time, document_name, pages, size, marking):
        """
        addQueueDocument(self, badge_number, event_time, document_name, pages, size, marking)
        """

        self.__print_queue.append([self.generateJobId(), badge_number, document_name, pages, size, marking])

    def pullQueuedDocument(self, badge_number, job_id, location, printer, event_time):
        """
        pullQueuedDocument(self, badge_number, job_id, location, printer, event_time)
        """

        try:
            for item, queued_docs in enumerate(self.__print_queue):
    
                if ((queued_docs[0] == job_id) and(queued_docs[1] == badge_number)):
    
                    logger.info("Creating DOCUMENT PULL event in the PRINT feed for user " + str(badge_number))

                    if users[badge_number].getSessionId() is None:
                        current_session = "N/A"
                    else:
                        current_session = users[badge_number].getSessionId()
    
                    create_event_output("PRINT", [badge_number,
                                                  location,
                                                  printer.getPrinterName(),
                                                  printer.getPrinterType(),
                                                  queued_docs[2],
                                                  queued_docs[3],
                                                  queued_docs[4],
                                                  queued_docs[5],
                                                  current_session,
                                                  "DOCUMENT PULLED FROM QUEUE",
                                                  SUCCESS], event_time)
                    del self.__print_queue[item]

        except Exception as pull_queued_document_ex:
            logger.error("Raised exception in pullQueuedDocument!")
            logger.info(str(pull_queued_document_ex))

    def getJobQueue(self):
        """
        getJobQueue(self)
        """

        return self.__print_queue

    def showAllQueuedDocuments(self):
        """
        showAllQueuedDocuments(self)
        """

        logger.debug("All queued documents on print queue " + str(self.__queue_name))

        for queued_docs in self.__print_queue:
            logger.debug("Job ID         : " + str(queued_docs[0]))
            logger.debug("Badge Number   : " + str(queued_docs[1]))
            logger.debug("Added to Queue : " + str(queued_docs[2]))
            logger.debug("Document       : " + str(queued_docs[3]))
            logger.debug("Pages          : " + str(queued_docs[4]))
            logger.debug("Size           : " + str(queued_docs[5]))
            logger.debug("Marking        : " + str(queued_docs[6]))

    def showQueuedDocuments(self, badge_number):
        """
        showQueuedDocuments(badge_number)
        """

        logger.debug("Queued documents for user " + str(badge_number) +
                     " on print queue " + str(self.__queue_name))

        for queued_docs in self.__print_queue:

            if queued_docs[1] == badge_number:
                logger.debug("Job ID         : " + str(queued_docs[0]))
                logger.debug("Badge Number   : " + str(queued_docs[1]))
                logger.debug("Added to Queue : " + str(queued_docs[2]))
                logger.debug("Document       : " + str(queued_docs[3]))
                logger.debug("Pages          : " + str(queued_docs[4]))
                logger.debug("Size           : " + str(queued_docs[5]))
                logger.debug("Marking        : " + str(queued_docs[6]))


"""
This sad and lonely looking line of code looks a bit out of place here (it probably is!)
I needed to set up the solitary "MAIN" print queue somewhere and here seemed as good a place
as any at the time I wrote the queue code. Sorry little line of code... :-(
"""

main_print_queue = PrintQueue("MAIN_PRINT_QUEUE")


class Printer(Device):
    """
    The base class for a printer
    """

    def __init__(self, office, printer_name, printer_type, asset_tag, direct_or_pull, print_queue):
        """
        __init__(self, office, printer_name, printer_type, asset_tag, direct_or_pull, print_queue)
        """

        Device.__init__(self, None, printer_name, printer_type, None, asset_tag, None, None)

        self.__office = office
        self.__printer_name = printer_name
        self.__printer_type = printer_type
        self.__direct_or_pull = direct_or_pull
        self.__print_queue = print_queue

    def getLocation(self):
        """
        getLocation(self)
        """

        return self.__office

    def getDirectOrPull(self):
        """
        getDirectOrPull(self)
        """

        return self.__direct_or_pull

    def getPrintQueue(self):
        """
        getPrintQueue(self)
        """

        return self.__print_queue

    def getPrinterName(self):
        """
        getPrinterName(self)
        """

        return self.__printer_name

    def getPrinterType(self):
        """
        getPrinterType(self)
        """

        return self.__printer_type

    def getCurrentLocation(self):
        """
        getCurrentLocation(self)
        """

        return self.__office

    def printDocument(self,
                      badge_number,
                      event_time,
                      document_name,
                      document_pages,
                      document_size,
                      marking,
                      print_queue):
        """
        Print a document from this printer.
        """

        try:
            if self.__direct_or_pull == "DIRECT":
                logger.info("Creating a direct print event for user " + str(badge_number))
    
                if users[badge_number].getSessionId() is None:
                    current_session = "N/A"
                else:
                    current_session = users[badge_number].getSessionId()
    
                create_event_output("PRINT", [badge_number,
                                              self.__office,
                                              self.__printer_name,
                                              self.__printer_type,
                                              document_name,
                                              document_pages,
                                              document_size,
                                              marking,
                                              current_session,
                                              "DOCUMENT PRINTED",
                                              SUCCESS], event_time)
            else:
                logger.info("Creating a queued print event for user " + str(badge_number))
    
                print_queue.addQueueDocument(badge_number,
                                             event_time,
                                             document_name,
                                             document_pages,
                                             document_size,
                                             marking)
    
                create_event_output("PRINT", [badge_number,
                                              self.__office,
                                              self.__printer_name,
                                              self.__printer_type,
                                              document_name,
                                              document_pages,
                                              document_size,
                                              marking,
                                              users[badge_number].getSessionId(),
                                              "DOCUMENT QUEUED",
                                              SUCCESS], event_time)
    
        except Exception as print_document_ex:
            logger.error("Exception raised in printDocument method!")
            logger.info(str(print_document_ex))

    def displayDetails(self):
        """
        Display method for an Printer's details.
        """

        logger.debug("Printer Details :-")
        logger.debug("Office       : " + str(self.__office))
        logger.debug("Printer Name : " + str(self.__printer_name))
        logger.debug("Printer Type : " + str(self.__printer_type))
        logger.debug("Asset Tag    : " + str(self.__asset_tag))

        if self.__direct_or_pull == "DIRECT":
            logger.debug("Printer is directly attached.")
        else:
            logger.debug("Printer is a 'Pull' printer.")

"""
END OF CLASSES DEFINITION
"""


"""
START OF FUNCTION DEFINITIONS
"""

def create_elk_lists():
    """
    This function is a bit of a workaround for using the standard method of discovering the
    current state of a value in the ELK stack as for some reason that was nailing my development
    VM. Now it does a quick bulk read of the state tables, dumps them into lists and then uses
    those lists to populate dictionaries with badge_number as the index.
    """

    elk_user_locations = list()
    elk_user_terminals = list()
    elk_user_phones = list()

    logger.disabled = True
    tracer = logging.getLogger('elasticsearch')
    tracer.setLevel(logging.CRITICAL)
    tracer.addHandler(logging.FileHandler(read_config_value(CONFIG_FILENAME,
                                                            "FileNames",
                                                            "ElasticsearchLogFile")))

    ES_HOST = {"host": ES_host, "port": ES_port}
    es = elasticsearch.Elasticsearch(hosts=[ES_HOST])

    """
    Check to ensure that the state table indexes have beed created before we get any further
    and end up embarassing ourselves....
    """

    try:
        if ((not es.indices.exists('user_locations')) or
            (not es.indices.exists('user_terminals')) or
            (not es.indices.exists('user_phones'))):
            sys.exit("State tables have not been created!!!")
    
        location_results = elasticsearch.helpers.scan(es,
                                                      index='user_locations',
                                                      doc_type='user_locations_record',
                                                      preserve_order=True,
                                                      query={"query": {"match": {"current": "Y"}}})
    
        for i, elk_location in enumerate(location_results):
            elk_user_locations.append([elk_location['_source']['badge_number'],
                                       elk_location['_source']['location']])
    
        terminal_results = elasticsearch.helpers.scan(es,
                                                      index='user_terminals',
                                                      doc_type='user_terminals_record',
                                                      preserve_order=True,
                                                      query={"query": {"match": {"current": "Y"}}})
    
        for i, elk_terminal in enumerate(terminal_results):
            elk_user_terminals.append([elk_terminal['_source']['badge_number'],
                                       elk_terminal['_source']['location'],
                                       elk_terminal['_source']['terminal']])
    
        phone_results = elasticsearch.helpers.scan(es,
                                                   index='user_phones',
                                                   doc_type='user_phones_record',
                                                   preserve_order=True,
                                                   query={"query": {"match": {"current": "Y"}}})
    
        for i, elk_phone in enumerate(phone_results):
            elk_user_phones.append([elk_phone['_source']['badge_number'],
                                    elk_phone['_source']['phone']])
    
        """
        The next couple of loops use deepcopy as I was concerned that there might be some
        referencing of values going on, although I'm not sure that's actually the case.
        No real harm done by doing a deepcopy on these though.
        """
    
        for user_location in range(len(elk_user_locations)):
            elk_user_locations_dict[elk_user_locations[user_location][0]] = copy.deepcopy(elk_user_locations[user_location][1:])
    
        for user_terminal in range(len(elk_user_terminals)):
            elk_user_terminals_dict[elk_user_terminals[user_terminal][0]] = copy.deepcopy(elk_user_terminals[user_terminal][1:])
    
        for user_phone in range(len(elk_user_phones)):
            elk_user_phones_dict[elk_user_phones[user_phone][0]] = copy.deepcopy(elk_user_phones[user_phone][1:])
    
        logger.disabled = False

    except Exception as create_elk_lists_ex:
        logger.error("Exception raised in create_elk_lists function!")
        logger.info(str(create_elk_lists_ex))


def populate_lists():
    """
    This is the bit that takes the entity data files (the .ent.csv files in the reference_data directory) and
    transforms them into lists of Python objects to make the code a bit more readable/usable elsewhere.
    Probably not the most 'Pythonic' bit of code but I'll refactor it once I've got the rest of the
    functionality up-and-running.
    """

    # USER_RISKS
    risks_dict = {}

    user_risks_file = read_config_value(CONFIG_FILENAME, "FileNames", "UserRisksFilename")

    with open(ref_data_directory + "/" + user_risks_file, 'rb') as f:
        csv_reader = csv.reader(f)
        next(csv_reader)
        risk_list = list(csv_reader)

    for i in range(len(risk_list)):
        risks_dict[risk_list[i][0]] = risk_list[i][1:]

    # TERMINALS
    terminals_file = read_config_value(CONFIG_FILENAME, "FileNames", "TerminalsFileName")

    with open(ref_data_directory + "/" + terminals_file, 'rb') as f:
        csv_reader = csv.reader(f)
        next(csv_reader)
        term_list = list(csv_reader)

    for i in range(len(term_list)):
        terminals_list.append(Terminal(term_list[i][0], term_list[i][2], term_list[i][1], term_list[i][3], term_list[i][4]))

    # CITRIX_SERVERS
    citrix_servers_file = read_config_value(CONFIG_FILENAME, "FileNames", "CitrixServersFileName")

    with open(ref_data_directory + "/" + citrix_servers_file, 'rb') as f:
        csv_reader = csv.reader(f)
        next(csv_reader)
        citrix_server_list = list(csv_reader)

    # server_name,location
    for i in range(len(citrix_server_list)):
        citrix_servers_list.append(CitrixServer(citrix_server_list[i][0], citrix_server_list[i][1], citrix_server_list[i][2]))

    # CITRIX_SESSIONS
    citrix_sessions_file = read_config_value(CONFIG_FILENAME, "FileNames", "CitrixSessionsFileName")

    with open(ref_data_directory + "/" + citrix_sessions_file, 'rb') as f:
        csv_reader = csv.reader(f)
        next(csv_reader)
        citrix_session_list = list(csv_reader)

    # session_name,location,citrix_server
    for i in range(len(citrix_session_list)):
        citrix_sessions_list.append(CitrixSession(citrix_session_list[i][0], citrix_session_list[i][1], citrix_session_list[i][2]))

    # PHONES
    phones_file = read_config_value(CONFIG_FILENAME, "FileNames", "PhonesFileName")

    with open(ref_data_directory + "/" + phones_file, 'rb') as f:
        csv_reader = csv.reader(f)
        next(csv_reader)
        phone_list = list(csv_reader)

    for i in range(len(phone_list)):
        phones_list.append(Phone(phone_list[i][0], phone_list[i][2], phone_list[i][1]))

    # LOCATIONS
    locations_file = read_config_value(CONFIG_FILENAME, "FileNames", "LocationsFileName")

    with open(ref_data_directory + "/" + locations_file, 'rb') as f:
        csv_reader = csv.reader(f)
        next(csv_reader)
        loc_list = list(csv_reader)

    for i in range(len(loc_list)):
        locations_list.append(Office(loc_list[i][0], loc_list[i][1], loc_list[i][2], loc_list[i][3]))

    # DOORS
    doors_file = read_config_value(CONFIG_FILENAME, "FileNames", "DoorsFileName")

    with open(ref_data_directory + "/" + doors_file, 'rb') as f:
        csv_reader = csv.reader(f)
        next(csv_reader)
        door_list = list(csv_reader)

    for i in range(len(door_list)):
        doors_list.append(Door(door_list[i][0], door_list[i][1], door_list[i][2]))

    # EMAIL_BODIES
    email_bodies_file = read_config_value(CONFIG_FILENAME, "FileNames", "EmailBodiesFileName")
    with open(ref_data_directory + "/" + email_bodies_file, 'rb') as f:
        csv_reader = csv.reader(f)
        next(csv_reader)
        email_body_list = list(csv_reader)

    for i in range(len(email_body_list)):
        email_bodies_list.append([email_body_list[i][0], email_body_list[i][1]])

    # MATCH_TERMS
    match_terms_file = read_config_value(CONFIG_FILENAME, "FileNames", "MatchTermsFileName")
    with open(ref_data_directory + "/" + match_terms_file, 'rb') as f:
        csv_reader = csv.reader(f)
        next(csv_reader)
        match_term_list = list(csv_reader)

    for i in range(len(match_term_list)):
        match_terms_list.append([match_term_list[i][0], match_term_list[i][1], match_term_list[i][2]])

    # PRINTERS
    printers_file = read_config_value(CONFIG_FILENAME, "FileNames", "PrintersFileName")
    with open(ref_data_directory + "/" + printers_file, 'rb') as f:
        csv_reader = csv.reader(f)
        next(csv_reader)
        printer_list = list(csv_reader)

    for i in range(len(printer_list)):
        printers_list.append(Printer(printer_list[i][0], printer_list[i][1], printer_list[i][2], None, printer_list[i][3], main_print_queue))

    # DEVICES
    devices_file = read_config_value(CONFIG_FILENAME, "FileNames", "DevicesFileName")

    with open(ref_data_directory + "/" + devices_file, 'rb') as f:
        csv_reader = csv.reader(f)
        next(csv_reader)
        device_list = list(csv_reader)

    for i in range(len(device_list)):
        devices_list.append(Device(device_list[i][0],
                                   device_list[i][1],
                                   device_list[i][2],
                                   device_list[i][4],
                                   device_list[i][5],
                                   device_list[i][6],
                                   device_list[i][7]))

    # USERS
    users_file = read_config_value(CONFIG_FILENAME, "FileNames", "UsersFilename")

    with open(ref_data_directory + "/" + users_file, 'rb') as f:
        csv_reader = csv.reader(f)
        next(csv_reader)
        user_list = list(csv_reader)

    # General details
    for i in range(len(user_list)):
        badge_list.append(user_list[i][0])
        users[user_list[i][0]] = Employee(user_list[i][0], user_list[i][1], user_list[i][2], user_list[i][3])
        users[user_list[i][0]].assignBadge(user_list[i][0])
        users[user_list[i][0]].assignRiskScore(risks_dict[user_list[i][0]][0])
        users[user_list[i][0]].setMainLocation(user_list[i][4])
        users[user_list[i][0]].setJobTitle(user_list[i][5])
        users[user_list[i][0]].setEmailAddress(user_list[i][6])
        users[user_list[i][0]].setPhoneNumber(user_list[i][7])
        users[user_list[i][0]].setPatternOfLife(user_list[i][9])
        users[user_list[i][0]].setPKIDetails(user_list[i][11])
        if (user_list[i][11] == "Y"):
            users[user_list[i][0]].setTestUser()

        # Set a flag to indicate whether the user is a smoker (for pattern of life stuff)
        if user_list[i][8] == "Y":
            users[user_list[i][0]].setSmoker()
        else:
            users[user_list[i][0]].setNonSmoker()

        # Assign user to a team if specified
        if user_list[i][10] is not None:
            users[user_list[i][0]].assignTeam(user_list[i][10], None)

        # Create the ELK lookup lists from the state tables (user_locations and user_terminals) in ElasticSearch
        create_elk_lists()

        # Set the locations and terminals for users in the state tables so that the data generation
        # is consistent, even when restarted at a later time.
        if int(user_list[i][0]) in elk_user_locations_dict:
            logger.info("Setting user in building for user " + str(user_list[i][0]) + " from ELK value")
            users[user_list[i][0]].setCurrentLocation(elk_user_locations_dict[int(user_list[i][0])][0])
            if int(user_list[i][0]) in elk_user_terminals_dict:
                logger.info("Setting user logged in to " + elk_user_terminals_dict[int(user_list[i][0])][1] +
                            " for user " + str(user_list[i][0]) + " from ELK value")
                users[user_list[i][0]].setCurrentTerminal(return_terminal_by_name(elk_user_terminals_dict[int(user_list[i][0])][1]))
    # Assign a random number of Assets/Devices to people
    for i in range(len(devices_list) - (random.randint(0, len(devices_list) - 1))):
        random_device = return_random_device()
        new_random_user = return_random_badge()
        if not random_device.hasOwner():
            new_device_name = users[new_random_user].getFirstName() + "'s " + random_device.getDeviceName()
            random_device.setDeviceName(new_device_name)
            random_device.assignOwner(new_random_user)

    # PKI Details
    pki_details_file = read_config_value(CONFIG_FILENAME, "FileNames", "PKIDetailsFileName")

    with open(ref_data_directory + "/" + pki_details_file, 'rb') as f:
        csv_reader = csv.reader(f)
        next(csv_reader)
        pki_detail_list = list(csv_reader)

    for i in range(len(pki_detail_list)):
        pki_details_list.append([pki_detail_list[i][0], pki_detail_list[i][1]])
        if pki_detail_list[i][2] != "None":
            users[pki_detail_list[i][0]].setCanLoginCircus()
        else:
            logger.info("User " + pki_detail_list[i][0] + " can't login to CIRCUS! " + pki_detail_list[i][2])
        if pki_detail_list[i][3] != "None":
            users[pki_detail_list[i][0]].setCanLoginVoyager()
        else:
            logger.info("User " + pki_detail_list[i][0] + " can't login to VOYAGER! " + pki_detail_list[i][3])
        if pki_detail_list[i][4] != "None":
            users[pki_detail_list[i][0]].setCanLoginStructure()
        else:
            logger.info("User " + pki_detail_list[i][0] + " can't login to STRUCTURE! " + pki_detail_list[i][4])

    # CIRCUS operations
    circus_operations_file = read_config_value(CONFIG_FILENAME, "FileNames", "CircusOperationsFileName")

    with open(ref_data_directory + "/" + circus_operations_file, 'rb') as f:
        csv_reader = csv.reader(f)
        next(csv_reader)
        circus_operation_list = list(csv_reader)

    for i in range(len(circus_operation_list)):
        circus_operations_list.append(circus_operation_list[i][0])

    # STRUCTURE operations
    structure_operations_file = read_config_value(CONFIG_FILENAME, "FileNames", "StructureOperationsFileName")

    with open(ref_data_directory + "/" + structure_operations_file, 'rb') as f:
        csv_reader = csv.reader(f)
        next(csv_reader)
        structure_operation_list = list(csv_reader)

    for i in range(len(structure_operation_list)):
        structure_operations_list.append(structure_operation_list[i][0])

    # VOYAGER operations
    voyager_operations_file = read_config_value(CONFIG_FILENAME, "FileNames", "VoyagerOperationsFileName")

    with open(ref_data_directory + "/" + voyager_operations_file, 'rb') as f:
        csv_reader = csv.reader(f)
        next(csv_reader)
        voyager_operation_list = list(csv_reader)

    for i in range(len(voyager_operation_list)):
        voyager_operations_list.append(voyager_operation_list[i][0])

    return True


def office_door_data_available(location):
    """
    This function identifies whether the location has door data or not.
    """

    try:
        for offices in locations_list:
            if offices.getLocationName() == location:
                return offices.hasDoorData()
    except Exception as odda_ex:
        logger.error("Exception raised in office_door_data_available")
        logger.info(str(odda_ex))

    return False


def return_random_badge():
    """
    As the name implies, this just returns a random user's badge number from the list

    *** THIS IS CURRENTLY KLUDGED TO RETURN BADGE NUMBERS OUTSIDE THE TEST USER BADGE RANGE
    """

    while True:
        random_badge_number = random.randint(0, len(badge_list) - 1)
        if random_badge_number < 1000:
            return badge_list[random_badge_number]


def return_random_pki_details():
    """
    As the name implies, this just returns a random user's PKI details from the list
    """

    return pki_details_list[random.randint(0, len(pki_details_list) - 1)]


def return_random_device():
    """
    As the name implies, this just returns a random device from the ingested list
    """

    return devices_list[random.randint(1, len(devices_list) - 1)]


def return_citrix_server(location):
    """
    Return the local CITRIX server for the given location.
    """

    for citrix_server in citrix_servers_list:
        if citrix_server.getLocation() == location:
            return citrix_server

    return None


def return_terminal_by_name(terminal_name):
    """
    return_terminal_by_name(terminal_name)
    """

    for terminal in terminals_list:
        if terminal.getTerminalName() == terminal_name:
            return terminal

    return None


def return_citrix_session_by_name(session_name):
    """
    return_citrix_session_by_name(session_name)
    """

    for citrix_session in citrix_sessions_list:
        if citrix_session.getSessionName() == session_name:
            return citrix_session

    return None


def return_citrix_session(citrix_server):
    """
    Return a CITRIX session from the pool associated to the supplied CITRIX server.
    """

    try:
        for citrix_session in citrix_sessions_list:
            if ((citrix_session.getLocation() == citrix_server.getLocation()) and
                (citrix_session.getServerName() == citrix_server.getServerName()) and
                (not citrix_session.isSessionAssigned())):
                return citrix_session

        logger.debug("Unable to assign free session for server " + citrix_server.getServerName())

    except Exception as return_citrix_session_ex:
        logger.error("Exception raised in return_citrix_session function!")
        logger.info(str(return_citrix_session_ex))

    return None


def release_citrix_session(badge_number, office, terminal):
    """
    Release a CITRIX session back to the pool for the local CITRIX server (and given user *obvs*).
    """

    logger.debug("Releasing a THIN client session from terminal " + terminal.getTerminalName() +
                 " for user " + badge_number)

    try:
        local_citrix_server = return_citrix_server(office)

        allocated_sessions_list = local_citrix_server.getAllocatedSessionsList()

        for item, allocated_session in enumerate(allocated_sessions_list):
            if ((allocated_session[2] == terminal.getTerminalName()) and
                (allocated_session[1] == badge_number)):
                logger.debug("Releasing session " + allocated_session[0])
                local_citrix_server.releaseSession(allocated_sessions_list[item])

    except Exception as release_citrix_session_ex:
        logger.error("Exception raised in release_citrix_session function!")
        logger.info(str(release_citrix_session_ex))


def return_random_printer(location):
    """
    Returns a random printer at the given location. This is a bit horrid but I'll refactor it later
    as I doubt it's a massive processing overhead.
    """

    while True:

        random_entry = random.randint(0, len(printers_list) - 1)

        if printers_list[random_entry].getLocation() == location:
            return printers_list[random_entry]


def return_random_direct_printer(location):
    """
    Returns a random direct printer at the given location. This is a bit horrid but I'll refactor it later
    as I doubt it's a massive processing overhead.
    """

    while True:

        random_entry = random.randint(0, len(printers_list) - 1)

        if ((printers_list[random_entry].getLocation() == location) and
            (printers_list[random_entry].getDirectOrPull() == "DIRECT")):
            return printers_list[random_entry]

def return_random_pull_printer(location):
    """
    Returns a random pull printer at the given location. This is a bit horrid but I'll refactor it later
    as I doubt it's a massive processing overhead.
    """

    while True:

        random_entry = random.randint(0, len(printers_list) - 1)

        if ((printers_list[random_entry].getLocation() == location) and
            (printers_list[random_entry].getDirectOrPull() == "PULL")):
            return printers_list[random_entry]


def return_random_recipient_list():
    """
    Returns a random list of email recipients up to a maximum configurable value.
    """

    rec_list = ""

    for i in range(max_recipients):

        rec_list += str(users[return_random_badge()].getEmailAddress())

        if (i < (max_recipients - 1)):
            rec_list += ";"

    return rec_list


def return_team_members(team_name):
    """
    Returns a list containing all of the members of a specified team.
    This feels like it should be better "Python-ised" with a Team class etc.
    """

    team_list = []

    if ((team_name == "") or (team_name is None)):
        return team_list

    for key, members in users.iteritems():

        if users[key].getCurrentTeam() == str(team_name):
            team_list.append(key)

    return team_list


def return_team_recipient_list(badge_number):
    """
    Returns a semi-colon separated email address list of the addresses of members of the specified
    user's team (minus themselves *obviously*)
    Used for generating a random team email when required.
    """

    rec_list = ""

    user_team = users[badge_number].getCurrentTeam()

    if ((str(user_team) != "None") and (str(user_team) != "")):
        rec_list = ""
        returned_team = return_team_members(user_team)

        for team_member in returned_team:
            if team_member != badge_number:
                rec_list += users[team_member].getEmailAddress()
                rec_list += ";"

        return rec_list[:(len(rec_list) - 1)]
    else:
        return "Incorrect recipient list"


def return_random_location():
    """
    return_random_location()

    Literally used in only one place so I have to ask "Is it worth it???"
    """

    return locations_list[random.randint(0, len(locations_list) - 1)].getLocationName()


def return_random_door(location):
    """
    Returns a random door at the given location. This is a bit horrid but I'll refactor it later
    as I doubt it's a massive processing overhead.
    """

    while True:

        random_entry = random.randint(0, len(doors_list) - 1)

        if doors_list[random_entry].getLocation() == location:
            return doors_list[random_entry]


def return_random_terminal(location):
    """
    Returns a random terminal at the given location. This is a bit horrid but I'll refactor it later
    as I doubt it's a massive processing overhead.
    """

    try:
        while True:

            random_entry = random.randint(0, len(terminals_list) - 1)

            if ((terminals_list[random_entry].getLocation() == location) or
                (terminals_list[random_entry].getTerminalType() == "THIN")):
                return terminals_list[random_entry]

    except Exception as ret_ran_term_ex:
        logger.error("Exception raised in return_random_terminal")
        return None


def return_random_phone(location):
    """
    Returns a random printer at the given location. This is a bit horrid but I'll refactor it later
    as I doubt it's a massive processing overhead.
    """

    available_phones = list()

    for phone in phones_list:
        if ((not phone.isLoggedIn()) and (phone.getLocation() == location)):
            available_phones.append(phone)

    if len(available_phones) > 0:
        random_phone = random.randint(0, len(available_phones) - 1)
        return available_phones[random_phone]
    else:
        logger.debug("No phones available whilst selecting random phone at " + str(location))

    return None


def create_email_events(event_time):
    """
    create_email_events(event_time)
    """

    for i in range(1, random.randint(1, noise_factor)):

        random_user = return_random_badge()

        if users[random_user].isLoggedIn():

            if return_random_outcome() == SUCCESS:
                recipient_list = return_random_recipient_list()
                logger.info("Creating a random out of team email event for user " + str(random_user) +
                            " at " + str(event_time) + " in the EMAILS feed")
                users[random_user].sendEmail(event_time, recipient_list)
            else:
                if users[random_user].getCurrentTeam() is not None:
                    recipient_list = return_team_recipient_list(random_user)
                    logger.info("Creating a random team email " +
                                " for user " + str(random_user) +
                                " event at " + str(event_time) + " in the EMAILS feed")
                    users[random_user].sendEmail(event_time, recipient_list)


def create_phone_events(event_time):
    """
    create_phone_events(event_time)
    """

    for i in range(1, random.randint(1, noise_factor)):

        random_from_user = return_random_badge()
        random_to_user = return_random_badge()

        if users[random_from_user].isLoggedIn():
            logger.debug("Creating a 'From' event at " + str(event_time) + " in the PHONES feed")
            logger.debug("Creating a 'To' event at " + str(event_time) + " in the PHONES feed")

            if users[random_to_user].getPhone() is not None:
                users[random_from_user].createPhonecall(event_time, users[random_to_user].getPhone())
            else:
                logger.debug("Null destination phone")


def create_print_events(event_time):
    """
    create_print_events(event_time)
    """

    for i in range(1, random.randint(1, noise_factor)):

        random_user = return_random_badge()

        if users[random_user].isLoggedIn():

            random_pages = random.randint(1, 30)
            random_size = (random_pages * random.randint(500, 1000))
            doc_name = 'DOC_' + datetime.datetime.today().strftime(FILENAME_DATE_FORMAT) + '.doc'
            actual_printer = return_random_printer(users[random_user].getCurrentLocation())

            actual_printer.printDocument(random_user,
                                         event_time,
                                         doc_name,
                                         random_pages,
                                         random_size,
                                         return_random_marking(),
                                         main_print_queue)

            logger.info("Creating a random event for user " + str(random_user) +
                        " at " + str(event_time) + " in the PRINT feed")


def create_print_queue_pull_events(event_time):
    """
    create_print_queue_pull_events(event_time)
    """

    current_print_queue = main_print_queue.getJobQueue()

    if len(current_print_queue) > 0:

        for i in range(1, random.randint(1, len(current_print_queue))):

            for jobs in current_print_queue:
                if RandomChance("HIGH"):
                    current_location = users[jobs[1]].getCurrentLocation()

                    if current_location is None:
                        logger.debug("User is swiped out of all buildings so can't create document pull event for job " + jobs[1])
                        return False

                    random_printer = return_random_printer(current_location)
                    logger.info("Creating a random print queue pull event for user " + str(jobs[0]) +
                                " at " + str(event_time) + " in the PRINT feed")
                    main_print_queue.pullQueuedDocument(jobs[1], jobs[0], current_location, random_printer, event_time)
                    return True

    logger.debug("No jobs in print queue for queue : " + str(main_print_queue.getQueueName()))

    return False


def create_circus_events(event_time):
    """
    create_circus_events(event_time)
    """

    for i in range(1, random.randint(1, noise_factor)):
        random_action = circus_operations_list[random.randint(0, len(circus_operations_list) - 1)]
        random_user = return_random_badge()

        if ((users[random_user].isLoggedIntoCircus()) and
            (random_action != "LOGIN") and
            (random_action != "LOGOUT")):
            logger.info("Creating a " + str(random_action) +
                        " event for user " + random_user +
                        " at " + str(event_time) +
                        " in the CIRCUS feed")
            users[random_user].performCircusOperation(random_action, return_success_or_failure(), event_time)
        elif ((users[random_user].isLoggedIntoCircus()) and
              (random_action == "LOGOUT")):
            logger.info("Creating a LOGOUT event for user " + random_user +
                        " at " + str(event_time) +
                        " in the CIRCUS feed")
            users[random_user].logoutCircus(event_time)
        elif ((users[random_user].isLoggedIn()) and
              (not users[random_user].isLoggedIntoCircus()) and
              (random_action == "LOGIN") and
              (users[random_user].checkPKIPermissions("CIRCUS"))):
            logger.info("Creating a LOGIN event for user " + random_user +
                        " at " + str(event_time) +
                        " in the CIRCUS feed")
            users[random_user].loginCircus(return_success_or_failure(), event_time)
        elif (not users[random_user].checkPKIPermissions("CIRCUS")):
            logger.info("Insufficient privileges for user " + random_user +
                        " to login to CIRCUS at " + str(event_time))
            create_event_output("CIRCUS", [random_user,
                                           "LOGIN",
                                           "Insufficient Privileges",
                                           DENIED], event_time)


def create_structure_events(event_time):
    """
    create_structure_events(event_time)
    """

    for i in range(1, random.randint(1, noise_factor)):
        random_action = structure_operations_list[random.randint(0, len(structure_operations_list) - 1)]
        random_user = return_random_badge()

        if ((users[random_user].isLoggedIntoStructure()) and
            (random_action != "LOGIN") and
            (random_action != "LOGOUT")):
            logger.info("Creating a " + str(random_action) + " event for user " + random_user + " at " + str(event_time) + " in the STRUCTURE feed")
            users[random_user].performStructureOperation(random_action, return_success_or_failure(), event_time)
        elif ((users[random_user].isLoggedIntoStructure()) and
              (random_action == "LOGOUT")):
            logger.info("Creating a LOGOUT event for user " + random_user + " at " + str(event_time) + " in the STRUCTURE feed")
            users[random_user].logoutStructure(event_time)
        elif ((users[random_user].isLoggedIn()) and
              (not users[random_user].isLoggedIntoStructure()) and
              (random_action == "LOGIN") and
              (users[random_user].checkPKIPermissions("STRUCTURE"))):
            logger.info("Creating a LOGIN event for user " + random_user + " at " + str(event_time) + " in the STRUCTURE feed")
            users[random_user].loginStructure(return_success_or_failure(), event_time)
        elif (not users[random_user].checkPKIPermissions("STRUCTURE")):
            logger.info("Insufficient privileges for user " + random_user +
                        " to login to STRUCTURE at " + str(event_time))
            create_event_output("STRUCTURE", [random_user,
                                              "LOGIN",
                                              "Insufficient Privileges",
                                              DENIED], event_time)


def create_voyager_events(event_time):
    """
    create_voyager_events(event_time)
    """

    for i in range(1, random.randint(1, noise_factor)):
        random_action = voyager_operations_list[random.randint(0, len(voyager_operations_list) - 1)]
        random_user = return_random_badge()

        if ((users[random_user].isLoggedIntoVoyager()) and
            (random_action != "LOGIN") and
            (random_action != "LOGOUT")):
            logger.info("Creating a " + str(random_action) + " event for user " + random_user + " at " + str(event_time) + " in the VOYAGER feed")
            users[random_user].performVoyagerOperation(random_action, return_success_or_failure(), event_time)
        elif ((users[random_user].isLoggedIntoVoyager()) and
              (random_action == "LOGOUT")):
            logger.info("Creating a LOGOUT event for user " + random_user + " at " + str(event_time) + " in the VOYAGER feed")
            users[random_user].logoutVoyager(event_time)
        elif ((users[random_user].isLoggedIn()) and
              (not users[random_user].isLoggedIntoVoyager()) and
              (random_action == "LOGIN") and
              (users[random_user].checkPKIPermissions("VOYAGER"))):
            logger.info("Creating a LOGIN event for user " + random_user + " at " + str(event_time) + " in the VOYAGER feed")
            users[random_user].loginVoyager(return_success_or_failure(), event_time)
        elif (not users[random_user].checkPKIPermissions("VOYAGER")):
            logger.info("Insufficient privileges for user " + random_user +
                        " to login to VOYAGER at " + str(event_time))
            create_event_output("VOYAGER", [random_user,
                                            "LOGIN",
                                            "Insufficient Privileges",
                                            DENIED], event_time)

"""
END OF FUNCTION DEFINITIONS
"""


def main():
    """
    This is the main body of code, defined like this so that the source can be imported into other
    Python scripts without it kicking off about stuff.
    """

    start_time = datetime.datetime.strptime(read_config_value(CONFIG_FILENAME,
                                                              "DateRange",
                                                              "StartDate"),
                                                              EVENT_DATE_FORMAT)

    end_time = datetime.datetime.strptime(read_config_value(CONFIG_FILENAME,
                                                            "DateRange",
                                                            "EndDate"),
                                                            EVENT_DATE_FORMAT)

    if read_config_value(CONFIG_FILENAME, "DateRange", "Continuous") == "True":
        logger.info("Entering continuous data generation mode....")
        continuous = True
        start_time = datetime.datetime.today()
        end_time = datetime.datetime.today() + datetime.timedelta(minutes=10)
    else:
        continuous = False
        if start_time is None or end_time is None:
            sys.exit("Start or end time has not been set!!!")
        logger.info("From " + str(start_time) + " until " + str(end_time))

    event_time = copy.deepcopy(start_time)

    granularity = int(read_config_value(CONFIG_FILENAME, "DataOptions", "Granularity"))

    json_config_file = read_config_value(CONFIG_FILENAME, "FileNames", "UseCaseJSONFile")

    use_case_config = dict()

    with open(json_config_file) as use_case_config_file:
        use_case_config = json.load(use_case_config_file)

    use_case_list = list()
    element_counter = 0

    main_uc_queue = UseCaseQueue('MainUseCaseQueue')

    for key, members in use_case_config.iteritems():
        use_case_list.append(UseCase(str(key)))
        for items in members:
            use_case_list[element_counter].addStep(UseCaseStep(items["step_number"],
                                                               items["action"]))

        use_case_list[element_counter].setUser(users[str(1000 + element_counter)])

        main_uc_queue.addUseCase(use_case_list[element_counter])
        use_case_list[element_counter].setActive()
        element_counter += 1

    """
    At this point we should maybe loop around the use-cases list and adding the appropriate
    number of users (probably at a badge number range of 1000+n) and then use them as required?
    """

    while(True):

        if ((not continuous) and (event_time > end_time)):
            logger.info("Event_time = " + str(event_time) + " , end_time = " + str(end_time))
            sys.exit("Completed!!!")

        try:

            try:
                today = datetime.datetime.today()

                for use_cases in main_uc_queue.getJobQueue():

                    if use_cases[1].isActive():

                        if use_cases[1].getCurrentStep().getActionTime() == today.strftime('%Y%m%d%H%M'):

                            logger.info("Triggering use-case " + use_cases[1].getUseCaseName() +
                                        " action : " + str(use_cases[1].getCurrentStep().getStepNumber()))
                            logger.info("Action : " + use_cases[1].getCurrentStep().getStepAction())

                            if use_cases[1].getCurrentStep().getStepAction() == "SWIPEIN":

                                use_cases[1].setLocation(use_cases[1].getUser().getMainLocation())

                                logger.info("Generating a swipe in event at " + use_cases[1].getLocation() +
                                            " for user " + str(use_cases[1].getUser().getBadgeNumber()) +
                                            " at time " + str(event_time))

                                use_cases[1].getUser().swipeInEmployee(use_cases[1].getLocation(),
                                                                   return_random_door(use_cases[1].getLocation()).getDoorName(),
                                                                   SUCCESS,
                                                                   event_time)

                            elif use_cases[1].getCurrentStep().getStepAction() == "SWIPEOUT":

                                logger.info("Generating a swipe out event at " + str(use_cases[1].getLocation()) +
                                            " for user " + str(use_cases[1].getUser().getBadgeNumber()) +
                                            " at time " + str(event_time))

                                use_cases[1].getUser().swipeOutEmployee(use_cases[1].getLocation(),
                                                                    return_random_door(use_cases[1].getLocation()).getDoorName(),
                                                                    SUCCESS,
                                                                    event_time)

                            elif use_cases[1].getCurrentStep().getStepAction() == "LOGIN":

                                random_terminal = return_random_terminal(use_cases[1].getUser().getMainLocation())
                                use_cases[1].setTerminal(random_terminal)
                                use_cases[1].setPKIDetails(use_cases[1].getUser().getPKIDetails())

                                logger.info("Generating a login event at " + str(use_cases[1].getLocation()) +
                                            " terminal " + str(use_cases[1].getTerminal().getTerminalName()) +
                                            " for user " + str(use_cases[1].getUser().getBadgeNumber()) +
                                            " at time " + str(event_time))

                                use_cases[1].getUser().loginEmployee(use_cases[1].getLocation(),
                                                                     use_cases[1].getTerminal(),
                                                                     SUCCESS,
                                                                     use_cases[1].getPKIDetails(),
                                                                     event_time)

                            elif use_cases[1].getCurrentStep().getStepAction() == "LOGIN WITH WRONG PKI":

                                random_terminal = return_random_terminal(use_cases[1].getUser().getMainLocation())
                                use_cases[1].setTerminal(random_terminal)
                                use_cases[1].setPKIDetails(return_random_pki_details())

                                logger.info("Generating a login event at " + str(use_cases[1].getLocation()) +
                                            " terminal " + str(use_cases[1].getTerminal().getTerminalName()) +
                                            " for user " + str(use_cases[1].getUser().getBadgeNumber()) +
                                            " with PKI details " + str(use_cases[1].getPKIDetails()) +
                                            " at time " + str(event_time))

                                use_cases[1].getUser().loginEmployee(use_cases[1].getLocation(),
                                                                     use_cases[1].getTerminal(),
                                                                     SUCCESS,
                                                                     use_cases[1].getPKIDetails(),
                                                                     event_time)

                            elif use_cases[1].getCurrentStep().getStepAction() == "LOGOUT":
                                logger.info("Generating a logout event at " +
                                            str(use_cases[1].getLocation()) +
                                            " terminal " +
                                            str(use_cases[1].getTerminal().getTerminalName()) +
                                            " for user " + str(use_cases[1].getUser().getBadgeNumber()) +
                                            " at time " + str(event_time))

                                use_cases[1].getUser().logoutEmployee(use_cases[1].getLocation(),
                                                                      use_cases[1].getTerminal(),
                                                                      SUCCESS,
                                                                      event_time)

                            elif use_cases[1].getCurrentStep().getStepAction() == "UNPLUG":

                                logger.info("Generating a device unplug event at " +
                                            str(use_cases[1].getLocation()) +
                                            " terminal " +
                                            str(use_cases[1].getTerminal().getTerminalName()) +
                                            " for user " + str(use_cases[1].getUser().getBadgeNumber()) +
                                            " at time " + str(event_time))

                                use_cases[1].getDevice().unPlug(use_cases[1].getUser().getBadgeNumber(),
                                                                use_cases[1].getLocation(),
                                                                use_cases[1].getTerminal(),
                                                                event_time)

                            elif use_cases[1].getCurrentStep().getStepAction() == "PLUGIN":

                                random_device = return_random_device()
                                use_cases[1].setDevice(random_device)

                                logger.info("Generating a device plug in event at " +
                                            str(use_cases[1].getLocation()) +
                                            " terminal " +
                                            str(use_cases[1].getTerminal().getTerminalName()) +
                                            " for user " + str(use_cases[1].getUser().getBadgeNumber()) +
                                            " at time " + str(event_time))

                                use_cases[1].getDevice().plugIn(use_cases[1].getUser().getBadgeNumber(),
                                                                use_cases[1].getLocation(),
                                                                use_cases[1].getTerminal(),
                                                                SUCCESS,
                                                                event_time)

                            elif use_cases[1].getCurrentStep().getStepAction() == "UNPLUG WITHOUT LOGIN":

                                random_terminal = return_random_terminal(use_cases[1].getUser().getMainLocation())
                                use_cases[1].setTerminal(random_terminal)

                                logger.info("Generating a device unplug event at " +
                                            str(use_cases[1].getLocation()) +
                                            " terminal " +
                                            str(use_cases[1].getTerminal().getTerminalName()) +
                                            " for user " + str(use_cases[1].getUser().getBadgeNumber()) +
                                            " at time " + str(event_time))

                                use_cases[1].getDevice().unPlug(use_cases[1].getUser().getBadgeNumber(),
                                                                use_cases[1].getLocation(),
                                                                use_cases[1].getTerminal(),
                                                                event_time)

                            elif use_cases[1].getCurrentStep().getStepAction() == "LOGIN CIRCUS":
                                logger.info("Generating a CIRCUS login  event for user " +
                                            str(use_cases[1].getUser().getBadgeNumber()) +
                                            " at time " + str(event_time))
                                use_cases[1].getUser().loginCircus(SUCCESS, event_time)
                            elif use_cases[1].getCurrentStep().getStepAction() == "PERFORM CIRCUS SEARCH":
                                logger.info("Generating a CIRCUS search event for user " +
                                            str(use_cases[1].getUser().getBadgeNumber()) +
                                            " at time " + str(event_time))
                                use_cases[1].getUser().performCircusOperation("SEARCH",
                                                                              SUCCESS,
                                                                              event_time)
                            elif use_cases[1].getCurrentStep().getStepAction() == "PERFORM CIRCUS PRINT":
                                logger.info("Generating a CIRCUS print event for user " +
                                            str(use_cases[1].getUser().getBadgeNumber()) +
                                            " at time " + str(event_time))
                                use_cases[1].getUser().performCircusOperation("PRINT",
                                                                              SUCCESS,
                                                                              event_time)
                            elif use_cases[1].getCurrentStep().getStepAction() == "LOGOUT CIRCUS":
                                logger.info("Generating a CIRCUS logout event for user " +
                                            str(use_cases[1].getUser().getBadgeNumber()) +
                                            " at time " + str(event_time))
                                use_cases[1].getUser().logoutCircus(event_time)

                            elif use_cases[1].getCurrentStep().getStepAction() == "LOGIN STRUCTURE":
                                logger.info("Generating a STRUCTURE login event for user " +
                                            str(use_cases[1].getUser().getBadgeNumber()) +
                                            " at time " + str(event_time))
                                use_cases[1].getUser().loginStructure(SUCCESS, event_time)
                            elif use_cases[1].getCurrentStep().getStepAction() == "PERFORM STRUCTURE SEARCH":
                                logger.info("Generating a STRUCTURE search event for user " +
                                            str(use_cases[1].getUser().getBadgeNumber()) +
                                            " at time " + str(event_time))
                                use_cases[1].getUser().performStructureOperation("SEARCH",
                                                                                 SUCCESS,
                                                                                 event_time)
                            elif use_cases[1].getCurrentStep().getStepAction() == "PERFORM STRUCTURE PRINT":
                                logger.info("Generating a STRUCTURE print event for user " +
                                            str(use_cases[1].getUser().getBadgeNumber()) +
                                            " at time " + str(event_time))
                                use_cases[1].getUser().performStructureOperation("PRINT",
                                                                                 SUCCESS,
                                                                                 event_time)
                            elif use_cases[1].getCurrentStep().getStepAction() == "LOGOUT STRUCTURE":
                                logger.info("Generating a STRUCTURE logout event for user " +
                                            str(use_cases[1].getUser().getBadgeNumber()) +
                                            " at time " + str(event_time))
                                use_cases[1].getUser().logoutStructure(event_time)

                            elif use_cases[1].getCurrentStep().getStepAction() == "LOGIN VOYAGER":
                                logger.info("Generating a VOYAGER login event for user " +
                                            str(use_cases[1].getUser().getBadgeNumber()) +
                                            " at time " + str(event_time))
                                use_cases[1].getUser().loginVoyager(SUCCESS, event_time)
                            elif use_cases[1].getCurrentStep().getStepAction() == "PERFORM VOYAGER SEARCH":
                                logger.info("Generating a VOYAGER search event for user " +
                                            str(use_cases[1].getUser().getBadgeNumber()) +
                                            " at time " + str(event_time))
                                use_cases[1].getUser().performVoyagerOperation("SEARCH",
                                                                               SUCCESS,
                                                                               event_time)
                            elif use_cases[1].getCurrentStep().getStepAction() == "PERFORM VOYAGER PRINT":
                                logger.info("Generating a VOYAGER print event for user " +
                                            str(use_cases[1].getUser().getBadgeNumber()) +
                                            " at time " + str(event_time))
                                use_cases[1].getUser().performVoyagerOperation("PRINT",
                                                                               SUCCESS,
                                                                               event_time)
                            elif use_cases[1].getCurrentStep().getStepAction() == "LOGOUT VOYAGER":
                                logger.info("Generating a VOYAGER logout event for user " +
                                            str(use_cases[1].getUser().getBadgeNumber()) +
                                            " at time " + str(event_time))
                                use_cases[1].getUser().logoutVoyager(event_time)

                            elif use_cases[1].getCurrentStep().getStepAction() == "PRINT DIRECT":

                                logger.info("Generating a direct print event for user " +
                                            str(use_cases[1].getUser().getBadgeNumber()) +
                                            " at time " + str(event_time))

                                random_pages = random.randint(1, 30)
                                random_size = (random_pages * random.randint(500, 1000))
                                doc_name = ('DOC_' + datetime.datetime.today().strftime(FILENAME_DATE_FORMAT) +
                                            '.doc')

                                actual_printer = return_random_direct_printer(use_cases[1].getLocation())

                                actual_printer.printDocument(use_cases[1].getUser().getBadgeNumber(),
                                                             event_time,
                                                             doc_name,
                                                             random_pages,
                                                             random_size,
                                                             return_random_marking(),
                                                             main_print_queue)

                            elif use_cases[1].getCurrentStep().getStepAction() == "PRINT TO QUEUE":

                                logger.info("Generating a print to queue event for user " +
                                            str(use_cases[1].getUser().getBadgeNumber()) +
                                            " at time " + str(event_time))

                                random_pages = random.randint(1, 30)
                                random_size = (random_pages * random.randint(500, 1000))
                                doc_name = ('DOC_' + datetime.datetime.today().strftime(FILENAME_DATE_FORMAT) +
                                            '.doc')

                                actual_printer = return_random_pull_printer(use_cases[1].getLocation())

                                actual_printer.printDocument(use_cases[1].getUser().getBadgeNumber(),
                                                             event_time,
                                                             doc_name,
                                                             random_pages,
                                                             random_size,
                                                             return_random_marking(),
                                                             main_print_queue)

                            elif use_cases[1].getCurrentStep().getStepAction() == "PULL PRINTS FROM QUEUE":

                                logger.info("Generating a pull print from queue event for user " +
                                            str(use_cases[1].getUser().getBadgeNumber()) +
                                            " at time " + str(event_time))

                                current_print_queue = main_print_queue.getJobQueue()
                                current_location = use_cases[1].getLocation()
                                actual_printer = return_random_pull_printer(use_cases[1].getLocation())

                                # JOB_ID, BADGE_NUMBER

                                if len(current_print_queue) > 0:

                                    for jobs in current_print_queue:
                                        if (jobs[1] == use_cases[1].getUser().getBadgeNumber()):
                                            main_print_queue.pullQueuedDocument(jobs[1],
                                                                                jobs[0],
                                                                                current_location,
                                                                                actual_printer,
                                                                                event_time)

                            elif use_cases[1].getCurrentStep().getStepAction() == "PLUGIN WITHOUT LOGIN":

                                random_device = return_random_device()
                                use_cases[1].setDevice(random_device)

                                random_terminal = return_random_terminal(use_cases[1].getLocation())
                                use_cases[1].setTerminal(random_terminal)

                                logger.info("Generating a device plug in event at " +
                                            str(use_cases[1].getLocation()) +
                                            " terminal " +
                                            str(use_cases[1].getTerminal().getTerminalName()) +
                                            " for user " + str(use_cases[1].getUser().getBadgeNumber()) +
                                            " at time " + str(event_time))

                                use_cases[1].getDevice().plugIn(use_cases[1].getUser().getBadgeNumber(),
                                                                use_cases[1].getLocation(),
                                                                use_cases[1].getTerminal(),
                                                                SUCCESS,
                                                                event_time)
                            else:
                                logger.error("Invalid action specified in Use-Case")

                            use_cases[1].getNextStep()
                    else:
                        use_cases[1].setActive()

            except Exception as use_case_queue_ex:
                logger.error("Exception raised in the use-case queue check code!")
                logger.info(str(use_case_queue_ex))

            # Device specific events including anomalous events for Use Case 1(a, b & c)
            if RandomChance("HIGH"):

                random_device = return_random_device()

                # If the randomly chosen device is assigned to a user and the user is currently logged in
                if ((random_device.getOwner() is not None) and (users[random_device.getOwner()].isLoggedIn())):
                    # users[random_device.getOwner()].displayDetails()
                    # Either plug in or unplug the device dependant on its current state
                    try:
                        if random_device.isPluggedIn():
                            random_device.unPlug(random_device.getOwner(),
                                                 users[random_device.getOwner()].getCurrentLocation(),
                                                 users[random_device.getOwner()].getCurrentTerminal(),
                                                 event_time)
                        else:
                            random_device.plugIn(random_device.getOwner(),
                                                 users[random_device.getOwner()].getCurrentLocation(),
                                                 users[random_device.getOwner()].getCurrentTerminal(),
                                                 return_random_outcome(),
                                                 event_time)
                    except Exception as plug_unplug:
                        logger.debug("Exception raised when plugging in or unplugging and owned device")
                        logger.debug(str(plug_unplug))
                else:
                    if RandomChance("MEDIUM"):
                        # The device is owned by a user but that user is not currently logged in
                        # Set a messahe string (for later) accordingly.
                        if random_device.getOwner() is not None:
                            message_string = ("Generating an anomalous event for device assigned to user " +
                                              str(random_device.getOwner()))
                            device_user = random_device.getOwner()
                        # The device is not owned by a user
                        else:
                            message_string = ("Generating an anomalous event for unassigned device " +
                                              str(random_device.getDeviceName()))
                            device_user = return_random_badge()
                        # If a chance factor is met then adjust the device proporties (if the device is
                        # either a KEYBOARD or MOUSE) so that they have a "capacity" greater than zero.
                        # This is for the use case where a device is mis-identified.
                        if RandomChance("LOW"):

                            if ((random_device.getDeviceType() == "KEYBOARD") or
                                (random_device.getDeviceType() == "MOUSE")):
                                random_device.setCapacity("100")

                        if users[device_user].isLoggedIn():

                            logger.debug(message_string)

                            if random_device.isPluggedIn():

                                try:
                                    random_device.unPlug(device_user,
                                                         users[device_user].getCurrentLocation(),
                                                         users[device_user].getCurrentTerminal(),
                                                         event_time)
                                except Exception as unplug:
                                    logger.error("Exception in anomalous event unplug code : " + str(unplug))

                            else:

                                try:

                                    if random_device.getOwner() is None:
                                        anomaly_location = return_random_location()
                                        random_device.plugIn(device_user,
                                                             anomaly_location,
                                                             return_random_terminal(anomaly_location),
                                                             return_random_outcome(),
                                                             event_time)
                                    else:
                                        random_device.plugIn(device_user,
                                                             users[random_device.getOwner()].getCurrentLocation(),
                                                             users[random_device.getOwner()].getCurrentTerminal(),
                                                             return_random_outcome(),
                                                             event_time)

                                except Exception as plugin:
                                    logger.error("Exception in anomalous event plug in code : " + str(plugin))

            # Herein lies the main body of the User (as opposed to Device) code.
            if RandomChance("HIGH"):
                random_user = return_random_badge()

                # There's a high likelihood that we're going to want to log into a phone
                # if the user is swiped into a building and potentially logged into their IT
                if RandomChance("HIGH"):
                    # I did wonder if this logic was sound but it does cater for the use case
                    # where a user is logged into their IT but we can't ascertain whether they're
                    # in a building or not.
                    if ((users[random_user].isLoggedIn()) or (users[random_user].isInBuilding())):
                        # If they're logged into a phone log off and vice versa
                        try:

                            if (not users[random_user].isLoggedIntoPhone()):
                                random_phone = return_random_phone(users[random_user].getCurrentLocation())

                                if random_phone is not None:
                                    users[random_user].loginPhone(random_phone, event_time)
                                    logger.debug("Login phone " + random_phone.getPhoneName() +
                                                " for user : " + str(random_user))
                                else:
                                    logger.debug("No phones available for login at location : " +
                                                str(users[random_user].getCurrentLocation()))
                            else:
                                logger.debug("Log out the phone for user : " + str(random_user))
                                users[random_user].logoutPhone(event_time)

                        except Exception as phone_ex:
                            logger.error("Exception raised in the login/logout phone section")
                            logger.debug(str(phone_ex))

                # If the user is already logged into their IT
                if users[random_user].isLoggedIn():
                    # There's a MEDIUM chance that they'll logout
                    if RandomChance("MEDIUM"):
                        try:
                            logger.info("Generating a logout event at " +
                                        str(users[random_user].getCurrentLocation()) +
                                        " terminal " +
                                        str(users[random_user].getCurrentTerminal().getTerminalName()) +
                                        " for user " + str(random_user) +
                                        " at time " + str(event_time))
                            users[random_user].logoutEmployee(users[random_user].getCurrentLocation(),
                                                              users[random_user].getCurrentTerminal(),
                                                              return_random_outcome(),
                                                              event_time)
                        except Exception as logout_ex:
                            users[random_user].displayDetails()
                            logger.info("Exception raised within the AD logout section of the main loop")

                    # If they're not going to logout then they can do a random smattering of work.
                    else:

                        if RandomChance("MEDIUM"):
                            create_phone_events(event_time)

                        if RandomChance("MEDIUM"):
                            create_email_events(event_time)

                        if RandomChance("MEDIUM"):
                            create_circus_events(event_time)
                            create_structure_events(event_time)
                            create_voyager_events(event_time)

                        if RandomChance("MEDIUM"):
                            # We should probably generate some pull-print events here as well
                            create_print_events(event_time)

                # If the user is in a building but not logged into their IT then do some relecant stuff
                else:
                    # Okay, so they're actually in the building
                    if users[random_user].isInBuilding():
                        # Create some pull-print events
                        if RandomChance("MEDIUM"):
                            create_print_queue_pull_events(event_time)

                        # Maybe swipe them out of the building?
                        if RandomChance("MEDIUM"):

                            try:
                                logger.info("Generating a swipe out event at " +
                                            str(users[random_user].getCurrentLocation()) +
                                            " for user " + str(random_user) +
                                            " at time " + str(event_time))
                                users[random_user].swipeOutEmployee(users[random_user].getCurrentLocation(),
                                                                    return_random_door(users[random_user].getCurrentLocation()).getDoorName(),
                                                                    return_random_outcome(),
                                                                    event_time)

                            except Exception as swipeout_ex:
                                logger.error("Exception in the swipe out section of the main code")
                                logger.debug(str(swipeout_ex))

                        # Randomly log the user in to their IT
                        elif RandomChance("HIGH"):

                            try:
                                random_terminal = return_random_terminal(users[random_user].getCurrentLocation())

                                if RandomChance("RARE"):
                                    logger.debug("Supplying random PKI details!")
                                    login_pki_details = return_random_pki_details()[1]
                                    logger.debug("Before = " + users[random_user].getPKIDetails())
                                    logger.debug("After = " + login_pki_details)
                                else:
                                    login_pki_details = users[random_user].getPKIDetails()

                                logger.info("Generating a login event at " +
                                            str(users[random_user].getCurrentLocation()) +
                                            " terminal " + str(random_terminal.getTerminalName()) +
                                            " type " + str(random_terminal.getTerminalType()) +
                                            " for user " + str(random_user) +
                                            " at time " + str(event_time))

                                users[random_user].loginEmployee(users[random_user].getCurrentLocation(),
                                                                 random_terminal,
                                                                 return_random_outcome(),
                                                                 login_pki_details,
                                                                 event_time)
                            except Exception as login_ex:
                                logger.error("Exception raised in AD login code within the main loop")
                                logger.debug(str(login_ex))

                    # Okay, so the user's not in the building so we should think about swiping them in
                    else:
                        try:
                            if RandomChance("MEDIUM"):
                                logger.info("Generating a swipe in event at " +
                                            str(users[random_user].getMainLocation()) +
                                            " for user " + str(random_user) +
                                            " at time " + str(event_time))
                                users[random_user].swipeInEmployee(users[random_user].getMainLocation(),
                                                                   return_random_door(users[random_user].getMainLocation()).getDoorName(),
                                                                   return_random_outcome(),
                                                                   event_time)
                        except Exception as swipein_ex:
                            logger.error("Exception raised when attempting to generate a door swipe in event")
                            logger.debug(str(swipein_ex))

            # On random occasions generate an event that accounts for one of the defined
            # use cases.
            if RandomChance("RARE"):
                logger.debug("Generating an anomalous event at time " + str(event_time) +
                             " for user " + str(random_user))

            # event_time = datetime.timedelta(milliseconds=granularity)
            event_time = datetime.datetime.today()

            if continuous:
                time.sleep(0.001*granularity)

        except KeyboardInterrupt:
            logger.debug("Event_time = " + str(event_time))
            sys.exit("\nInterrupted!\n")

        except Exception as e:
            logger.error("Unhandled exception in main loop : " + str(e))

    logger.debug("Run complete!")


populate_lists()


if __name__ == "__main__":
    main()
