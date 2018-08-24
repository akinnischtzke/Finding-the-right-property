

''' 

Uses BeautifulSoup to get information from individual web pages. Parse out information of interest and save in csv file:
        - Title
        - Property type (e.g. "Land")
        - Parcel size
        - Other ID
        - Price
        - Property features (activities, view, waterfront, terrain, etc)
        - Location (lat/lon)
        - Text description

'''

import pandas as pd
import listings_functions as lf
import random
import numpy as np
import time
import requests
from bs4 import BeautifulSoup

wdata = []
df_new = pd.DataFrame()
i=0

a, m = 2.75, 1.  # shape and mode
tpause = (np.random.pareto(a, 10000) + 1) * m # generate a long-tailed distribution for timing interval
tpause += 10
tpause[tpause > 45] = 45

with open('landwatch_data.csv', 'rb') as csvfile:
    
    listings = pd.read_csv(csvfile)
    
    for url in listings.loc[72:,'url']:

        #print(url)
        i += 1
        print(i)
        print("waiting {:.2f} seconds".format(tpause[i]))
        time.sleep(tpause[i])

        response = requests.get(url)
        soup = BeautifulSoup(response.content, "html.parser")
     
        # Get title
        prop_title = lf.get_title(soup)
        
        # Get property information
        prop_type, prop_size, prop_price, prop_id = lf.get_values(soup)
        
        # Get geo-coordinates 
        lat, lon = lf.get_latlon(soup)
        
        # Get features 
        activities, waterfront, adj_owner, utilities, view, terrain = lf.get_features(soup)

        # Get text of property description (will still need to be cleaned up somewhat)
        prop_description = lf.get_description(soup)

        wdata.append([prop_title, prop_type, prop_size, prop_price, prop_id, 
                      activities, waterfront, adj_owner, utilities, view, 
                      terrain,lat, lon, prop_description])

df_new = pd.DataFrame(wdata,columns = ['Title','Property type', 'Parcel Size', 'Price', 
                                       'MLS or other ID','Activities','Waterfront',
                                       'Adjacent Owner','Utilities','View','Terrain',
                                       'Latitude','Longitude','Description'])

df = pd.concat([listings, df_new], axis=1)
df.to_csv("landwatch_propertydata.csv")

