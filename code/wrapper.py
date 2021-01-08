from subprocess import call
import time
import datetime as dt
import json
import byText

urls = [
    ["https://www.reddit.com/r/EntitledParents/", "Entitled Parents","PLWRLqG67y-vzk3d8G9ulEPH6xrEEgUTzZ"],
    ["https://www.reddit.com/r/TalesFromTechSupport/","Tales From Tech Support","PLWRLqG67y-vyvr_YSwsO3EsgRVVxK8vDd"],
    ["https://www.reddit.com/r/TalesFromRetail/","Tales From Retail","PLWRLqG67y-vxdZ_Vg5tVs_rHArkjhyvR0"],
    ["https://www.reddit.com/r/confessions","Confessions","PLWRLqG67y-vxIO6pD9j2Ctb1Nx2j6XwKP"],
    ["https://www.reddit.com/r/MaliciousCompliance/", "Malicious Compliance","PLWRLqG67y-vykwS-4Yz2_GEJ5yBZD-ERL"]
]
def formatUrl(url,isPost=False):
    url = url.replace("https://reddit.com/","")
    url = url.replace("http://reddit.com/","")
    url = url.replace("https://www.reddit.com/","")
    url = url.replace("http://www.reddit.com/","")
    if isPost==False:
        slashes = url.count("/")
        if slashes==2:
            url = url[:url.rfind("/")] #if there is more than one slash, we remove everything second slash down
    else:
        url = url.replace("r/","",1)
        url = url.replace("/comments/","")
        index = url.find("/")
        url = url[index:] #remove subreddit name
    return url

f = open("../data/lastMade.json","r")
try:
        dict = json.loads(f.read())
        lastUrl = dict['url']
        last = dict['time']
except:
    last = 0
    lastUrl = None

f.close()
hourMax = 20
hourMin = 9
dif = (60*60*3)+(60*5) #3 hours and 5 min apart.
dict = {}
print(last,lastUrl)
while True:
    if lastUrl==None or lastUrl>=len(urls)-1:
        print("reseting lastUrl")
        lastUrl = 0
    else:
        lastUrl+=1
    while lastUrl<len(urls):
        url = urls[lastUrl]
        while 1==1:
            current = time.time()
            hour = dt.datetime.now().hour
            if current-last>=dif and hour<=hourMax and hour>=hourMin:
                print("Making a new video from "+formatUrl(url[0]))
                ret = call(['python3', 'byText.py','-u',url[0],'-t',url[1],"-p",url[2]])
                if ret==0:
                    print("Complete success!")
                    last = time.time()
                    dict['url'] = lastUrl
                    dict['time'] = last
                    f = open("../data/lastMade.json","w") #for temp storage in case any failure.
                    f.write(json.dumps(dict))
                    f.close()
                    lastUrl+=1
                else:
                    print("Error making video. Posts not marked as used, and moving on to next sub")
                    lastUrl+=1
                break
            #print("Not a good time, waiting 10 minutes than trying again...")
            time.sleep(600)
