# -*-coding: utf-8 -*-
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from subprocess import call
import re
import subprocess
from PIL import Image
from PIL import ImageFont
import os,shutil
import sys
import math
import time
import json
import flock
from image_utils import ImageText
current_image = 0
testurl = "https://www.reddit.com/r/entitledparents/comments/dh5fn6/em_tries_to_get_me_and_my_coworkers_fired_after/"
prevLength = 0
word_per_minute = 175

fileLock_file = '../data/lock'

base_keywords = ['reddit','r/entitledParents','reddit reader','text to speech','fun','r/ChoosingBeggars','r/MaliciousCompliance','r/','TheRedditExperiment','Storytime','upvote']

# settings
color = (255, 255, 255)
background = (45,45,45)
bg_img = "../static/img/bg.png"
SIZE = Image.open(bg_img).size
#IMGWIDTH=SIZE[0]
border=100
#IMGHEIGHT = SIZE[1]
del SIZE
IMGWIDTH = 1920
IMGHEIGHT = 1080
bg_img = (IMGWIDTH,IMGHEIGHT)
font = '../static/fonts/Raleway-Light.ttf'
font_size = 40
overlay = (0,0,0,120)
bitrate = 5000
#Tut: https://gist.github.com/turicas/1455973
newLine = 2*ImageFont.truetype(font, font_size).getsize("g")[1]

def setImgGlobals(imgpath):
    global bg_img
    bg_img = imgpath
    SIZE = Image.open(bg_img).size
    global IMGWIDTH
    IMGWIDTH = SIZE[0]
    global IMGHEIGHT
    IMGHEIGHT = SIZE[1]

def pullText(URL): #returns list of tuples in form (string, type)

    options = webdriver.ChromeOptions()
    options.headless = True
    driver = webdriver.Chrome(options=options)
    driver.get(URL)

    S = lambda X: driver.execute_script('return document.body.parentNode.scroll'+X)
    driver.set_window_size(S('Width'),S('Height')) # May need manual adjustment
    try:
        el = driver.find_element_by_xpath('//*[@data-click-id="text"]/div')
        user = driver.find_element_by_css_selector('._2mHuuvyV9doV3zwbZPtIPG')
        user = user.text
        title = driver.find_element_by_css_selector('._eYtD2XCVieq6emjKBH3m')
        title = title.text
    except Exception as e:
        print(str(e))
        driver.quit()
        print("Couldnt find text element, skipping post.")
        return -1
    hasImg = hasImage(el)
    if len(el.text)<15:
        driver.quit()
        print("Too short of post")
        return -1
    if re.match("http",el.text)!=None:
        driver.quit()
        print("Started with link, skipping")
        return -1
    if hasImg==True:
        print("Has image, skipping post")
        driver.quit()
        return -1
    children = el.find_elements_by_xpath('./*')
    textList = [(user,"USER"),(title,"TITLE")]

    print("Getting text from: {}...".format(formatUrl(URL,isPost=True)),end="")
    for i in children:
        if len(i.text)>0:
            if i.tag_name=="ul":
                items = i.find_elements_by_xpath('./li')
                for item in items:
                    links = getLinks(i)
                    for link in links:
                        item.text.replace(link,"<Link>")
                    typeList = []
                    strings = re.findall('[^?.!;]+[?.!;]*[ "]*',item.text)
                    if len(strings)==0:
                        strings = [item.text]
                    strings[0] = u"\u2022" +strings[0]
                    for l in range(len(strings)):
                        typeList.append("lip")
                    textList+=list(zip(strings,typeList))
                strings = []
                typeList = []
                strings.append(0)
                typeList.append("BREAK")
                #print("end list")
                textList+=list(zip(strings,typeList))
            else:
                links = getLinks(i)
                for link in links:
                    i.text.replace(link,"<Link>")
                strings = re.findall('[^?.!;]+[?.!;]*[ "]*',i.text)
                #^^finds any amount of characters followed by any amount of punctuation
                #print(strings)
                if len(strings)==0:
                    strings = [i.text]
                typeList = []
                for l in range(len(strings)):
                    typeList.append(i.tag_name)

                strings.append(0)
                typeList.append("BREAK")
                textList+=list(zip(strings,typeList))
    driver.quit()
    print("Done")
    #print(textList)
    #textList = textList+[("","START_KID")]+textList+[("","END_KID")]+textList
    return (textList,user)

def getLinks(el):
    ret = []
    try:
        links = re.findall('https{0,1}[^ ]*',el.text)
    except:
        return ret
    for link in links:
        isSubreddit = re.findall("r/[\S]*?[\s]",link)
        if len(isSubreddit)==0:
            ret.append(link)
    return ret


def checkSticky(element):
    try:
        element.find_element_by_class_name("icon-sticky")
        return True
    except:
        return False

def hasImage(element):
    try:
        element.find_element_by_xpath('.//img')
        return True
    except:
        return False


def outImgAndSound(textList,user,number,imageNumber=0):
    global words_per_minute
    global border
    heightInfo = getHeights(textList)
    #path_img_temp = './images/scrape{}.png'.format(number)
    if heightInfo[0]==0:
        img = ImageText(bg_img, background=background,overlay=overlay,border=border,overlay_height=heightInfo[1])
        height = (IMGHEIGHT-heightInfo[1])/2+(newLine/2)
    else:
        img = ImageText(bg_img, background=background,overlay=overlay,border=border,overlay_height=IMGHEIGHT-border-border)
        height = border+(newLine/2) #since height seems to be relative to bottom of text

    overall = ""
    last_width = border
    firstBreak = True
    textNumber = 0
    videoFiles = []
    existed = False
    new_post = True
    if os.path.exists("../../tmp/videos/{}.txt".format(number)):
        existed = True
    f = open("../../tmp/videos/{}.txt".format(number),"a+")
    if existed:
        videoFiles.append("\n") #add newline for new first entry
    for index,entry in enumerate(textList):
        if new_post==True:
            pass
            # tmpTextList = textList[index:]
            # ret = getHeights(tmpTextList,True,height)
            # #img.stamp_arrows(border,IMGHEIGHT-((ret[1]-height)/2))
            # new_post = False
        if entry[1]=="START_KID":
            new_post = True
            height+=newLine
            border+=200
            last_width = border
            continue
        if entry[1]=="END_KID":
            border-=200
            last_width = border
            height+=newLine
            continue

        if entry[0]=="\n":
            continue
        if entry[1]=='BREAK':
            #print("Newline cuz break")
            height+=newLine
            last_width = border
            firstBreak = True
            continue
        if height+getEntryHeight(entry,last_width)>IMGHEIGHT-border:
            textNumber=0
            imageNumber +=1
            if heightInfo[0]==imageNumber:
                img = ImageText(bg_img, background=background,overlay=overlay,border=border,overlay_height=heightInfo[1])
                height = (IMGHEIGHT-heightInfo[1])/2+(newLine/2)
            else:
                img = ImageText(bg_img, background=background,overlay=overlay,border=border,overlay_height=IMGHEIGHT-border-border)
                height = border+(newLine/2)
            last_width = border
        if entry[1]=="lip":
            if firstBreak==False:
                #print("Newline cuz list")
                height+=newLine
            last_width = border+15
            overall+=entry[0]
            firstBreak=False
        else:
            overall+=entry[0]
        #print(last_width, " for ", entry[0])
        if entry[1]=="TITLE":
            endCoord = img.write_text_box((border, height,border), entry[0], box_width=IMGWIDTH-(border*2), font_filename=font,
                       font_size=font_size+15, color=color)
            height = endCoord[1]+newLine
            last_width = border
        elif entry[1]=="USER":
            endCoord = img.write_text_box((border, height,border), entry[0], box_width=IMGWIDTH-(border*2), font_filename=font,
                       font_size=font_size-15, color=color)
            height = endCoord[1]+newLine/2
            last_width = border
            continue
        else:
            endCoord = img.write_text_box((border, height,last_width), entry[0], box_width=IMGWIDTH-(border*2), font_filename=font,
                       font_size=font_size, color=color)
            height = endCoord[1]
            last_width = endCoord[0]
        #print(last_width)
        if last_width>=IMGWIDTH-(border*2) or last_width<border:
            last_width = border
            height+=newLine
        path_img = "../../tmp/images/scrape_{}_{}_{}.png".format(number,imageNumber,textNumber)

        #voice setup
        path_voice = "../../tmp/sounds/sound_{}_{}_{}.mp4".format(number,imageNumber,textNumber)
        passIn = convertForVoice(entry[0])
        img.save(path_img)
        call(['say','-v','Daniel','-r',"{}".format(word_per_minute),'-o',path_voice,passIn])

        #combine to video
        path_video ='../../tmp/videos/video{}_{}_{}.mp4'.format(number,imageNumber,textNumber)
        makeVideo(path_img,path_voice,path_video)
        videoFiles.append("file ")
        videoFiles.append('video{}_{}_{}.mp4'.format(number,imageNumber,textNumber))
        videoFiles.append("\n")
        textNumber+=1


    del videoFiles[-1] #remove final \n
    f.writelines(videoFiles)
    f.close()
    return imageNumber


def getEntryHeight(entry,lastWidth,font_size_multipler=1):
    height = 0
    font_var = 0
    dummyImg = ImageText((IMGWIDTH,IMGHEIGHT), background=background)
    if(entry[1]=="lip"):
        height+=newLine
    elif(entry[1]=="TITLE"):
        font_var=15
        height+=newLine
    elif(entry[1]=="USER"):
        font_var=-15
        height+=newLine
    height+=dummyImg.write_text_box((0,0,lastWidth), entry[0], box_width=IMGWIDTH-(border*2), font_filename=font,
               font_size=font_size_multipler*font_size+font_var, color=color)[1]
    return height



def convertForVoice(string):
        string = string.replace(u"\u2022","")
        string = string.replace('"','')
        string = string.replace("“",'')
        string = string.replace("”",'')

        string = string.replace(":)",'') #happy face
        string = string.replace(";)",'') #winking happy face

        string = string.replace(":')'",'') #crying happy
        string = string.replace(";')'",'') #winking crying happy

        string = string.replace(":('",'') #sad face
        string = string.replace(";('",'') #winking sad face

        string = string.replace(":'('",'') #crying sad face
        string = string.replace(";'('",'') #winking crying sad face

        string = string.replace("/", " slash ")
        string = string.replace("\\", " slash ")

        #weird word cases:
        string = re.sub("No\.+","No,",string) #fix tts saying 'Number' for 'No.'
        string = re.sub("[rR]eading","reeding",string) #bot pronounces "reading" as "red-ing" for some reason..
        return string

def get_WPM():
    global words_per_minute
    return word_per_minute

def makeFullPostVideo(number,name):
        f = open("../../out/{}.txt".format(name),"a+")
        values1 = ["ffmpeg","-loglevel","error","-f", "concat", "-safe", "0","-i", "../../tmp/videos/{}.txt".format(number)]
        values2 = ["-c", "copy", "../../tmp/fullPosts/{}.mp4".format(number)]
        values = values1+values2
        f.write("file ")
        f.write('../tmp/fullPosts/{}.mp4'.format(number))
        f.write("\n")
        #static at the end of videos
        f.write("file ")
        f.write('../tmp/static.mp4')
        f.write("\n")
        f.close()
        call(values)
        return name

def makeFullVideo(name):
        f = open("../../out/{}.txt".format(name),"r")
        lines = f.readlines()
        del lines[-1]
        f.close()
        f = open("../../out/{}.txt".format(name),"w")
        f.writelines(lines)
        f.close()

        values1 = ["ffmpeg","-loglevel","error", "-f","concat", "-safe", "0","-i", "../../out/{}.txt".format(name)]
        values2 = ["-c", "copy", "../../out/{}.mp4".format(name)]
        values = values1+values2
        call(values)

def formatName(name):
            i =0
            newName = name
            while os.path.exists('../../out/{}'.format(newName)+'.txt'):
                newName = name+str(i)
                i+=1
            return newName


def makeStatic(text):
    global words_per_minute
    file="static"
    new = ImageFont.truetype(font, 3*font_size).getsize("g")[1]
    #first, get the height that would make this vertically centered
    height = getEntryHeight((text,"p"),0,3)
    overlay_height = (IMGHEIGHT-height)/2
    height = (IMGHEIGHT-height)/2-new/2
    #actually make the post
    img = ImageText(bg_img, background=background,overlay=overlay,border=border,overlay_height=overlay_height)
    img.write_text_box((border, height), text, box_width=IMGWIDTH-(border*2), font_filename=font,
               font_size=3*font_size, color=color,place="center")

    path_img = "../../tmp/images/{}.png".format(file)
    img.save(path_img)
    path_voice= "../../tmp/sounds/{}.mp4".format(file)

    call(['say','-v','Daniel','-r',"{}".format(word_per_minute),'-o',path_voice,"Thank you, next!"])
    makeVideo(path_img,path_voice,"../../tmp/{}.mp4".format(file))

def makeVideo(path_img,path_voice,path_video):
    audioCmdString = 'ffprobe -show_entries format=duration -v error -of default=noprint_wrappers=1:nokey=1 {}'.format(path_voice)
    audioCmdArgs = audioCmdString.split(" ")
    audio_length = 0
    try:
        audio_length = subprocess.check_output(audioCmdArgs)
        audio_length = str(audio_length)
        audio_length = re.search("\d+\.\d*",audio_length).group(0)
    except:
        audio_length=False
    if audio_length==False or float(audio_length)==0:
        videoCmdString = "ffmpeg -loglevel error -loop 1 -y -i {} -i {} -shortest {}".format(path_img,path_voice,path_video)
    else:
        videoCmdString = "ffmpeg -loglevel error -loop 1 -y -i {} -i {} -to {} -shortest {}".format(path_img,path_voice,audio_length,path_video)
    videoCmdArgs = videoCmdString.split(" ")
    call(videoCmdArgs)

def makeTitle(text,voiceText,name):
    global words_per_minute
    file="title"
    new = ImageFont.truetype(font, 3*font_size).getsize("g")[1]
    #first, get the height that would make this vertically centered
    height = getEntryHeight((text,"p"),0,3)
    overlay_height = (IMGHEIGHT-height)/2
    height = (IMGHEIGHT-height)/2-new/2

    #actually make the post
    img = ImageText(bg_img, background=background,overlay=overlay,border=border,overlay_height=overlay_height)
    img.write_text_box((border, height), text, box_width=IMGWIDTH-(border*2), font_filename=font,
               font_size=3*font_size, color=color,place="center")

    path_img = "../../tmp/images/{}.png".format(file)
    path_voice= "../../tmp/sounds/{}.mp4".format(file)
    img.save(path_img)
    text = convertForVoice(voiceText)
    call(['say','-v','Daniel','-r',"{}".format(word_per_minute),'-o',path_voice,text])
    makeVideo(path_img,path_voice,"../../tmp/{}.mp4".format(file))
    f = open("../../out/{}.txt".format(name),"a+")
    f.write("file ../tmp/title.mp4\n")
    f.close()

def makeThumbnail(imgFile,episodeNum):
    #note: thumbnails should conform to same height/width size as video
    try:
        imgFile = imgFile.replace(" ","")
        path_img = "../static/thumbs/{}.jpg".format(imgFile)
        img = ImageText(path_img)
        size = img.size
        new = ImageFont.truetype(font, 5*font_size).getsize("g")[1] #newline size
        text = "Ep. #{}".format(episodeNum)
        tw = ImageFont.truetype(font, 5*font_size).getsize(text)[0]#text width
        th = new #text height
        over = Image.new("RGBA", (tw,th), color=(0,0,0,200)) #create overlay of correct size

        w = int((size[0]-tw)/2) #horizontally centered width
        h = int((size[1]-th)/2) #vertically centered height
        img.image.paste(over,(w,h), over) #add full size overlay
        img.write_text_box((0,h),text,box_width=size[0]-50,font_filename=font,
                font_size=5*font_size,color = (255,51,0),place="center")
        img.save("../../tmp/images/thumbnail.jpg")

    except Exception as e:
        print(e)
        pass

def replaceSubName(text,subName):
    print(subName)
    text = re.sub('r slash.*? ',subName,text)
    print(text)
    return text

def checkargs():
    args = sys.argv[1:]
    ret = {"err":"NONE"}
    count = 0
    if "-h" in args:
        ret['-h'] = "Y"
        return ret #nothing besides help prints

    if "-p" in args: #playlist id
        index = args.index("-p")+1
        if index<len(args):
            ret["-p"]= args[index]
            count+=2
        else:
            ret["err"] = "NOP"
    if "-d" in args: #debug arg, doesnt actually make a video
            ret['-d'] = "Y"
            count+=1
    if "-q" in args:
        index = args.index("-q")+1
        if index<len(args):
            ret["-q"] = int(args[index])
            count+=2
        else:
            ret["err"] = "NOQ"
            return ret
    if "-t" in args:
        index = args.index("-t")+1
        if index<len(args):
            ret["-t"] = args[index]
            count+=2
        else:
            ret["err"] = "NOTITLE"
            return ret

    if "-u" in args:
        index = args.index("-u")+1
        if index<len(args):
            ret["-u"] = args[index]
            count+=2
        else:
            ret["err"] = "NOURL"
            return ret
    else:
        ret["err"] = "NOUFLAG"
        return ret
    if(count!=len(args)):
        ret["err"] = "INV"
    return ret

def usage():
    print("usage: [-h -d -q amount -t title] -u url")

def printHelp():
    usage()
    print("\n-h : Prints this help message")
    print("-d : Debug mode (skips uploading the video)")
    print("-q : How many threads to pull. ")
    print("-t : Title of reddit sub for reading (seperate sub name)")
    print("-u : URL of thread to traverse (Required)\n")

def clearFolders():
    shutil.rmtree("../../tmp/images")
    os.mkdir("../../tmp/images")
    shutil.rmtree("../../tmp/sounds")
    os.mkdir("../../tmp/sounds")
    shutil.rmtree("../../tmp/videos")
    os.mkdir("../../tmp/videos")
    shutil.rmtree("../../tmp/fullPosts")
    os.mkdir("../../tmp/fullPosts")

def removeFile(name):
    try:
        os.remove(name)
    except OSError:
        pass



errMessages = {
    "NONAME": "Error: -n used but no name specified",
    "INV":"Error: Invalid argument(s)",
    "NOUFLAG":"Error: -u Flag not used.",
    "NOURL":"Error: -u used but no url specified",
    "NOQ":"Error: -q used but no amount specified",
    "NOTITLE":"Error: -t used but no title specified",
    "NOIMG":"Error: -i used but no image path specified",
    "NOP":"Error: -p used but no playlist id specified"
}

def lock():
    fileLock_file = FileLock("../data/lock.lock")


def getHeights(textList,justThis=False,start_height=0): #returns number of images and height of last image
    global font_size
    global border
    img = ImageText(bg_img, background=background,overlay=overlay,border=border,overlay_height=IMGHEIGHT-border-border)
    height = border+(newLine/2) #since height seems to be relative to bottom of text
    if start_height!=0 and start_height>height:
        height=start_height
    overall = ""
    last_width = border
    firstBreak = True
    imageNumber = 0
    for entry in textList:
        if justThis==True and entry[1]=="START_KID":
            return (imageNumber,height-border)
        if entry[1]=="START_KID":
            new_post = True
            height+=newLine
            border+=200
            last_width = border
            continue
        if entry[1]=="END_KID":
            border-=200
            last_width = border
            height+=newLine
            continue

        if entry[0]=="\n":
            continue
        if entry[1]=='BREAK':
            #print("Newline cuz break")
            height+=newLine
            last_width = border
            firstBreak = True
            continue
        if height+getEntryHeight(entry,last_width)>IMGHEIGHT-border:
            if justThis==True:
                return (imageNumber,height-border)
            imageNumber +=1
            img = ImageText(bg_img, background=background,overlay=overlay,border=border,overlay_height=IMGHEIGHT-border-border)
            height = border+(newLine/2)
            last_width = border
        if entry[1]=="lip":
            if firstBreak==False:
                #print("Newline cuz list")
                height+=newLine
            last_width = border+15
            overall+=entry[0]
            firstBreak=False
        else:
            overall+=entry[0]

        if entry[1]=="TITLE":
            endCoord = img.write_text_box((border, height,border), entry[0], box_width=IMGWIDTH-(border*2), font_filename=font,
                       font_size=font_size+5, color=color)
            height = endCoord[1]+newLine
            last_width = border
        elif entry[1]=="USER":
            endCoord = img.write_text_box((border, height,border), entry[0], box_width=IMGWIDTH-(border*2), font_filename=font,
                       font_size=font_size-15, color=color)
            height = endCoord[1]+newLine
            last_width = border
        else:
            endCoord = img.write_text_box((border, height,last_width), entry[0], box_width=IMGWIDTH-(border*2), font_filename=font,
                       font_size=font_size, color=color)
            height = endCoord[1]
            last_width = endCoord[0]
        #print(last_width)
        if last_width>=IMGWIDTH-(border*2) or last_width<border:
            last_width = border
            height+=newLine
    return (imageNumber,height-border)

def getPreviouslyRead():
    f = open("../data/read.json","r")
    try:
        dict = json.loads(f.read())
    except:
        f.close()
        f = open("../data/readtemp.json","r")
        dict = json.loads(f.read())
    f.close()
    return dict

def writePreviouslyRead(dict):
    f = open("../data/readtemp.json","w") #for temp storage in case any failure.
    f.write(json.dumps(dict))
    f.close()
    f = open("../data/read.json","w")
    f.write(json.dumps(dict))
    f.close()

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

def upload_video(vid_file,vid_title,vid_des,playlist=None,keywords=[]):
    global base_keywords
    keys = base_keywords+keywords
    keys = ','.join(keys)
    if playlist==None:
        ret = call(['python3','../upload/upload_video.py',"--file={}".format(vid_file),"--title={}".format(vid_title), "--description={}".format(vid_des), "--keywords={}".format(keys)])
    else:
        ret = call(['python3','../upload/upload_video.py',"-p={}".format(playlist),"--file={}".format(vid_file),"--title={}".format(vid_title), "--description={}".format(vid_des), "--keywords={}".format(keys)])
    return ret

if __name__ == '__main__':
    options = checkargs()
    quantity = 7 #default
    err = options["err"]
    attempt = 0

    readDict = getPreviouslyRead()

    if err!="NONE": #checks for errors
        print(errMessages[err])
        usage()
        sys.exit(-1)

    name = "output"

    if "-h" in options: #case help
        printHelp()
        sys.exit(-1)

    newName = formatName(name) #gets appropriate name to prevent overwrite
    if newName!=name:
        name = newName
        print("Outputting final product to {}.mp4".format(name))


    if "-q" in options: #amount of posts passed in
        quantity = options["-q"]

    subName = None
    if "-t" in options:
        subName = options["-t"]
    debug = False
    if '-d' in options:
        debug = True
    playlist = "None"
    if '-p' in options:
        playlist = options["-p"]
    url = options["-u"] #must be here, would have exited before if not

    options = webdriver.ChromeOptions()
    options.headless = True
    driver = webdriver.Chrome(options=options)
    driver.get(url)
    oldPosts = set([])
    numberDone = 0
    done=False
    listOfPosts = []
    if quantity==0:
        driver.quit()
        sys.exit(-1)
    urlKey = formatUrl(url) #not a post
    if subName==None:
        subName=urlKey
    urlDict = dict()
    if urlKey in readDict:
        urlDict = readDict[urlKey]
    if 'episodeNumber' in urlDict:
        episodeNum = urlDict['episodeNumber']
    else:
        episodeNum = 1
    vid_title = "Best of {} Episode~{}".format(urlKey,episodeNum)
    voice_text = "Best of r/{} Episode {}. . .  . Subscribe for Redit Videos Daily".format(subName,episodeNum)
    usedLinks = []
    while done==False:
        posts = driver.find_elements_by_css_selector('.Post')
        if len(posts)==0:
            # postList = driver.find_elements_by_css_selector('.SQnoC3ObvgnGjWt90zD9Z._2INHSNB8V5eaWp4P0rY_mE')
            print("Error: No elements found on page. Are you sure this is a subreddit?")
            driver.quit()
            sys.exit(-1)

        posts = set(posts)-oldPosts
        posts = list(posts)
        for post in posts:
            isSticky = checkSticky(post)
            if isSticky==True:
                print("Post is sticked, skipping")
                continue
            try:
                a = post.find_element_by_css_selector('.SQnoC3ObvgnGjWt90zD9Z._2INHSNB8V5eaWp4P0rY_mE')
            except:
                print("Couldnt find <a> element")
                continue
            link = a.get_attribute("href")
            linkRef = formatUrl(link,isPost=True)
            if linkRef in urlDict:
                print("Already did this post")
                continue
            ret = pullText(link)
            if(ret==-1):
                urlDict[linkRef]="ERR"
                continue
            urlDict[linkRef] = "GOOD"
            listOfPosts.append(ret)
            usedLinks.append(link);
            numberDone+=1
            if numberDone==quantity: #consider making this a passable parameter
                done=True
                break
        if numberDone==quantity:
            break
        if len(posts)!=0:
            lastEl = posts[-1]
        try:
            attempt+=1
            if attempt>30:
                sys.exit(-1)
            driver.execute_script("arguments[0].scrollIntoView();",lastEl)
            print("Searching for more posts...")
            time.sleep(5) #give extra time to load new elements
            oldPosts = set(posts)
        except:
            print("Couldnt scroll last element, exit failure")
            sys.exit(-1)
            break
    print("Pulled all text. Making video now...")
    driver.quit()

    print("Getting Lock File...",end="",flush=True)
    with open(fileLock_file,'w') as fp:
        with flock.Flock(fp,flock.LOCK_EX) as lock:
            print("Lock secured")
            clearFolders()
            makeStatic("Next Post")
            makeThumbnail(subName,episodeNum)
            makeTitle(vid_title,voice_text,name)

            for i in range(len(listOfPosts)):
                    postText = listOfPosts[i][0]
                    user = listOfPosts[i][1]
                    outImgAndSound(postText,user,i)
                    makeFullPostVideo(i,name)
            makeFullVideo(name)
            vid_file = "../../out/{}.mp4".format(name)
            vid_title = "Best of {} Episode {} [The Reddit Experiment]".format(urlKey,episodeNum)
            vid_des = "Reddit posts directly from {}, read aloud for your convience and pleasure :) ".format(urlKey)
            subJustName = urlKey[2:]
            vid_des += "\n#{} #Reddit #TheRedditExperiment".format(subJustName)
            vid_des+= "\n\nRead the posts in this video:\n"
            vid_des+= '\n'.join("{}: {}".format(index,value) for index,value in enumerate(usedLinks,start=1))
            if debug==True:
                print("Skipping upload [Debug Mode]")
                sys.exit(0)
            ret = upload_video(vid_file,vid_title,vid_des,playlist)
            print("Return from upload:",ret)
            if ret!=0:
                sys.exit(-1)
            urlDict['episodeNumber'] = episodeNum+1
            readDict[urlKey] = urlDict
            writePreviouslyRead(readDict)
    sys.exit(0)
