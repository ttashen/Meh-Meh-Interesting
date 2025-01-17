from bs4 import BeautifulSoup
import numpy as np
import pandas as pd
import requests
import json
import string
from urllib.parse import urlparse
import re
import time 

def get_all_urls():
#   Get all the deal links from deal list page
#   Since list page needs refresh to show all the deals, I accessed the network topic.js to get the full list 
    all_deal_link = []
    for i in range(1,20):
        all_deal_link.append('https://meh.com/forum/topics.json?page={0}&category=deals&sort=date-created'.format(i))
#     each element obtained double_url has the url of interest in [], and a duplicate in () right after. The url needs to be parsed from the string.
    double_url = []
    for link in all_deal_link:
        response = requests.get(link)
        raw_data = json.loads(response.text)
        for x in raw_data:
            double_url.append(x['text']['raw'])
    table = str.maketrans(dict.fromkeys("()"))
    url = []
    for s in double_url:
        if ']' in s:
            url.append(s.split(']')[1].translate(table))
        else:
            url.append(s)
    return url

def feature_scrapping(url):
    features = {}
#     to test the request is a success
    response = requests.get(url)
    soup = BeautifulSoup(response.content,'html.parser')
    print(response.status_code)
    description = soup.find(class_='features').find('ul')
    if description:
        item_features = description.text.strip()
    else:
        item_features = None
    spec_link = soup.find(class_='specs')
    if spec_link:
        spec_url = spec_link['href']
#     to test the request is a success
        spe_response = requests.get(spec_url)
        print(spe_response.status_code)
        spe_soup =BeautifulSoup(spe_response.content,'html.parser')
        item_id = spe_soup.find(class_='h-entry topic unread')['id']
        date = spe_soup.find('time')['datetime']
        condition = re.compile(r'Condition')
        specs = spe_soup.find('li', class_='comment')
        condition = specs.find(text=condition)
    else:
        item_id = None
        date = None
        condition = None
    item = soup.find(class_='features').find('h2').text
    story = soup.find(class_='story').text.strip()
    visits = int(soup.find(class_='primary').find('strong').text.strip())
    phone_visit = float(soup.find(class_='secondary').find_all('strong')[0].text.strip('%'))/100
    tablet_visit = float(soup.find(class_='secondary').find_all('strong')[1].text.strip('%'))/100
    mehs = int(soup.find(id='total-mehs').text)
    type_meh = float(soup.find(id='referrals').find(class_='primary').find('strong').text.strip('%'))/100
    referrals = soup.find_all(class_='referrer')
    ref_dict = {}
    for ref in referrals:
        link = ref.find(class_='base')['href']
        parsed_uri = urlparse(link)
        web = parsed_uri.netloc.split('.')[-2]
        ref_dict[web] = float(ref['data-percentage'])
    sale_num = int(soup.find(id='sold-quantity').text)
    sale_revenue = int(soup.find(id = 'sold-revenue').text.strip('$'))
    poll_stats = soup.find(class_='vote-count')
    if poll_stats:
        poll_num = int(soup.find(class_='vote-count').text.split()[0])
    else:
        poll_num = 0
    features['datetime']=date
    features['item_id']=item_id
    features['item_name']=item
    features['item_features']=item_features
    features['condition']=condition
    features['story']=story
    features['visits']= visits
    features['phone_visits']=phone_visit
    features['tablet_visits']=tablet_visit
    features['mehs']=mehs
    features['type_meh']=type_meh
    features['sale_num']=sale_num
    features['sale_revenue']=sale_revenue
    features['poll_num']=poll_num
    return {**features, **ref_dict}


if __name__=='__main__':
    urls = get_all_urls()[1:]
    rows = []
    unparsed = []
    for url in urls:
        print (url)
        try:
            rows.append(feature_scrapping(url))
        except:
            unparsed.append(url)
            print ('url {0} could not be parsed'.format(url))
#     sleep command here is to prevent the server being 'angry' at my scraping
        time.sleep(np.random.randint(3,10))
#     to see which url is not responding
#     for i, url in enumerate(urls):
#         print (i)
#     columns.append(feature_scrapping(url))
#     time.sleep(np.random.randint(3,10))
    data = pd.DataFrame(rows)
    data.to_csv('meh_data',sep='\t')
    with open('unparsed.txt', 'w') as f:
        for item in unparsed:
            f.write("%s\n" % item)
        
        
        
    