import tkinter as tk
from selenium import webdriver
from selenium.common import exceptions
from selenium.webdriver.common.keys import Keys
import re
import subprocess
from subprocess import call
from PIL import Image
from PIL import ImageFont
import os,shutil
import sys
import math
import time
import json
import flock
from image_utils import ImageText
import byText
posts = []
master = 0
frame = 0
g_row = 0
parent_stack = [0]
last_level = 0
fileLock_file = '../data/lock'
word_length = 0.0
video_length = 0
video_length_sec = 0

base_keywords = ["r/AskReddit","Reddit","Read aloud","Text to speech"]


#class for comment section: '._1YCqQVO-9r-Up6QPB9H6_4._1YCqQVO-9r-Up6QPB9H6_4'
#iterate through the divs

class postStruct:
    def __init__(self, user,level,div,parent,textList):
        global g_row
        self.user = user
        self.div = div
        self.level = level
        self.parent = parent
        self.id = g_row
        self.selected = tk.BooleanVar()
        self.textList = textList
        self.kids = []
        padding = (level-1)*100
        check = tk.Checkbutton(frame, text=div, variable=self.selected, command = self.update_video_length,wraplength=width-padding-1200,justify=tk.LEFT,font=("Courier", 20))
        check.grid(row=g_row,column=0,padx=(level-1)*100,pady=25,sticky="W")
        check["bg"] = bgColor
        if self.parent!=0:
            self.parent.passUp(self)

    def __str__(self):
        if self.parent!=0:
            return "ID: {} User: {} Level: {} Parent: {} Text: {}...".format(self.id,self.user,self.level, self.parent.id,self.div[:10])
        else:
            return "ID: {} User: {} Level: {} Parent: None Text: {}...".format(self.id,self.user,self.level,self.div[:10])

    def passUp(self,kid):
        try:
            self.kids+=[kid]
            if self.parent!=0:
                self.parent.passUp(kid)
        except Exception as e:
            print(str(e))
            print("Passup fail")

    def update_video_length(self):
        global word_length
        global video_length
        global video_length_sec
        num_words = len(self.div.split(" "))
        if self.selected.get()==True:
            word_length+=num_words
        else:
            word_length-=num_words
        l = word_length/byText.get_WPM()
        l = str(l)
        l = l.split(".")
        if len(l)>=1:
            video_length.set("Minutes:"+l[0])
        else:
            video_length.set("Minutes:0")
        if len(l)==2:
            l[1] = float("0."+l[1])
            video_length_sec.set("Seconds:"+str(int(l[1]*60)))
        else:
            video_length_sec.set("Seconds:0")


def submit():
    global name
    used = 0
    name = byText.formatName(name)
    title = titleBoxText.get()
    desc = descriptionBoxText.get()
    introQuestion = introBoxText.get()
    frame.destroy()
    print("**************************************")
    print("Starting Video Creation")
    print("**************************************\n")

    print("Getting Lock File...",end="",flush=True)
    with open(fileLock_file,'w') as fp:
        with flock.Flock(fp,flock.LOCK_EX) as lock:
            print("Lock secured")
            byText.clearFolders()
            byText.makeTitle(introQuestion,introQuestion+"...Be sure to Subscribe!",name)
            byText.makeStatic("Next Comment")
            for index,i in enumerate(posts):
                if i.selected.get()==True and i.parent==0:
                    list_posts = [i]+i.kids
                    imgNumber = 0
                    for post in list_posts:
                        imgNumber = byText.outImgAndSound(post.textList,post.user,used,imgNumber)+1
                    byText.makeFullPostVideo(used,name)
                    used+=1
            byText.makeFullVideo(name)
            vid_file = "../../out/{}.mp4".format(name)
            if len(sys.argv)==1:
                print("Video made but not uploaded. Exiting!")
                driver.quit()
                sys.exit(0)
            ret = upload_video(vid_file,title,desc)
            if ret==0:
                print("Video created!")
            else:
                print("Failed to create video")
            driver.quit()
            sys.exit(0)

def strip__out_of_range_characters(tweet):
    char_list = [tweet[j] for j in range(len(tweet)) if ord(tweet[j]) in range(65536)]
    tweet=''
    for j in char_list:
        tweet=tweet+j
    return tweet

def new_checkbox(user,level,div,textList):
    global g_row
    global last_level
    global parent_stack
    if level>3:
        return
    if level<last_level:
        for x in range(0,last_level-level+1):
            pop_parent()
    elif level==last_level:
        pop_parent()

    div = strip__out_of_range_characters(div)
    post = postStruct(user,level,div,parent_stack[-1],textList)
    posts.append(post)
    parent_stack.append(post)
    last_level = level
    g_row+=1
    return post

def scroll_to_last(elements,driver):
    last = elements[-1]
    try:
        driver.execute_script("arguments[0].scrollIntoView();",last)
        time.sleep(1) #give extra time to load new elements
    except:
        print("Fail to scroll")
        pass

def upload_video(vid_file,vid_title,vid_des,playlist=None,keywords=[]):
    if len(sys.argv)==1:
        print("Video saved but not uploaded. Filename: {}".format(name))

    keys = base_keywords+keywords
    keys = ','.join(keys)
    if playlist==None:
        ret = call(['python3','../upload/custom_upload_video.py',"--file={}".format(vid_file),"--title={}".format(vid_title), "--description={}".format(vid_des), "--keywords={}".format(keys)])
    else:
        ret = call(['python3','../upload/custom_upload_video.py',"-p={}".format(playlist),"--file={}".format(vid_file),"--title={}".format(vid_title), "--description={}".format(vid_des), "--keywords={}".format(keys)])
    return ret

def get_comments(url,isComment=False,start_level=0):
    if (start_level>7):
        return []
    global driver
    print("Doing comments for {} (start: {}, isComment:{})".format(url,start_level,isComment))
    driver.get(url)
    driver.execute_script("return document.getElementsByClassName('_1tvdSTbdxaK-BnUbzUIqIY _2GyPfdsi-MbQFyHRECo9GO cx1ohrUAq6ARaXTX2u8YN')[0].remove();");
    all_comments = []
    clickables = set()
    try:
        try:
            button = driver.find_element_by_css_selector('._2JBsHFobuapzGwpHQjrDlD.j9NixHqtN2j8SKHcdJ0om._2nelDm85zKKmuD94NequP0')
            if button!=None:
                button.click()
        except:
            print("No button to click")
        attempt = 0
        while 1==1:
            print("Searching for more comments...",end="")
            comments_section = driver.find_element_by_css_selector('._1YCqQVO-9r-Up6QPB9H6_4._1YCqQVO-9r-Up6QPB9H6_4')
            try:
                new_clickables = comments_section.find_elements_by_css_selector('._3_mqV5-KnILOxl1TvgYtCk')
                new_clickables = set(new_clickables)
                print("(Doing clickables: )",len(new_clickables.difference(clickables)))
                for i in new_clickables.difference(clickables):
                    kid = i.find_element_by_xpath("p")
                    driver.execute_script("arguments[0].scrollIntoView(true)",kid)
                    kid.click()
                print("Clicked more replies")
                clickables = new_clickables.copy()
                time.sleep(2)
            except exceptions.StaleElementReferenceException as e:
                pass
            except Exception as e:
                print(str(e))
                pass
            comments_list = comments_section.find_elements_by_xpath('div')

            if len(comments_list)>1000:
                all_comments=comments_list
                print("Found comments")
                print("Hit comment max")
                break

            if len(all_comments)>0 and len(comments_list)>0 and all_comments[-1]==comments_list[-1]:
                print("No comments found")
                if attempt>3: #assume no more comments
                    break
                attempt+=1
                scroll_to_last(comments_list,driver)
                continue
            elif len(comments_list)>0:
                if isComment==True:
                    comments_list = comments_list[1:]
                all_comments=comments_list
                print("Found comments")
                attempt = 0
        last_thread_level = 0
        previous_post = None
        final_all_comments = all_comments[:]
        post_infos_only = []
        wasclick = False
        for i in all_comments:
            d  = {}
            d["text"] = i.text

            try:
                d["comment"] = i.find_element_by_xpath('.//*[@data-test-id="comment"]').text
                d["ref"] = ""
                d["textList"] = parseElement(i.find_element_by_xpath('.//*[@data-test-id="comment"]'))
            except:
                try:
                    d["comment"] = ""
                    d["ref"] = i.find_element_by_xpath(".//a[contains(@class, 'b57A3J7QBa7TvY8XeupVn')]").get_attribute("href")
                    d["textList"] = []
                except:
                    continue
            post_infos_only.append(d)
        length = len(post_infos_only)
        prev_percentage = 0
        for index,i in enumerate(post_infos_only):
            if int(index/length*100)>prev_percentage:
                prev_percentage = int(index/length*100)
                sys.stdout.write("\rPercent done: {} ".format(int(index/length*100)))
                sys.stdout.flush()
            if isThread(i):
                try:
                    #print("New URL For Thread: ", repr(previous_post["text"])[:10])
                    ref = i["ref"]
                    new_set = get_comments(ref,True,last_thread_level-1)
                    final_all_comments += new_set
                    continue
                except:
                    continue

            level,user = level_user(i["text"])
            if level==0 and user==0:
                continue
            try:
                comment = i["comment"]
                last_thread_level = level+start_level
                new_checkbox(user,last_thread_level,comment,i["textList"])
                previous_post = i
                final_all_comments+=[i]
            except Exception as e:
                print(str(e))
                print("Failed (no comment):",repr(i["text"])[:10])
                continue

        print("Leaving comments!")
        return final_all_comments
    except Exception as e:
        print(str(e))
        print("Error when opening url: is this a reddit post?")
        print("Leaving comments!")
        return []

def parseElement(comment):
    try:
        div = comment.find_element_by_xpath('./div')
        children = div.find_elements_by_xpath('./*')
        textList = []
        for el in children:
            if len(el.text)>0:
                if el.tag_name=="ul":
                    items = el.find_elements_by_xpath('./li')
                    for item in items:
                        links = byText.getLinks(item)
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
                    links = byText.getLinks(el)
                    for link in links:
                        el.text.replace(link,"<Link>")
                    strings = re.findall('[^?.!;]+[?.!;]*[ "]*',el.text)
                    #^^finds any amount of characters followed by any amount of punctuation
                    #print(strings)
                    if len(strings)==0:
                        strings = [el.text]
                    typeList = []
                    for l in range(len(strings)):
                        typeList.append(el.tag_name)

                    strings.append(0)
                    typeList.append("BREAK")
                    textList+=list(zip(strings,typeList))
        return textList
    except Exception as e:
        print(e)
        return []




def isThread(el):
    return el["text"]=="Continue this thread\n "

def isMoreReplies(el):
    spaceIndex = el.text.find(" ")+1
    return el.text[spaceIndex:]=="more replies" or el.text[spaceIndex:]=="more reply"

def pop_parent():
    global parent_stack
    parent_stack = parent_stack[:-1]

def level_user(text):
    ogText = text
    try:
        levelI = text.find("\n")
        level = text[6:levelI]
        level = int(level)
        text = text[levelI+1:]
        userI = text.find("\n")
        user = text[:userI]
        return level,user
    except:
        print("Failed to get user and level",repr(ogText))
        return 0,0

def on_configure(event):
    # update scrollregion after starting 'mainloop'
    # when all widgets are in canvas
    canvas.configure(scrollregion=canvas.bbox('all'))

def on_mousewheel(event):
    # update scrollregion after starting 'mainloop'
    # when all widgets are in canvas
    canvas.yview_scroll(-1*(event.delta), "units")


if __name__=="__main__":

    if len(sys.argv)>1:
        url = sys.argv[1]
    else:
        print("Default mode, no uploading!")
        url = 'https://www.reddit.com/r/entitledparents/comments/gqnnhw/ed_demands_a_meeting_room_to_speak_with_his/'

    name = "output"
    bgColor = "#a5b2d1"
    width = 2000
    height = 1200
    screenSize = "{}x{}".format(width,height)

    # --- setup scrollable canvas GUI ---
    root = tk.Tk()
    root.geometry(screenSize)
    root["bg"] = bgColor

    video_length = tk.StringVar()
    video_length.set("Minutes:0")
    video_length_sec = tk.StringVar()
    video_length_sec.set("Seconds:0")

    length_box = tk.Frame(root,width=200,height=100,borderwidth=0)
    length_box["bg"] = bgColor
    length_box.grid(row=0,column=0,sticky="NWE")

    lengthLabel = tk.Label(length_box, textvariable=video_length, height=4,borderwidth=0)
    lengthLabel["bg"] = bgColor
    lengthLabel.grid(row=0,column=0,sticky="NW")

    lengthLabel_sec = tk.Label(length_box, textvariable=video_length_sec, height=4,borderwidth=0)
    lengthLabel_sec["bg"] = bgColor
    lengthLabel_sec.grid(row=0,column=1,sticky="NW")

    canvas = tk.Canvas(root,borderwidth=0,highlightthickness=0)
    canvas.grid(row=1,column=0,sticky="NWES")

    scrollbar = tk.Scrollbar(root, command=canvas.yview,borderwidth=0)
    scrollbar.grid(row=1,column=1,sticky="NS")
    scrollbar["bg"] = bgColor
    scrollbar["troughcolor"] = bgColor


    canvas.configure(yscrollcommand = scrollbar.set)

    scrollbarH = tk.Scrollbar(root, command=canvas.xview, orient=tk.HORIZONTAL,borderwidth=0)
    scrollbarH.grid(row=2,column=0,sticky="WE")
    scrollbarH["bg"] = bgColor
    scrollbarH["troughcolor"] = bgColor

    canvas.configure(xscrollcommand = scrollbarH.set)
    root.grid_rowconfigure(0, weight=0)
    root.grid_columnconfigure(0, weight=1)
    root.grid_rowconfigure(1, weight=1)
    canvas.grid_rowconfigure(0, weight=1)
    canvas.grid_columnconfigure(0, weight=1)
    canvas["bg"] = bgColor


    # update scrollregion after starting 'mainloop'
    # when all widgets are in canvas
    root.bind_all("<MouseWheel>", on_mousewheel)
    canvas.bind('<Configure>', on_configure)

    # --- put frame in canvas ---

    frame = tk.Frame(canvas,borderwidth=0,highlightthickness=0)
    frame["bg"] = bgColor
    frame.grid(row=0,column=0,stick="NWES")
    canvas.create_window((0,0), window=frame, anchor='nw')
    frame.grid_rowconfigure(0, weight=1)
    frame.grid_columnconfigure(0, weight=1)

    #make textbox for title and description
    titleLabelText = tk.StringVar()
    titleLabelText.set("Video Title:")
    titleLabel=tk.Label(frame, textvariable=titleLabelText, height=4)
    titleLabel["bg"] = bgColor
    titleLabel.grid(row=0,column=0,sticky="W")
    titleBoxText=tk.StringVar(None)
    titleBox=tk.Entry(frame,textvariable=titleBoxText,width=50)
    titleBox.grid(row=0,column=0,padx=150,sticky="W")

    descriptionLabelText = tk.StringVar()
    descriptionLabelText.set("Video Description:")
    descriptionLabel=tk.Label(frame, textvariable=descriptionLabelText, height=4)
    descriptionLabel["bg"] = bgColor
    descriptionLabel.grid(row=1,column=0,sticky="W")
    descriptionBoxText=tk.StringVar(None)
    descriptionBox=tk.Entry(frame,textvariable=descriptionBoxText,width=50)
    descriptionBox.grid(row=1,column=0,padx=150,sticky="W")

    introLabelText = tk.StringVar()
    introLabelText.set("Intro Question Text:")
    introLabel=tk.Label(frame, textvariable=introLabelText, height=4)
    introLabel["bg"] = bgColor
    introLabel.grid(row=2,column=0,sticky="W")
    introBoxText=tk.StringVar(None)
    introBox=tk.Entry(frame,textvariable=introBoxText,width=50)
    introBox.grid(row=2,column=0,padx=150,sticky="W")

    g_row = 3


    options = webdriver.ChromeOptions()
    options.headless = False
    options.add_argument('--profile-directory=Profile 1') #which chrome profile
    options.add_argument("user-data-dir=/Users/joe/Library/Application Support/Google/Chrome/Profile 1") #Path to your chrome profile
    driver = webdriver.Chrome(options=options)
    get_comments(url)
    submitBtn = tk.Button(frame, text="Submit", width=10, command=submit)
    submitBtn.grid(row=g_row, column=0,pady=25,sticky="S")

    print("**************************************")
    print("Starting Comment Selection")
    print("**************************************\n")
    root.mainloop()
    driver.quit()
    #for i in posts:
    #    print(i)
