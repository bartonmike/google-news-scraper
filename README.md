# Article Scraper Requirements
Python installed

Requires an installation of Chrome

gnews 

newspaper3k

lxml[html_clean]

beautifulsoup4

requests

selenium

htmldate

charset_normalizer==2.0.2

fake_useragent

gspread

oauth2client

# Google Sheets Information

This program uses the gspread python module to access and edit a Google sheet

This program uses the 1st party Google Console software with the Drive and Sheets APIs to be able to generate a 
key and account that can access and edit any Google sheet

An article that explains this method: https://medium.com/daily-python/python-script-to-edit-google-sheets-daily-python-7-aadce27846c0 

website to create project, key, and access APIs: https://console.developers.google.com/ 

This program requires a JSON file that stores the key of the account/bot that was generated from the Google developers console
and for that file to be named "client_key.json"

The Google sheets that this program makes are formatted as follows:

---first sheet (Named "Article_Links")
    The first cell of the first row stores the titles ('URL', 'URL TITLE', 'Search_Source', 'Search_Terms', 'Published Date', 'Date', 'Notes')
    The second cell of the first row stores the last removed and added prompts
    The second row stores the titles of the columns
    All the rows that follow store the article entries that were found

--second sheet (Named "Prompts")
    cell A1 - stores all the prompts that the program has made, will read, and search for
    cell B1 - stores the previous changes
    cell A3 - the cell that stores the prompt templates
    cell C3 - the cell that stores the affiliation definitions
    cell A5 - the cell that stores the custom prompts
    cell C5 - the cell that stores the date 

--third sheet (Named "Prompt_history")
    the first row - stores the titles of the table ('Prompt Changes', 'URL')
    second row and beyond - stores prompt history values

--fourth sheet (Named "Run_Log")
    first row - stores the titles of the table ('Title', 'Message', 'Date')
    second row and beyond - stores run log values, such as any errors encountered and amount of entries found for each person

# Inputs

There are 5 different sections in the Google sheet that take inputs, all on the second worksheet labeled "Prompts"

# First Name, Last Name, Affiliation Table

  This is the main input of the program. It is a table that is on row 6 and below of the prompts worksheet of the Google sheet. 
  It has three columns, "First Name", "Last Name", and "Affiliation". Each row will correspond to a certain person, and their data input into their
  respective columns. The program will use this table to generate separate prompts that will correspond to each row. It will use those prompts 
  to fetch news articles for each person entered. 

# Prompt Formatting
      These prompts are the templates that are used to generate the prompts for each person. 
  They are formatted in the same way that one would do to search specific prompts on a web browser. 
  to search for an exact phrase one must put it in quotation marks "like so". This program supports only 
  exact phrases, so the prompt templates must be in quotation marks. Each line denotes one individual search, a search can 
  contain multiple quotation mark queries "such as this" and "with this". 
      How the template takes values from the people is it uses keywords to be able to insert the information of the person. 
  This program takes in a person's first name, last name, and affiliation to be able to search news for them, a template should include those
  inside so that the program can properly search for them. when you write, 'First Name', 'Last Name', and 'Affiliation' into the template it will replace them with the relative data for the person. 
      
  An example of prompt formatting is as follows: 

      "First Name Last Name" "Affiliation"
      
      "Last Name, First Name" "Affiliation"
      
      "Dr. Last Name" "Affiliation"

  These templates will be filled with the relative data of each person and generate all variations of the data until it has a comprehensive list
  of prompts for each person

# Affiliations

  These prompts add additional definitions for an affiliation which enables the program to create new variations on the prompts of a person. 
  An additional definition of an affiliation provides more detail and reaches into searching for someone, for example, an article might not contain 
  OSU within it, but it might contain "Oregon State University", therefore being able to search for both terms would yield a more accurate list. 

  How these inputs work is through a variable/assignment type statement. You input the affiliation that you would put in the affiliations column in the 
  person list, type an equal, then the alternate definition of such affiliation, for example, "OSU = Oregon State University". If you want to add another 
  separate definition, just write it on the other line. If there is an affiliation with multiple alternate definitions, then separate it with a comma, for example
  "UO = University of Oregon, U of O". 
  
  An example of an affiliations entry is as follows: 

      OSU = Oregon State University
      
      UO = University of Oregon, U of O
      
      OHSU = Oregon Health and Science University

# Custom Prompts

  The custom prompts section is a very powerful section when it comes to additional customization. If there is a subject that doesn't fit the first name, last name, or affiliation
  format, it can be entered here. The only caveat here is that each individual search entry has to be entered manually instead of being generated. 

Prompts line formatting is as follows:

  each line corresponds to a search on the web browser, all prompts entered on the same line will be searched together at once

  each prompt is separated by a " | " (including the spaces on either side.). The verticle line MUST HAVE SPACES ON EITHER SIDE

    example: 

        prompt1 otherwordinprompt1 | prompt2 otherwordinprompt2 

        is the same as if you entered this into the web browser: 

        "prompt1 otherwordinprompt1" "prompt2 otherwordinprompt2" 

  the code WILL ERROR if it is not entered in this way.
  If the search only has one prompt you do not have to put in the " | "

Prompts person/theme separation formatting: 

  if you are searching through multiple subjects, each with its own bundles of search lines, it is best to separate them 
  with a blank line. The code will recognize the blank line and separate the subjects. 

  This method is beneficial if the themes/subjects overlap, but you want the CSV to show the same article for each person/subject instead of for just one.
  In other words, the program only checks and discards duplicate articles within a given person/subject bundle, NOT for all the entries. 

  IF THERE IS A SPACE IN AN EMPTY LINE THE PROGRAM WILL NOT INTERPRET IT AS A SEPARATOR. IT NEEDS TO BE A COMPLETE BLANK LINE


There is also additional functionality if you want to add a custom prompt to a person that is entered in the first name, last name, affiliation table. 
All you have to do is preface your prompts in the previous line with the First Name, Last Name, and Affiliation, separated with spaces, of the person you would like to append 
the custom prompt with. For example, if I would like to append a custom prompt 'Artificial Intelligence | Jensen Huang' to my table entry of Jensen | Huang | NVIDIA (First|Last|Affiliation)
then I would put as follows into the Custom Prompts section: 

  Jensen Huang NVIDIA
  Artificial Intelligence | Jensen Huang


FULL EXAMPLE FOR A Custom_Prompts Entry:

Prompts start:

    Jensen Huang NVIDIA
    Artificial Intelligence | Jensen Huang
    
    Neil Tyson Hayden Planetarium
    Astrophysics | Black Holes
    
    Apple | Apple Intelligence
    Macbook Air | Apple 
    
    Microsoft | Open AI | Chat GPT | Sam Altman
    
    Bill Gates | Microsoft
    Gates, Bill | Microsoft

Prompts end

The program will search the first line for any similarities in the first name, last name, and affiliation table. If there is a match, then that subject will be added. 
In the example I am trying to search for 'Jensen Huang NVIDIA' and 'Neil Tyson Hayden Planetarium' in my table, so if the table has a match those prompts after would be appended. 
The other ones, since there is a ' | ' in them, will find no entries in the table, therefore they will be added as their separate subject and entry. 


# Date/TIme

Prompts date formatting:

  if you want to search from now up to a certain date, you can enter the date below the Date/Time box

    acceptable date formats are as follows:
        YYYY/MM/DD (the MM and DD don't have to be two digits)
        "1 week ago", "3 weeks ago", etc.
        "1 month ago", "3 months ago", etc. 
        "1 year ago", "3 years ago" etc.
    
IMPORTANT NOTES FOR DATES: 
  1. if you choose to enter any of the latter 3, you cannot mix and match, for example, you cannot do "1 year and 5 months ago", 
      you would have to do "17 months ago" you can only use 1 word out of "week, month, year"

  2. the number also must be the first character, and be proceeded with a space. "1 year"

  3. Bing dates are more limited than google dates. The following things apply to only the Bing results, the Google results will work as intended

      - Bing news does not support exact dates, therefore if the YYYY/MM/DD format is entered it will be ignored for Bing, fetching the all-time results.

      - Bing does not support multiple month/week formats, therefore if "week" or "month" is present it will be interpreted as only 1 week or 1 month.
          (if "3 weeks" is in the document, the program will interpret it as "1 week" for bing. Same situation for months).

      - Bing does not support year searches, therefore if the "year" format is used for the date, bing will search all-time results.


# EXECUTION EXAMPLE IN COMMAND LINE

An example of how the program interprets the first line is as follows: 

******** "Jensen Huang" "NVIDIA" ********
--------Searching Google..............................

----Adding to SHEET...
See the Future at GTC 2024: NVIDIA’s Jensen Huang to Unveil Latest Breakthroughs in Accelerated Computing, Generative AI and Robotics
https://nvidianews.nvidia.com/news/see-the-future-at-gtc-2024-nvidias-jensen-huang-to-unveil-latest-breakthroughs-in-accelerated-computing-generative-aiand-robotics

----Adding to SHEET...
Nvidia CEO Jensen Huang Is Powering the AI Revolution
https://www.wired.com/story/nvidia-hardware-is-eating-the-world-jensen-huang/

----Adding to SHEET...
Nvidia CEO: Smart, successful people struggle with these 2 traits—but they kept my $2 trillion company from collapsing
https://www.cnbc.com/2024/03/30/nvidia-ceo-these-soft-skills-saved-my-2-trillion-company.html

----Adding to SHEET...
Nvidia CEO Jensen Huang agrees he is demanding and a perfectionist
https://fortune.com/2024/04/30/nvidia-ceo-jensen-huang-demanding-perfectionist-say-staff/

(continues)

--------Searching Bing..............................

----Adding to SHEET...
Nvidia's Founder Went From Dishwasher to Tech Titan and Learned the Power of Storytelling to Build a Brand
https://www.inc.com/carmine-gallo/nvidias-founder-went-from-dishwasher-to-tech-titan-learned-power-of-storytelling-to-build-a-brand.html

----Adding to SHEET...
Meet Nvidia CEO Jensen Huang, the man behind the $2 trillion company powering today's artificial intelligence
https://www.msn.com/en-us/news/technology/meet-nvidia-ceo-jensen-huang-and-the-2-trillion-company-powering-todays-ai/ar-AA1nPmH5?ocid=BingNewsSearch

----Adding to SHEET...
NVIDIA CEO says its secret sauce is one part persistence, resilience, belief and a huge vision
https://www.tweaktown.com/news/98054/nvidia-ceo-says-its-secret-sauce-is-one-part-persistence-resilience-belief-and-huge-vision/index.html

(continues)

(continues for all prompts)

----Writing Person......
Done


If the Adding to SHEET is replaced with a DUPLICATE like: 

DUPLICATE
Nvidia's Founder Went From Dishwasher to Tech Titan and Learned the Power of Storytelling to Build a Brand
https://www.inc.com/carmine-gallo/nvidias-founder-went-from-dishwasher-to-tech-titan-learned-power-of-storytelling-to-build-a-brand.html

it is not added to the SHEET

if there is an error message that looks like:

An error occurred while fetching the article: Article `download()` failed with 403 Client Error: Forbidden for url: https://www.fastcompany.com/91033514/nvidia-most-innovative-companies-2024 on URL https://www.fastcompany.com/91033514/nvidia-most-innovative-companies-2024
TIMED OUT
Adding to CSV...
ARTICLE TIMED OUT WHEN FETCHING DATA
https://www.fastcompany.com/91033514/nvidia-most-innovative-companies-2024


the article is still added to the SHEET, but with the title "ARTICLE TIMED OUT WHEN FETCHING DATA"

The only time an article is not added to the SHEET is when "DUPLICATE" is present, or "Adding to SHEET" is not present


# NOTES MESSAGES

This program has various notes that can pop up for each article, indicated in the notes section of the table on the first worksheet of the Google sheet. The possible notes and 
their explanations are as follows:

Can't Double Check Prompt in Article::: This is the most common note that one might see in the program. The cause of this note can be many different reasons, but here are a few common ones.
    - There was a false positive and the article doesn't have the search term that was used to find it (This is most common with bing results). 
    - The article has a paywall/other popup on load that prevents the program from reading the text
    - The article only reveals a portion of the text and needs the user to press a button to reveal the rest, with the search term in that hidden part (Common for MSN news)
    - The article is formatted in such a way that the program cannot pull the text and do a check

Timed Out::: This error is a blanket statement for any errors that the program encountered while trying to open and fetch data from an article.
            The program found an article in it's query, but there was an error, like a denied request, or a timed out error, that prevented it from opening the article. 

MSN News Link::: The program found an article that is on MSN news, and since MSN news articles are overwhelmingly reposted articles in which their source is from another site, it should be 
                noted when they are stumbled upon because the original article still needs to be found. MSN news links often come with additional errors as they are difficult to read for the 
                program. 

Duplicate text with.....::: This note appears when the program finds a 75% or higher similarity match between the chosen article and another article that it found before. The program doesn't 
                            update the program before with this note. 

# RUNNING PROGRAM

make sure Python and chrome are installed

go to the website to create a project, key, and access api's: https://console.developers.google.com/, create a project, download Drive and Sheets APIs, 
go to credentials and create a service account, go to keys in the service account and generate a key, download the JSON, and put it into the directory with 
the article_scraper.py program.

create a Google sheet and share your Google sheet with your service account. The email of the service account should be located in the credentials section.

make sure to have both the "article_scraper.py" file and the "article_create.py" file in the same directory

go to the command line and cd into the directory and run article_create.py with the command "python article_create.py". The program will prompt for 
the name of the Google sheet that you created and should add more sheets and text into the Google Sheets and create additional text files in the directory.

o to the command line and cd into the directory and run article_scraper.py with the command "python article_scraper.py".
