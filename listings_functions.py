
from bs4 import BeautifulSoup
import pandas as pd
import random
import re as re
import requests

from selenium import webdriver
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

import time
import zipcode

def click_next_button(driver):
    try:
        next_button = driver.find_element_by_link_text("Next")
        next_button.click()
        time.sleep(2)
        
        return True
    except (TimeoutException, NoSuchElementException):
        #raise ValueError("Clicking the 'Buy' button failed")
        print("No more results!")
        
        return False

def get_description(soup):    
    text = soup.find("div", {"class": "margin marginright marginbottom"})
    
    
    if text is None:
        description = "None"
    else:
        text = text.prettify().split("<span>\n")
        if len(text) >= 2:
            text = text[1]
        elif len(text) < 2:
            text = text[0]
        else:
            text = "None"
        
        text_splits = text.split("\n")
        description = []
        for text in text_splits:
            if "<" not in text:
                description.append(text)
        
        description = "".join(description)
    
    return description

def get_title(soup):
    text = soup.find("div", {"class": "detTitle"})
    
    if text is None:
        return []
    else:
        text = text.prettify()#.split("<span>\n")
        text = text.split("h1")[1].replace('>\n',"").lstrip()
        text = text.replace('\n </',"")
    
        return text

def get_values(soup):    
    text = soup.find("div", 
                     {"class": "left darkgreen dtrighthalf"})
    
    if text is None:
        prop_type = [] 
        prop_size = [] 
        prop_price = []
        prop_id = []
        
    else:
        
        text = text.prettify().split('class="pattname"')[1:]

        name = []
        value = []
        for t in text:
            n, v = t.split('class="pattvalue"')
            n = n.split('\n')[1].lstrip(" ")#,"")
            v = v.split('\n')[1].lstrip(" ")#,"").replace(" ","")
            name.append(n)
            value.append(v)
        prop_type = value[0]
        prop_size = value[1]
        prop_price = value[2]
        prop_id = value[3]

    return prop_type, prop_size, prop_price, prop_id

def get_latlon(soup):    
    text = soup.find("div", {"id": "iframe-map"})
    if text is None:
        lat = []
        lon = []
    else:
        text = text.prettify()    
        text = text.split('q=')[1].split('&amp')[0]
        lat,lon = text.split('%2C')
    
    return lat, lon

def remove_html_tags(text):
    #"""Remove html tags from a string"""
    import re
    clean = re.compile('<.*?>')
    clean_text = re.sub(clean, '', text)
    clean_text = clean_text.replace('\n','')
    clean_text = clean_text.replace('">','')
    clean_text = clean_text.replace('<div class="','')
    clean_text = clean_text.replace("bold",'')
    clean_text = clean_text.lstrip().rstrip()
    
    return clean_text

def get_features(soup):  
    
    activities = []
    waterfront = []
    adj_owner = []
    utilities = []
    view = []
    terrain = []
    
    # First parse the feature name & values from the text
    features_all = []   
    text = soup.find("div", {"class": "left dtlefthalf margintop"})
    
    if text is None:
        pass
        
    else:
        text = text.prettify()
        text = text.split("clear bold accent margintop")[1:]
        for t in text[:-2]:
            feature = t.split("clear pattname")[0]
            if ':' in t.split("clear pattname")[1]:
                subfeature = t.split("clear pattname")[0]
                values = t.split("clear pattname")[1].split("pattvalue")[1:]#t.split("clear pattvalue")[2:]
            else:
                subfeature = 'Nan'
                values = t.split("clear pattname")[1:]

            feature = remove_html_tags(feature)
            subfeature = remove_html_tags(subfeature)
            values = [remove_html_tags(v) for v in values]
            features_all.append([feature,values])

            # Next organize into a standard format (not all listings have the same features)
            if 'activities' in feature.lower():
                activities = values
            elif 'waterfront' in feature.lower():
                waterfront = values
            elif 'owner' in feature.lower():
                adj_owner = values
            elif 'utilities' in feature.lower():
                utilities = values
            elif 'view' in feature.lower():
                view = values
            elif 'terrain' in feature.lower():
                terrain = values        
    
    return activities, waterfront, adj_owner, utilities, view, terrain


def start_initialsearch(text, chrome_path):
    
    global driver
    print("Starting initial search...")
    driver = webdriver.Chrome(chrome_path)
    driver.get("your url here")

    search = driver.find_element_by_id("hero_qv")
    search.send_keys(text)
    search.send_keys(Keys.RETURN) # hit return after you enter search text
    time.sleep(3) # sleep for few seconds so you can see the results

    return driver

def region_search():

    print("Filtering by region...")
    region_xpath = '/html/body/div[1]/div[4]/div[1]/div[2]/span[8]/a'
    button = driver.find_element_by_xpath(region_xpath).click()
    time.sleep(2) # sleep for few seconds 

def price_filter(pmin, pmax):

    print("Filtering by price...")
    priceMin = driver.find_element_by_id("pmin")
    priceMin.send_keys(str(pmin))
    priceMax = driver.find_element_by_id("pmax")
    priceMax.send_keys(str(pmax))

    button_xpath = '/html/body/div[1]/div[4]/div[1]/div[2]/div[10]/div[2]/input[4]' # price 'go' button
    button = driver.find_element_by_xpath(button_xpath).click()
    time.sleep(3) # sleep for few seconds 

def size_filter(smin, smax):

    print("Filtering by acreage...")
    sizeMin = driver.find_element_by_id("smin")
    sizeMin.send_keys(str(smin))
    sizeMax = driver.find_element_by_id("smax")
    sizeMax.send_keys(str(smax))

    button2_xpath = '/html/body/div[1]/div[4]/div[1]/div[2]/div[15]/div[2]/input[4]' # parcel size 'go' button
    button = driver.find_element_by_xpath(button2_xpath).click()
    time.sleep(3) # sleep for few seconds 


def get_listing_url(listings):

    # parse individual listing numbers; create URL for each listing from the listing number
    listing_url = []
    wdata = []
    
    for l in listings:
        listing_num = l.split("alt=")[0].split('"')[1]
        url = 'your url here'
        listing_url.append(url)

        print(url)

        wdata.append([listing_num, url])    #,prop_description])

    return wdata













