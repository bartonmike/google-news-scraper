# NAME: article_scraper.py
#
# article_create.py MUST BE RUN BEFORE THIS CODE (only once to initialize the google sheet)
#
# Python Version Tested With: 3.12.2 / 3.12.3 / 3.9.18
#
# Author: Carter Deal
#         Anderson Lab
#         Oregon State University
# 
# Description: This program takes data from a google sheet file concerning certain subjects/people and searches for them in both
#               Google news and Bing news. The program takes in the First name, Last name, and affiliaation of people and generates 
#               search prompts based on the prompt formatting templates provided and the affiliation definitions provided, 
#               aswell as filters those searches by a date if it is entered. The prompts entered will be searched exactly, meaning that the
#               articles have to contain the prompt in them, no similarity searching for the prompt itself (but there will be similarity checking
#               between the articles themselves). If the file finds a duplicate article within the 
#               same person/theme, it flags it. Once all the articles are found, they are
#               extracted and are output into a google sheets file. There is a text files named search_terms, prompt_formatting, custom_terms, and affiliations that store the 
#               previous inputs, then logs any changes on the third sheet in the google sheet document.
#               
# Inputs: First Name, Last Name, Affiliation table/entries. 
#         Custom Prompts (optional)
#         Prompt Formatting (Templates)
#         Affiliations (optional)
#         Date/Time (optional)
#
#
# Outputs: 
#           Command line: iterating through search prompts with notifications of duplicate or addition to csv for each article
#               
#           Files: outputs a google sheet containing all articles found for each prompt, with Article URL,  Title, browser (Google and/or Bing),
#                   and search prompts as headers and data entries, aswell as a notes section for each article. Run logs and Prompt History will also be outputted in the google sheet
#

################################################################################ IMPORTS ##################################################################################################

###### Google news and general imports
from gnews import GNews # pip3 install gnews, pip3 install newspaper3k, pip3 install lxml[html_clean]
import time
import random
import os
from newspaper import Config
from datetime import date, datetime, timedelta
from dateutil.relativedelta import relativedelta
from bs4 import BeautifulSoup # pip3 install beautifulsoup4
import requests # pip3 install requests
from difflib import SequenceMatcher
from htmldate import find_date #pip3 install htmldate, pip3 install charset_normalizer==2.0.0
import logging
from fake_useragent import UserAgent # pip3 install fake_useragent

####### openai import
from openai import OpenAI # pip3 install openai

####### progress bar
from tqdm import tqdm, trange

####### bing search imports (selenium)
from selenium import webdriver # pip3 install selenium
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

####### gspread imports (api to access google sheets)
import gspread # pip3 install gspread
from oauth2client.service_account import ServiceAccountCredentials # pip3 install oauth2client
from gspread.utils import ValidationConditionType

############################################################################### USER INPUTS ################################################################################################
#------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------#
#------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------#
#------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------#
#------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------#
#------------------------------------------------------------------ENTER OPENAPI KEY IN THE QUOTATION MARKS--------------------------------------------------------------------------------#

ai = OpenAI(api_key = "")

#------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------#
#------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------#
#------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------#
#------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------#
#------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------#
############################################################################## DEFINED FUNCTIONS ###########################################################################################

# similarity matcher, returns percentage of similarity between two given strings
def similar(a, b):
    return SequenceMatcher(None, a, b).ratio()


# function that formats and organizes the prompts into a 2d array that the program can read
# the top level of the array is the different themes/people and the 2nd level is the individual search terms
def organize_prompts(prompts):

    temp_date = None # variable that stores the date entered in search_terms
    new_prompts = [] # 2d array that stores the temp_prompt of each person
    temp_prompts = [] # stores lines for one person

    # loop through all lines
    for num in range(len(prompts)):
        prompts[num] = prompts[num].strip()

        # hit the date separator, end of file, store line ahead as date and break from loop
        if(prompts[num] == "/"):
            new_prompts.append(temp_prompts)
            if(num + 1 <= len(prompts) - 1):
                temp_date = prompts[num + 1]
                break
        # hit empty line, emptying the temp_prompts of the person into the 2d array, resetting for a new person
        if(prompts[num] == ""):
            new_prompts.append(temp_prompts)
            temp_prompts = []
        # separate the prompts from |, format and add them into the temp_prompts
        else:
            arr = prompts[num].split(' | ')
            temp = ""

            for item in arr:
                temp += '"' + item + '" '

            temp_prompts.append(temp)

            if(num >= len(prompts) - 1): # adds the last item in the list (this triggers if there is no date)
                new_prompts.append(temp_prompts)
    
    return new_prompts, temp_date


# function that compares two arrays of strings and finds the removed and added values of the new string in comparison
# to the old string, returns string of the added and removed values 
def compare_people(new_people,old_people):
    diff_removed = []
    diff_added = []

    # added items
    for person in new_people:
        if person == '/':
            break
        not_found = 1
        for old_person in old_people:
            if old_person == '/':
                break
            if person in old_person:
                not_found  = 0
            
        if not_found:
            diff_added.append('"' + person + '"')

    str_diff1 = ' '.join(diff_added)

    # removed items
    for person in old_people:
        if person == '/':
            break
        not_found = 1
        for new_person in new_people:
            if new_person == '/':
                break
            if person in new_person:
                not_found  = 0
            
        if not_found:
            diff_removed.append('"' + person + '"')

    str_diff2 = ' '.join(diff_removed)

    return str_diff1, str_diff2

############################################################################## PROGRAM STARTS ###########################################################################################

ua = UserAgent()

logger = logging.getLogger('htmldate.utils')
logger.disabled = True

prompts = [] # stores all lines in file

max_results = 1000; # max results that the program will search for (bing search will match or go a little over)

# initializing sheets
scope = [
    'https://www.googleapis.com/auth/spreadsheets',
    'https://www.googleapis.com/auth/drive'
    ]

file_name = os.path.dirname(os.path.abspath(__file__)) + '/client_key.json'

creds = ServiceAccountCredentials.from_json_keyfile_name(file_name,scope)
client = gspread.authorize(creds)

f = open(os.path.dirname(os.path.abspath(__file__)) + '/article_name.txt', 'r')
article_name = f.readlines()[0].strip()

sheet = client.open(article_name).worksheet('Prompts')
Run_Log = client.open(article_name).worksheet('Run_Log')

people = []
row_values = []
index = 7

prompts = []
prompt = []

# reading the affiliation definitions, organizing them and separate the definitions from the terms
affiliation_definitions_sheet = sheet.cell(3,3).value

if(affiliation_definitions_sheet != None):
    affiliation_definitions = affiliation_definitions_sheet.split('\n')
    raw_affiliations = affiliation_definitions_sheet.split('\n')
    for i in range(len(affiliation_definitions)):
        affiliation_definitions[i] = affiliation_definitions[i].split(' = ')
        affiliation_definitions[i][1] = affiliation_definitions[i][1].split(', ')

prompt_templates = sheet.cell(3,1).value

# if there is no prompt templates, then there is nothing to run
if(prompt_templates == None):
    Run_Log.append_row(['PROMPT ERROR', 'NO PROMPT FORMATTING. Not running news search...', str(date.today())])
    exit()
else:
    prompt_templates = prompt_templates.split('\n')

# read all the people listed in prompts on the sheet
while True:
    row_values = sheet.row_values(index)
    if(row_values == []):
        break
    index = index + 1
    
    people.append(row_values)

    time.sleep(1)

new_people = []

# create a string combining first, last, and affiliation into one string
for person in people:
    new_people.append(' '.join(person))

for person in people:
    prompt = []

    affiliations = person[2].split('/')

    for institution in affiliations:
        # defaualt search terms, just the raw words given
        for template in prompt_templates:
            prompt.append(template.replace('First Name', person[0]).replace('Last Name', person[1]).replace('Affiliation', institution).replace('" "', ' | ').replace('"',''))
        # if there is a definition/s that matches the affiliation/s given for the person, add all the variations to their prompts
        for definition in affiliation_definitions:
            if definition[0].strip() == institution.strip():
                for definition_variation in definition[1]:
                    for template in prompt_templates:
                        prompt.append(template.replace('First Name', person[0]).replace('Last Name', person[1]).replace('Affiliation', definition_variation).replace('" "', ' | ').replace('"',''))
    # if there is an empty prompt, remove it
    for i in range(len(prompt)):
        if prompt[i].strip() == '':
            prompt.pop(i)

    prompts.append(prompt)

text = ''

datesheet = sheet.cell(5,3).value
counter = 0

############################################################################ ACCESS GOOGLE SHEETS / CHECK AND UPDATE PROMPTS ##################################################################################
#Google sheets initialization
#Authorize the API
scope = [
    'https://www.googleapis.com/auth/spreadsheets',
    'https://www.googleapis.com/auth/drive'
    ]
file_name = os.path.dirname(os.path.abspath(__file__)) + '/client_key.json'
creds = ServiceAccountCredentials.from_json_keyfile_name(file_name,scope)
client = gspread.authorize(creds)

sheet = client.open(article_name).worksheet('Prompts') # opening the prompts section of the sheet

# opening the prompt history of the sheet, it should be named 'Prompt_History'
link_history_sheet = client.open(article_name).worksheet('Prompt_History')

# open custom prompts
sheet_cust_prompts = sheet.cell(5,1).value

# format the custom prompts and add them to the actual prompts array
if(sheet_cust_prompts != None):
    cust_formatted, empty_date = organize_prompts(sheet_cust_prompts.split('\n'))

    for section in cust_formatted:
        section_found = False
        x = 0
        # try to locate if they are accessing a person, add the prompt to that person if found
        for person in people:
            string_person = ' '.join(person)
            if(string_person in section[0]):
                section_found = True
                for i in range(len(section)):
                    if (i != 0):
                        prompts[x].append(section[i].replace('" "', ' | ').replace('"',''))
            x += 1
        # if they did not find the person, add the prompt to the end
        if(section_found == False):
            new_person = []
            for i in range(len(section)):
                new_person.append(section[i].replace('" "', ' | ').replace('"',''))

            prompts.append(new_person)
# format the array of prompts to one single text
for prompt in prompts:
    counter += 1
    for item in prompt:
     text += str(item) + '\n'
    if(counter == len(prompts)):
        text += '/\n' + datesheet
    else:
        text += "\n"
# update new prompts array to sheet
sheet.update_cell(1,1,text)
# read prompts and date from sheet, organize them
new_prompts, new_temp_date = organize_prompts(sheet.cell(1,1).value.split('\n'))

# open previous prompts from text file
with open(os.path.dirname(os.path.abspath(__file__)) + "/search_terms.txt", 'r', encoding = 'utf-8') as file:
    old_people = file.readlines()

date_found = 0

# strip the lines of the text
for i in range(len(old_people)):
    old_people[i] = old_people[i].strip()

# append the date to the new people array
new_people.append('/')
new_people.append(new_temp_date)

old_temp_date = None 

# find the date in the text file, assign it to variable
if(len(old_people) > 2):
    if '/' in old_people[len(old_people) - 2]:
        old_temp_date = old_people[(len(old_people) - 1)]
# find the custom prompts
if(sheet.cell(5,1).value != None):
    custom_prompts = sheet.cell(5,1).value.split('\n')
else:
    custom_prompts = ''

# open all the remaining text files and strip their values
with open(os.path.dirname(os.path.abspath(__file__)) + "/custom_terms.txt", 'r', encoding = "utf-8") as file:
    custom_prompts_file = file.readlines()

for i in range(len(custom_prompts_file)):
    custom_prompts_file[i] = custom_prompts_file[i].strip()

with open(os.path.dirname(os.path.abspath(__file__)) + "/prompt_formatting.txt", 'r', encoding = "utf-8") as file:
    prompt_formatting_file = file.readlines()

for i in range(len(prompt_formatting_file)):
    prompt_formatting_file[i] = prompt_formatting_file[i].strip()

with open(os.path.dirname(os.path.abspath(__file__)) + "/affiliations.txt", 'r', encoding = "utf-8") as file:
    affiliations_file = file.readlines()

for i in range(len(affiliations_file)):
    affiliations_file[i] = affiliations_file[i].strip()

# code that checks for the amount of spaces in the new and old custom prompts
# as spaces are also a factor to denote if changes happened
cust_file_space = 0

for line in custom_prompts_file:
    if line == '':
        cust_file_space += 1

cust_space = 0

for line in custom_prompts:
    if line == '':
        cust_space += 1

cust_space_diff = 0

if cust_space != cust_file_space:
    cust_space_diff = 1

# compare the new strings with the old strings of all the editable content
cust_diff1, cust_diff2 = compare_people(custom_prompts, custom_prompts_file)
people_diff1, people_diff2 = compare_people(new_people, old_people)
aff_diff1, aff_diff2 = compare_people(raw_affiliations, affiliations_file)
form_diff1, form_diff2 = compare_people(prompt_templates, prompt_formatting_file)

# formatting the output strings
str_diff1 = 'Added:'
str_diff2 = 'Removed:'

# adding the appropriate changed values to the output strings
if(people_diff1 != ''):
    str_diff1 += '\n\tPeople:' + people_diff1
if(people_diff2 != ''):
    str_diff2 += '\n\tPeople:' + people_diff2

if(cust_diff1 != ''):
    str_diff1 += '\n\tCustom:' + cust_diff1
if(cust_diff2 != ''):
    str_diff2 += '\n\tCustom:' + cust_diff2

if(form_diff1 != ''):
    str_diff1 += '\n\tPrompt Templates:' + form_diff1
if(form_diff2 != ''):
    str_diff2 += '\n\tPrompt Templates:' + form_diff2

if(aff_diff1 != ''):
    str_diff1 += '\n\tAffiliations:' + aff_diff1
if(aff_diff2 != ''):
    str_diff2 += '\n\tAffiliations:' + aff_diff2

# checking date
if(old_temp_date != new_temp_date):
    if(old_temp_date != None):
        str_diff2 += '\n\tTime:' + '"' + old_temp_date + '"'
    if(new_temp_date != None):
        str_diff1 += '\n\tTime:' + '"' + new_temp_date + '"'

# printing to console changes
print(str_diff1 + '\n' + str_diff2)

# if there are changes
if(str_diff1.strip() != 'Added:' or str_diff2.strip() != 'Removed:'):
    # updating cell in first sheet with added and removed values
    sheet.update_cell(1,2,str_diff1 + '\n' + str_diff2)
    sheet.columns_auto_resize(0, 1)

    # appending to the second row the changes
    link_history_sheet.append_row([str_diff1 + '\n' + str_diff2, str(date.today())])
    link_history_sheet.columns_auto_resize(0, 2)

    # opening the search terms file and overwriting the new prompts
    f = open(os.path.dirname(os.path.abspath(__file__)) + "/search_terms.txt", "w")
    f.write('\n'.join(new_people))
    f.close()

if(cust_diff2.strip() != '' or cust_diff1.strip() != '' or cust_space_diff):
    c = open(os.path.dirname(os.path.abspath(__file__)) + "/custom_terms.txt", "w")
    c.write('\n'.join(custom_prompts))
    c.close()

if(form_diff2.strip() != '' or form_diff1.strip() != ''):
    c = open(os.path.dirname(os.path.abspath(__file__)) + "/prompt_formatting.txt", "w")
    c.write('\n'.join(prompt_templates))
    c.close()

if(aff_diff2.strip() != '' or aff_diff1.strip() != ''):
    c = open(os.path.dirname(os.path.abspath(__file__)) + "/affiliations.txt", "w")
    c.write('\n'.join(raw_affiliations))
    c.close()

# bing has its own date rules, initialize bing date to none (no limit)
bing_date = None

res = True

date_cutoff = None

############################################################################ FORMATTING DATE ##################################################################################
# formatting the date depending on what was on file
if (new_temp_date != None):
    # checks if the date contains week month or year
    # uses timedelta/relativedata to translate weeks/months/years
    # into a time that could be subtracted from current date
    # Saves that date an split YYYY-MM-DD into three pieces: "YYYY", "MM", "DD"
    # bing date is limited (1 week, 1 month, all time), so week translates to 1 week ago
    # month = 1 month ago, year = all time
    if "week" in new_temp_date:
        new_temp_date = new_temp_date.split(" ")
        new_temp_date = int(new_temp_date[0])
        date_cutoff = str(date.today() - timedelta(weeks=new_temp_date))
        new_temp_date = date_cutoff.split('-')
        bing_date = "8"
    else: 
        if "month" in new_temp_date:
            new_temp_date = new_temp_date.split(" ")
            new_temp_date = int(new_temp_date[0])
            date_cutoff = str(date.today() - relativedelta(months=new_temp_date))
            new_temp_date = date_cutoff.split('-')
            bing_date = "9"
        else:
            if "year" in new_temp_date:
                new_temp_date = new_temp_date.split(" ")
                new_temp_date = int(new_temp_date[0])
                date_cutoff = str(date.today() - relativedelta(years=new_temp_date))
                new_temp_date = date_cutoff.split('-')

            # if date is already entered, check formatting and split into three piece format
            else:
                format = "%Y/%m/%d"

                # checking if format matches the date 
                res = True
                
                # using try-except to check for truth value
                try:
                    res = bool(datetime.strptime(new_temp_date, format))
                    date_cutoff = new_temp_date
                except ValueError:
                    res = False

                new_temp_date = new_temp_date.split('/')

today = str(date.today()) # get today's date

end_date = today.split('-') # split today's date into three piece format

############################################################################ BEGIN SEARCH ##################################################################################
# initialize values for search
user_agent = str(ua.chrome)
config = Config()
config.browser_user_agent = user_agent
config.request_timeout = 10

# if the user entered date in file and it is formatted correctly, if not then initialize search without date range
if(new_temp_date != None) and res == True:
    google_news = GNews(max_results= max_results, end_date= (int(end_date[0]), int(end_date[1]), int(end_date[2])) , start_date = (int(new_temp_date[0]), int(new_temp_date[1]), int(new_temp_date[2])))
else:
    google_news = GNews(max_results= max_results)

# initialize data and headers for csv file
data = []
header =['URL', 'URL_Title', 'Search_Source', 'Search_Terms', 'Published Date', 'Date', 'Notes']

headers = {
            "User-Agent":
            str(ua.chrome)
            }

# iterate through 2d array, go through each person than interate through each query per person
# checks for duplicates on the per person level. If the same article shows up for the prompts of
# different people, it will show up for every person in the csv file
# also uses tqdm to create a progress bar
for person in tqdm(new_prompts):
    hit = False
    person_data = [] # reset the per person news data

    try:

        for query in person:

            #################################################### Searching Google ################################################################

            query_split = query.split('" "')
            
            # formatting the queries
            for i in range(len(query_split)):
                query_split[i] = query_split[i].replace('" ', '').replace('"', '')

            # getting the articles
            news_articles = google_news.get_news(query)
            tqdm.write('\n\n******** ' + query + '********')
            tqdm.write("--------Searching Google..............................\n")
            time.sleep(random.uniform(3,5))

            for article in news_articles:

                # base64 decoding method for google links is too unreliable
                # using the selenium method of clicking through link and waiting for redirect before
                # pulling link, python requests couldn't do it from my testing

                options = webdriver.ChromeOptions()
                options.add_experimental_option("excludeSwitches", ['enable-logging'])
                options.add_argument('--headless=new')
                options.add_argument('--log-level=3')
                options.add_argument('--no-sandbox')
                options.set_capability("browserVersion", "117")
                options.add_argument("--disable-dev-shm-usage")
                driver = webdriver.Chrome(options = options)

                driver.get(article['url'])

                time.sleep(1)

                actual_url = driver.current_url

                full_article = google_news.get_full_article(actual_url)  # newspaper3k instance, you can access newspaper3k all attributes in full_article
                    
                try:

                    Notes = ''

                    duplicate = False

                    # check for duplicate in the person's data
                    for j in person_data:
                        if j[0] == full_article.url + " " and j[1] == full_article.title:
                            duplicate = True
                    # checking for a similarity match, if there is then add match to notes
                    if not duplicate:
                        for item in person_data:
                            sim = similar(full_article.text, item[6])
                            if sim >= 0.75:
                                tqdm.write("----TOO MUCH SIMILARITY DETECTED: " + str(round(sim * 100,2)) + "%")
                                Notes += "Duplicate text with: " + item[0] + "\n"
                    
                    # if it's a duplicate, don't add it to data, if it is then do
                    if duplicate: 
                        tqdm.write('----DUPLICATE')
                        tqdm.write(full_article.title + '\n' + full_article.url + '\n')
                    else:

                        items_found = True

                        # double checking for search terms in article
                        for item in query_split:
                            if item.lower() not in full_article.text.lower():
                                items_found = False
                        # if not found add to notes
                        if not items_found:
                            Notes += "Prompt not found in article\n"
                        
                        # check for match along other categories, if there is then append the prompt to that entry
                        outside_scope_match = False
                        for item in data:
                            if item[0].strip() == full_article.url.strip():
                                tqdm.write("-----Match with another person's article-----")
                                outside_scope_match = True
                                if(query not in item[3]):
                                    item[3] += "," + query

                        # if there is no duplicate found, append it to the master array
                        if not outside_scope_match:
                            if(date_cutoff == None or full_article.publish_date == None or str(full_article.publish_date) >= date_cutoff):
                                tqdm.write('----Adding to SHEET...')
                                tqdm.write(full_article.title + '\n' + full_article.url + '\n')
                                person_data.append([full_article.url + " ", full_article.title, "Google", query, full_article.publish_date, today, full_article.text, Notes])
                            else:
                                tqdm.write('---False Positive, Date: ' + str(full_article.publish_date) + ' outside of Specified Range........')
                                tqdm.write(full_article.title + '\n' + full_article.url + '\n')
                # full_article is not reliable, if there is an error fetching data full_article is empty
                # in this instance, actual_url needs to be used
                except: 
                    tqdm.write('----TIMED OUT')

                    Notes = ''

                    duplicate = 0

                    # check for duplicates in the person's data
                    for j in person_data:
                        if j[0] == actual_url + " " and j[1] == "ARTICLE TIMED OUT WHEN FETCHING DATA":
                            duplicate = 1
                            
                    # if it's a duplicate, don't add it to data, if it is then do
                    if duplicate: 
                        tqdm.write('----DUPLICATE')
                        tqdm.write("ARTICLE TIMED OUT WHEN FETCHING DATA" + '\n' + actual_url + '\n')
                    else:
                        outside_scope_match = False
                        # checking for match in other categories, if so append query to original entry
                        for item in data:
                            if item[0].strip() == actual_url.strip():
                                tqdm.write("-----Match with another person's article-----")
                                outside_scope_match = True
                                if(query not in item[3]):
                                    item[3] += "," + query

                        # if no duplicate, append to master list of articles
                        if not outside_scope_match:
                            tqdm.write('----Adding to SHEET...')
                            tqdm.write("ARTICLE TIMED OUT WHEN FETCHING DATA" + '\n' + actual_url + '\n')
                            Notes += "Timed Out\n"
                            person_data.append([actual_url + " ",  "ARTICLE TIMED OUT WHEN FETCHING DATA", "Google", query, "ERROR FETCHING PUBLISHED DATE", today, "NONE", Notes])

                driver.close()
        
            #################################################### Searching Bing ################################################################

            tqdm.write("--------Searching Bing..............................\n")

            headers = {
            "User-Agent":
            str(ua.chrome)
            }

            query_bing = query.replace(" ","+")
            query_bing = query_bing.replace("&", "%26")
            query_bing = query_bing.replace(",", "%2C")
            query_bing = query_bing.lower()

            # initializing chrome tab and searching the bing url
            options = webdriver.ChromeOptions()
            options.add_experimental_option("excludeSwitches", ['enable-logging'])
            options.add_argument('--headless=new')
            options.add_argument('--log-level=3')
            options.set_capability("browserVersion", "117")
            driver = webdriver.Chrome(options = options)
            # building url 
            if(bing_date == None):
                url = 'https://www.bing.com/news/search?q=' + query_bing + '&qft=sortbydate%3d"1"&form=PTFTNR'
            else:
                url = 'https://www.bing.com/news/search?q=' + query_bing + '&qft=sortbydate%3d"1"+interval%3d"' + bing_date + '"&form=PTFTNR'

            driver.get(url)
            wait = WebDriverWait(driver, 3)
            new_count = 0
            old_count = 0

            products = []

            while True:
                old_count = new_count
                # waiting for news to load articles
                try:
                    products = wait.until(EC.visibility_of_all_elements_located((By.CSS_SELECTOR, ".news-card")))
                except:
                    break
                new_count = len(products)

                # scroll down to last product to trigger loading
                driver.execute_script("arguments[0].scrollIntoView();", products[len(products) - 1])

                # sleep to let additional content load
                time.sleep(2)

                # if the count didn't change, we've loaded all products on the page
                # if the count is bigger than or equal to the max, get out
                if new_count == old_count or new_count >= max_results:
                    break

            # print results
            for product in products:
                link = product.get_attribute('url')
                title = product.get_attribute('data-title')
                
                Notes = ''

                time.sleep(random.uniform(3,5))
                
                try:
                    # fetching and parsing html
                    p = requests.get(link, headers = headers, timeout=10)
                    soup = BeautifulSoup(p.text, features = "html.parser")

                    published_date = find_date(link)

                    # kill all script and style elements
                    for script in soup(["script", "style"]):
                        script.extract()    # rip it out

                    # get text
                    text = soup.get_text()

                    # break into lines and remove leading and trailing space on each
                    lines = (line.strip() for line in text.splitlines())
                    # break multi-headlines into a line each
                    chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
                    # drop blank lines
                    text = '\n'.join(chunk for chunk in chunks if chunk)

                    if "www.msn.com" in link:
                        Notes += "MSN News Link\n"

                    duplicate = False
                    # checks for duplicates in person's data
                    for j in person_data:
                        if j[0].strip() == link.strip():
                            if(j[2].strip() == "Google"):
                                j[2] = "Google,Bing"
                            duplicate = True

                    # check for similarity, add note if similarity found
                    if not duplicate:
                        for item in person_data:
                            sim = similar(text, item[6])
                            if "www.msn.com" not in link:
                                if sim >= 0.75:
                                    tqdm.write("----TOO MUCH SIMILARITY DETECTED: " + str(round(sim * 100,2)) + "%")
                                    Notes = "Duplicate text with: " + item[0] + "\n"

                    # if there is a duplicate, add it to the person's data. If there is not, don't
                    if duplicate: 
                        tqdm.write('----DUPLICATE')
                        tqdm.write(title + '\n' + link + '\n')
                    else:
                        items_found = True
                        # double check for query in article
                        for item in query_split:
                            if item.lower() not in text.lower():
                                items_found = False

                        # query not double checked in article make note
                        if not items_found:
                            Notes += "Prompt not found in article\n"
                        outside_scope_match = False

                        # locating match in other category, if there is then append query to original
                        for item in data:
                            if item[0].strip() == link.strip():
                                tqdm.write("-----Match with another person's article-----")
                                outside_scope_match = True
                                if(query not in item[3]):
                                    item[3] += "," + query

                        # if no duplicate then append to person list
                        if not outside_scope_match:
                            if(date_cutoff == None or published_date == None or published_date >= date_cutoff):
                                tqdm.write('----Adding to SHEET...')
                                tqdm.write(title + '\n' + link + '\n')
                                person_data.append([link + " ", title, "Bing", query, published_date, today, text, Notes])
                            else:
                                tqdm.write('---False Positive, Date: ' + str(published_date) + ' outside of Specified Range........')
                                tqdm.write(title + '\n' + link + '\n')
                except:
                    outside_scope_match = False

                    # looking for match in other category, if there is then append query to original
                    for item in data:
                        if item[0].strip() == link.strip():
                            tqdm.write("-----Match with another person's article-----")
                            outside_scope_match = True
                            if(query not in item[3]):
                                    item[3] += "," + query

                    # if no duplicate then append to person list
                    if not outside_scope_match:
                        tqdm.write('----Adding to SHEET...')
                        tqdm.write("ARTICLE TIMED OUT WHEN FETCHING DATA" + '\n' + link + '\n')
                        Notes += "Timed Out\n"
                        person_data.append([link + " ",  "ARTICLE TIMED OUT WHEN FETCHING DATA", "Bing", query, "ERROR FETCHING PUBLISHED DATE", today, "NONE", Notes])

            driver.close()

        # writing the person/category to the master list
        tqdm.write("--------Writing Person...............................\n")
        for hit in person_data:
            data.append([hit[0], hit[1], hit[2], hit[3], hit[4], hit[5], hit[7],'','','']) # add everything except the whole text

        Run_Log.append_row([person[0], "Entries: " + str(len(person_data)), str(date.today())])

        sheet.columns_auto_resize(0, 2)
    
    except Exception as e:

        Run_Log.append_row(["ERROR: ", str(e) , str(date.today())])

        sheet.columns_auto_resize(0, 2)

############################################################################ OPENAI API ##################################################################################
print("\n--------Initializing OpenAI API...............................")

for i in trange(len(data)): # going through all found news articles
    if not ("ARTICLE TIMED OUT WHEN FETCHING DATA" in str(data[i][1])):
    
        # using openapi to find whether the news source is local, national, or international
        news_source = ai.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {
                    "role": "user",
                    "content": "Please give a one word response to whether the given news article site is a local, national, or international news source, if it is outside the U.S.A. it is considered international: " + str(data[i][0])
                }
            ]
        )

        data[i][7] = str(news_source.choices[0].message.content)

        # trying to approximate what number region this news source is affiliated with
        epa_region = ai.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {
                    "role": "user",
                    "content": "Please only give a one number response on your best approximation on what EPA region the subject of this news article is located in: " + str(data[i][0])
                }
            ]
        )

        data[i][8] = str(epa_region.choices[0].message.content)


        # finding the name of the news source of the given article link
        news_name = ai.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {
                    "role": "user",
                    "content": "Please respond with only the name of the news source of this article link: " + str(data[i][0])
                }
            ]
        )

        data[i][9] = str(news_name.choices[0].message.content)


############################################################################ WRITING TO GSHEETS ##################################################################################

print("\n--------Writing Everything to SHEET...............................")

# open first sheet
sheet = client.open(article_name).sheet1

index = 1
titles = sheet.row_values(index)

# check for empty headers, if not there then populate them
if(str(titles) == "[]"):
    sheet.insert_row(header,index)

#find the row length of the sheet
start_rows = len(sheet.get_all_values())

# signal beginning of data
sheet.append_row(['Start of Date ' + date_cutoff + ' to ' + str(date.today())])

# populate data array with articles
index = 3
for item in data:
     item[4] = str(item[4])
     index += 1

# post articles, signal end of data
sheet.append_rows(data)
sheet.append_row(['End of Date ' + date_cutoff + ' to ' + str(date.today())])

end_rows = len(sheet.get_all_values())

# add yes or no cell to each row
if(len(data) > 0):
    sheet.add_validation('K' + str(start_rows + 2) + ":K" + str(end_rows - 1), ValidationConditionType.one_of_list, ['yes','no'], showCustomUi=True)

# size cells to fit data
sheet.columns_auto_resize(0, index)

print("\n--------DONE...............................\n")