# NAME: article_create.py
#
# Parent program: article_scraper.py
#
# Python Version Tested With: 3.12.2 / 3.12.3 / 3.9.18
#
# Author: Carter Deal
#         Anderson Lab
#         Oregon State University
# 
# Description: This program is the configuration program to article_scraper.py. It is run once the user has created a google console service account
#              and a google sheet that is shared with the account. it will add additional worksheets into the google sheet and add title text for the categories of the sheet. it will also 
#              create text files that the article_scraper needs to function. 
#
# Inputs: name of google sheet file 
#
#
# Outputs: 
#           Google sheets "Prompts", "Prompt_History", "Run_Log" worksheets, aswell as renaming the first sheet "Article_Links". Various text in each worksheet for formatting
#           "affiliations", "custom_terms", "prompt_formatting", "search_terms" txt files. 
#


# gspread imports
import gspread # pip3 install gspread
from oauth2client.service_account import ServiceAccountCredentials # pip3 install oauth2client
from gspread_formatting import * # pip3 install gspread_formatting

# initializing google sheets api
scope = [
    'https://www.googleapis.com/auth/drive',
    'https://www.googleapis.com/auth/drive.file'
    ]
file_name = 'client_key.json'
creds = ServiceAccountCredentials.from_json_keyfile_name(file_name,scope)
client = gspread.authorize(creds)

# ask user for name to google sheet that is shared to the google developer bot in client_key.json
sheet_name = input("What is the name of your google sheet?\n")

# open sheet
sheet = client.open(sheet_name)

# create article links worksheet
article_links = sheet.sheet1
article_links.update_title("Article_Links")

# create worksheets
prompts = sheet.add_worksheet("Prompts", 200, 10)
prompt_history = sheet.add_worksheet("Prompt_History",200,10)
run_log = sheet.add_worksheet("Run_Log",200,10)

# article_links headers
header =['URL', 'URL Title', 'Search Source', 'Search Terms', 'Published Date', 'Date', 'Notes', 'News Source Reach', 'EPA Region Approximation', 'News Source', 'Display on Site']

# add headers
article_links.append_row(header)

# headers for prompts
prompt_header = [['First Name', 'Last Name', 'Affiliation']]

# updating text into cells of prompts worksheet
prompts.update(range_name = 'A6:C6', values = prompt_header)
prompts.update(range_name = 'A4', values = [['Custom Prompts']])
prompts.update(range_name = 'A2', values = [['Prompt Formatting']])
prompts.update(range_name = 'C4', values = [['Date/Time']])
prompts.update(range_name = 'C2', values = [['Affiliations']])

# conditional formatting of article_links, every odd row turned grey from columns A to K, except 1st row
range_to_format = "A2:K"
rule1 = ConditionalFormatRule(
    ranges=[GridRange.from_a1_range(range_to_format, article_links)],
    booleanRule=BooleanRule(
        condition=BooleanCondition('CUSTOM_FORMULA',["=ISODD(ROW())"]),
        format=CellFormat(backgroundColor=Color(0.9, 0.9, 0.9))  # Light gray
    )
)

# 1st row of article_links set to dark grey
format_cell_range(article_links, "A1:K1", CellFormat(backgroundColor = Color(.7,.7,.7)))

# save conditional formatting for article_links
rules = get_conditional_format_rules(article_links)
rules.append(rule1)
rules.save()


# conditional formatting for prompts worksheet, every even row is turned grey from colmuns A to C, except for first 6 rows
range_to_format = "A7:C"
rule2 = ConditionalFormatRule(
    ranges=[GridRange.from_a1_range(range_to_format, prompts)],
    booleanRule=BooleanRule(
        condition=BooleanCondition('CUSTOM_FORMULA',["=ISEVEN(ROW())"]),
        format=CellFormat(backgroundColor=Color(0.9, 0.9, 0.9))  # Light gray
    )
)
# save conditional formatting for prompts worksheet
rules = get_conditional_format_rules(prompts)
rules.append(rule2)
rules.save()

# set coloring for cells in the first 6 rows of prompts worksheet
format_cell_ranges(prompts, [["A6:C6", CellFormat(backgroundColor = Color(.7,.7,.7))], 
                             ["A4:C4", CellFormat(backgroundColor = Color(.7,.7,.7))], 
                             ["A2:C2", CellFormat(backgroundColor = Color(.7,.7,.7))],
                             ['A1', CellFormat(backgroundColor = Color(.9,.9,.9))], 
                             ['A3', CellFormat(backgroundColor = Color(.9,.9,.9))], 
                             ['A5', CellFormat(backgroundColor = Color(.9,.9,.9))],
                             ['C1', CellFormat(backgroundColor = Color(.9,.9,.9))], 
                             ['C3', CellFormat(backgroundColor = Color(.9,.9,.9))], 
                             ['C5', CellFormat(backgroundColor = Color(.9,.9,.9))]])

# conditional formatting for prompt_history worksheet, every odd row is turned grey for columns A to B, except first row
range_to_format = 'A2:B'
rule3 = ConditionalFormatRule(
    ranges=[GridRange.from_a1_range(range_to_format, prompt_history)],
    booleanRule=BooleanRule(
        condition=BooleanCondition('CUSTOM_FORMULA',["=ISODD(ROW())"]),
        format=CellFormat(backgroundColor=Color(0.9, 0.9, 0.9))  # Light gray
    )
)

# save conditional formatting for prompt_history worksheet
rules = get_conditional_format_rules(prompt_history)
rules.append(rule3)
rules.save()

# set first row of prompt history to dark grey
format_cell_range(prompt_history, "A1:B1", CellFormat(backgroundColor = Color(.7,.7,.7)))

# conditional formatting for run_log worksheet, every odd row is turned grey for columns A to C, except first row
range_to_format = 'A2:C'
rule4 = ConditionalFormatRule(
    ranges=[GridRange.from_a1_range(range_to_format, run_log)],
    booleanRule=BooleanRule(
        condition=BooleanCondition('CUSTOM_FORMULA',["=ISODD(ROW())"]),
        format=CellFormat(backgroundColor=Color(0.9, 0.9, 0.9))  # Light gray
    )
)

# save conditional formatting for run_log worksheet
rules = get_conditional_format_rules(run_log)
rules.append(rule4)
rules.save()

# set color of first row of run_log to dark grey
format_cell_range(run_log, "A1:C1", CellFormat(backgroundColor = Color(.7,.7,.7)))

# prompt history header
history_header = ['Prompt Changes', 'Date']

# add prompt history header to sheet
prompt_history.append_row(history_header)

# run log header
run_log_header = ['Title', 'Message', 'Date']

# add run log header to sheet
run_log.append_row(run_log_header)

try: 
    # create search terms txt
    f = open('search_terms.txt', 'x')
    f.close()
except:
    pass # file already exists

try:
    # create custom_terms txt
    f = open('custom_terms.txt', 'x')
    f.close()
except:
    pass # file already exists

try:
    # create affiliations txt
    f = open('affiliations.txt', 'x')
    f.close()
except:
    pass # file already exists

try: 
    # create prompt formatting txt
    f = open('prompt_formatting.txt', 'x')
    f.close()
except:
    pass # file already exists

try:
    # create article name txt
    f = open('article_name.txt', 'x')
    f.close()
except:
    pass # file already exists

try:
    # write article name to the newly created article name txt
    f = open('article_name.txt', 'w')
    f.write(sheet_name)
    f.close()
except:
    pass # file already exists