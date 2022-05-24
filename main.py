# ######################### PARSE HTML DOC ###################################
# ----------------------------------------------------------------------------
from bs4 import BeautifulSoup
import requests as req
import time

# set url
url = 'https://view.news.email.ikea.co.uk/?qs=5548cf544922c066baceb138255b8c4b835acd2da9e8fbd9bb1e6c084ed5ad24328d66077956c3f0091d1e973e5e70e98b08666671c92a901b168bbaf80a1adc7f762aba7e540f9a1867d98397007b0e'
# requesting for the website
Web = req.get(url)
# creating a BeautifulSoup object and specifying the parser
soup = BeautifulSoup(Web.content, features="html.parser")

import numpy as np
# create empty arrays to store scraped values
link_arr = []
redirect_link = []
utm_terms = []

for link in soup.find_all('a'):
    if link.get('href'):
        link_arr.append(link.get("href"))

# delete main weblink
link_arr = np.delete(link_arr, 0)
link_arr = link_arr.tolist()
# print(link_arr)

# ######################### FIND COORDINATES #################################
# ----------------------------------------------------------------------------
# convert html to png
from selenium import webdriver
from selenium.webdriver.firefox.options import Options

# run headless version of Firefox
options = Options()
options.headless = True
browser = webdriver.Firefox(options=options,executable_path="C:/Users/putsam/Anaconda3/envs/py36/geckodriver-v0.30.0-win64/geckodriver.exe")
print('Headless Firefox Running...')

# browser.maximize_window()
browser.get(url)
# get window size
s = browser.get_window_size()
# obtain browser height and width
w = browser.execute_script('return document.body.parentNode.scrollWidth')
h = browser.execute_script('return document.body.parentNode.scrollHeight')
# set to new window size
browser.set_window_size(w, h)
# obtain screenshot of page within body tag
browser.find_element_by_tag_name('body').screenshot("out.png")
browser.set_window_size(s['width'], s['height'])

# create empty numpy array to store coordinates
data = np.zeros([2,2], dtype=int)
topleft = np.zeros([2,2], dtype=int)
bottomright = np.zeros([2,2], dtype=int)

# loop through links array
for i in link_arr:
    # find element by URL link
    element = browser.find_element_by_xpath('//a[@href="'+i+'"]') 
    # append element coordinates to data(arr)
    x = element.location['x']
    y = element.location['y']
    w = element.size['width']
    h = element.size['height']
    # center heat coordinates to middle of element
    x = int(x+(w/2))
    y = int(y+(h/2))
    data = np.append(data, [[x,y]], axis=0)
    tlx = int(x-(w/2))
    tly = int(y-(h/2))
    topleft = np.append(topleft, [[tlx,tly]], axis=0)
    brx = int(x+(w/2))
    bry = int(y+(h/2))
    bottomright= np.append(bottomright, [[brx,bry]], axis=0)
    
# delete sample data
data = np.delete(data, 0, 0)
data = np.delete(data, 0, 0)
topleft = np.delete(topleft, 0, 0)
topleft = np.delete(topleft, 0, 0)
bottomright = np.delete(bottomright, 0, 0)
bottomright = np.delete(bottomright, 0, 0)
# print(data)

####### DON'T USE SELENIUM FOR THIS TRUST ME, URLLIB WILL SUFFICE ############
# ----------------------------------------------------------------------------
import urllib.request

for i in link_arr:
    u = urllib.request.urlopen(i)
    redirect_link.append(u.url)
    # print(u.url)
    full_link = u.url
    if "utm_term=" in full_link:
        # print(full_link.split("utm_term=",1)[1])
        utm_terms.append(full_link.split("utm_term=",1)[1])
    else:
        # print("NO UTM TERM FOUND!")
        utm_terms.append(None)

# insta utm won't show, will find a better solution moving forward
insta_utm = (utm_terms.index('F_Footer_PinterestLink') + 1)
utm_terms[insta_utm] = 'F_Footer_InstagramLink'

print('Coordinates np.array Shape: ', data.shape)
print('Original Link Shape: ', len(link_arr))
print('Redirected Link Shape: ', len(redirect_link))
print('UTM Terms Shape: ', len(utm_terms))

none_indices = [i for i, e in enumerate(utm_terms) if e == None]
print ('None Indices: ', none_indices)

# delete 'None' coordinates in data
data = np.delete(data, none_indices, axis=0)
topleft = np.delete(topleft, none_indices, axis=0)
bottomright = np.delete(bottomright, none_indices, axis=0)
    
# delete 'None' in utm_terms
for elem in utm_terms:
        if elem == None:
            utm_terms.remove(elem)
            
# delete in reverse order to not throw off subsequent indices
for index in sorted(none_indices, reverse=True):
    del link_arr[index]
    del redirect_link[index]

import numpy as np 
utm_termsNP = np.array(utm_terms)

dict = {}
for term, val in zip(utm_termsNP, data):
    dict[term] = val

import pandas as pd
df = pd.read_csv("C:/Users/putsam/OneDrive - OneWorkplace/Documents/HeatMap/clicks.csv")
clicks_name = df['linkName'].tolist()

for i in clicks_name:
    if i in utm_terms:
        mult = (df.loc[df['linkName'] == i, 'NumberofClicks']).tolist()[0]
        for j in range (mult+1):
            data = np.append(data, [dict[i]], axis=0)
print(data)
print(data.shape)

# ########################## HEATMAP VISUALIZATION ##########################
# ---------------------------------------------------------------------------
import numpy as np 
import cv2

# read image
src = cv2.imread("out.png")
# get size of canvas
width, height, _ = src.shape
# blank heatmap canvas
heatmap_image = np.zeros((width,height,1), np.uint8)

itter = 0
# plot data points
for coord in data:
    x,y = coord
    cv2.circle(heatmap_image, (x-15,y), 30, (255,0,0), -1)
# set markers as heatmap
heatmap_image = cv2.distanceTransform(heatmap_image, cv2.DIST_C, 5)
# cosmetics for heatmap
heatmap_image = heatmap_image * 11
heatmap_image = np.uint8(255 * heatmap_image)
heatmap_image = cv2.applyColorMap(heatmap_image, cv2.COLORMAP_JET)
# overlay
fin_img = cv2.addWeighted(heatmap_image, 0.6, src, 0.4, 0.0)
print('Press "Q" to close window')
print('Image will be saved as "result.png" in active directory')
while True:
    # show heatmap figure
    cv2.imshow("Heat Map", fin_img)
    # set break key 'q'
    if cv2.waitKey(1) & 0xFF == ord("q"):
        # export image
        cv2.imwrite("result.png", fin_img)
        break

cv2.destroyAllWindows()

# ########################## KDE PLOT VISUALIZATION ##########################
# ----------------------------------------------------------------------------

# import the required packages
from scipy import stats, integrate
import numpy as np
import seaborn as sns
import matplotlib.pyplot as plt
import math
import matplotlib.image as mpimg 

# load the coordinates file
x = data[:, 0]
y = data[:, 1]

img = mpimg.imread('out.png')

ax = sns.kdeplot(x, y, 
                  height=160, aspect=(src.shape[1])/(src.shape[0]),
                  cmap="viridis", cbar=False, gridsize=1000,
                  xlabel='None', ylabel='None', 
                  alpha=0.7, 
                  zorder=2
                  )
ax.set(ylim=(0,src.shape[0]))
ax.set(xlim=(0,src.shape[1]))
ax.invert_yaxis()
loc = sns.scatterplot(x=x, y=y, zorder=3)
ax.imshow(img, zorder=1)

















