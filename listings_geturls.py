
import os
import pandas as pd
import listings_functions as lf

# Navigate to home page; start search for "New York"
cwd = os.getcwd()
chrome_path = cwd + "/chromedriver" 
print(chrome_path)

start_search = "New York"
driver = lf.start_initialsearch(start_search, chrome_path)

# Filter by region (uses xpath)
lf.region_search()

# Limit search by price range (uses xpath)
price_min = 50001
price_max = 1000000

lf.price_filter(price_min, price_max)

# Limit by size
size_min = 1
size_max = 50

lf.size_filter(size_min, size_max)

# Loop through each page of search results by clicking 'next' button
all_data = [] # data to write to file
is_next = True # keeps track of if there is another page of results
page_num = 1 # current page number 

while is_next == True:
    
    print("page ",str(page_num),"...")
    
    # get entire page of information   
    output = driver.page_source 
        
    # break into individual listings on the page (all info about the listing)
    listings=[]
    listings = output.split("data-pid=")[1:] # listing info contained in "data-pid"
    print("found", len(listings)," listings") # should be 16 listings per page

    # Parse html to get the URL for each listing
    page_urls = lf.get_listing_url(listings)
    all_data.append(page_urls)

    # click the 'next' button to bring up next page of results
    is_next = lf.click_next_button(driver)
    page_num += 1

# After reading all pages, put in a dataframe, then save to a .csv file
new_data = [url for group in all_data for url in group]

df = pd.DataFrame(new_data, columns=['listing number','url'])
print("Number of listings: ", df.shape[0])
df.drop_duplicates(subset='listing number', inplace=True)
print("Number of unique listings: ", df.shape[0])
df.to_csv("property_data.csv")

driver.quit() # terminate session








