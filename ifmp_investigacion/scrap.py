"""This is the example module.

This module does stuff.
Created on Sun Aug  1 10:43:34 2021
"""

__version__ = '0.5'
__author__ = 'Juan Ignacio Rodríguez Vinçon'

################################### IMPORTS ###################################
import unicodedata
import time
import random
import re

import requests
from requests.exceptions import HTTPError
from bs4 import BeautifulSoup

################################ SUB-ROUTINES #################################
def generator():
    while True:
        yield


def make_request(url, sleep = None, data = None):
    '''
    some function description to input later.

    input variables
    output results
    example
    '''

    # Header to send to website:
    header = {
        'user-agent':
            r'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:90.0)'
            r' Gecko/20100101 Firefox/90.0'
            }
    # Timeout in case there's no response from website
    time_out = 10

    # If a request was done to the same site before, sleep first
    if sleep != None:
        time.sleep(sleep)

    # Try to make request to website
    try:
        # Start clock to time response
        start = time.time()
        if data != None:
            r = requests.post(url, data = data, headers = header,
                              timeout = time_out)
        else:
            r = requests.get(url, headers = header, timeout = time_out)
        # Delay next request by random rate between 1 and 2 times longer
        # than (10s + time it took to load page).
        # 10s was chosen because CSIC website asks for it in their robots.txt
        delay = 10 + (time.time() - start)
        sleep_time = random.uniform(1, 2) * delay
        # If response was successful, no exception will be raised
        # Uncomment next line in case of wanting to know the status code
        #print(f"Success! Response is {r.status_code}")


        return r, sleep_time

    except HTTPError as http_err:
        print(f"HTTP error occurred: {http_err}")
    except Exception as err:
        print(f"Other error occurred: {err}")


def extract_text(html_content, add_new_line = False):
    '''
    some function description to input later.

    input variables
    output results
    example
    '''

    if add_new_line:
        text = ''
        for ele in html_content:
            text += ele.text + '\n' #### evitar \n en último elemento usando range(len())? o while? y ahorra un loop
    else:
        text = html_content.text
    text = 'n/a' if (text.isspace()) or (text == None) else text.strip()
    if text != 'n/a':
        text = text.lower()
        text = (
            unicodedata
            .normalize('NFKD', text)
            .encode('ascii', 'ignore')
            .decode('utf8')
            )

    return text


def extract_href(html_content):
    '''
    some function description to input later.

    input variables
    output results
    example
    '''

    href = html_content.get('href')
    href = 'n/a' if (href.isspace()) or (href == None) else href.strip()
    href = href + '/' if (href != 'n/a') and (href[-1] != '/') else href

    return href


def clean(string, output_ls = False, keyword = None):  #Incluirla en extract?
    '''
    some function description to input later.

    input variables
    output results
    example
    '''

    if output_ls: ### Sirve solo para CSIC y EI, ANII solo tiene un responsable, SNI no tiene responsable (estos se limpian en DF)
        if (keyword == 'responsables') or (keyword == 'responsables:'): ### si checkeo aca las palabras, no es necesario en linear_search()
            to_replace = (
                r'prof\.|dra\.|adj\.|adj,|agdo\.|agda\.|tit\.|as\.|dr\.|lic\.'
                r'|br\.|mg\.|\(\w*\)|\(designada.*|responsables:'
                r'|comision curricular:|comision de seguimiento|coordinadora.*'
                r'|\.\sinstituto.*|\.\sdepartamento.*|:.*|\sfac\..*|\sinco,.*'
                r'|\sdepbio.*|\scenur.*|(?<!\()\sfacultad.*'
                )
        elif keyword == 'servicios involucrados':
            to_replace = r'\(\w*\)|:.*'
        text = re.sub(to_replace, '', string)
        text = re.sub('\(.*\)|-.*', '', text)
        ls = re.split('\n+|/|,|\.|;', text)
        # Cleans list of empty string values by using "if x" (in order to
        # evaluate TRUE it must not be empty)
        ls[:] = [x.strip() for x in ls if x.strip()]

        return ls

    else:
        text = string.replace('\n', ' ').replace('\r', '')  # parece no funcionar aca, pero en extract funcionaba.

        return text


def linear_search(html_content, keyword, in_content = False, inverse = False):
    '''
    some function description to input later.

    input variables
    output results
    example
    '''

    # List of missing values to compare with the results of the search.
    missing_values = [
        '.',
        'pagina en construccion.',
        'no corresponde'
        ]
    # List of keywords to compare for the clean function.
    clean_keywords = [
        'responsables',
        'responsables:',
        'servicios involucrados'
        ]
    # Iterate through each element in html_content and extract its text.
    for i in range(len(html_content)):
        text = extract_text(html_content[i])

        # If the keyword and the result are in the same level content,
        # split it accordingly and then check for a match.
        if in_content:
            text = clean(text)
            attr, value = (
                # Split on the first space counting from the end of the string,
                re.split('\s(?=\S+$)', text) 
                if inverse
                # else split on the first space.
                else text.split(maxsplit = 1)
                )
            if (attr == keyword) and (value not in missing_values):
                return attr, value
            elif (attr == keyword) and (value in missing_values):
                return attr, 'n/a'

        # Else just check for a match and if found apply extract_text on child.
        elif text == keyword:
            child = (
                extract_text(html_content[i+1], True)
                if keyword == 'responsables:'
                else extract_text(html_content[i+1])
                )
            if child not in missing_values:
                child = (
                    clean(child, True, keyword) 
                    if keyword in clean_keywords
                    else clean(child)
                    )
                return text, child
            else:
                return text, 'n/a'

    # If no match was found:
    return keyword, 'n/a'


def table_scrapper(rows, cell_tag, dataset,
                   keys, href = None, base_url = None):
    '''
    some function description to input later.

    input variables
    output results
    example
    '''

    # Copy the dataset to modify.
    dic = dataset
    # Iterate through each row.
    for row in rows:
        # Iterate through each cell to extract the relevant data.
        j = 0
        missing_values_counter = 0
        for i in range(len(row.select(cell_tag))):
            cell = row.select(cell_tag)[i]
            text = extract_text(cell)

            # Check that cell is not empty.
            if (text != 'n/a') and (j < len(keys)):
                dic[keys[j]].append(text)
                j += 1
            # If missing value add one to counter.
            else:
                #print(missing_values_counter)
                missing_values_counter += 1
            # If there is more than 1 missing value, break loop.

            if missing_values_counter > 1:
                break

        # Checks if there is an URL to extract and perform extraction
        # (as long as the row wasn't skipped because of missing values).
        if (href != None) and (missing_values_counter < 2):
            for k, v in href.items():
                url = row.select('a')[v]
                url = extract_href(url)
                url = (
                    base_url + url
                    if (base_url != None) and (url != 'n/a') 
                    else url
                    )
                dic[k].append(url)


    return dic