import facebook    #sudo pip install facebook-sdk
import itertools
import json
import re
from urllib.parse import urlencode
from urllib.request import Request, urlopen
import requests
#the accss token of your facebook page
access_token = "EAACFHRNkwlQBAIYBX0NRjZCxFLBCF9ZA8fjExW8hbSeC5epY5mPOOdHVOsAeMSIJz6lMyvG3Sbg50vX4hZBFeOYnf1npZAj0PsZAkkGpf5JZCCQ5Pbv4FS60nstHk3pEG3ZAufF0UdE3dQnNvQ0dacF3OtnjwaMindKqHs88QdVsz1fiuaEhEDS8ZCZB41IXGGc5ubClQGmAaoQZDZD"
banning_liste=[]
app_id="146359925916244"

#the blacklist.txt containt all the comment that will be deleted
blacklist = [line.rstrip('\n') for line in open("blacklist.txt", "r")]


def add_to_blacklist(blacklist,comment):
    blacklist.append(comment)
#adding a new comment to the list
add_to_blacklist(blacklist,'bullshit')


graph = facebook.GraphAPI(access_token)
#first we will get all the post that the page did
posts = graph.get_connections("me",connection_name='posts')
Jstr = json.dumps(posts)
JDict = json.loads(Jstr)

count = 0
print(JDict['data'])
for i in JDict['data']:
    allID = i['id']
    #then we will go throught the comments to see if any comment is in our blacklist
    comments = graph.get_connections(id=allID, connection_name='comments')
    for elem in comments['data']:
        #if the comment is in the blacklist
        if elem['message'] in blacklist:
            #the comment is deleted
            print("the comment "+elem['message']+" was deleted")
            graph.delete_object(id=elem['id'])
            #the id of the user is add to our list of people that we gonna ban
            print(elem['from']['id']+" was banned")
            banning_liste.append(elem['from']['id'])
        
#banning those users
#the url used for the http post request to ban someone
url="https://graph.facebook.com/"+app_id+"/banned?access_token="+access_token+'&uid='+str(banning_liste)
response = requests.post(url)
print (response.text)
#update the blacklit
file_bl=open("blacklist.txt",'w')
for elem in blacklist:
    file_bl.write(elem+"\n")
file_bl.close()
