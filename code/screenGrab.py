from selenium import webdriver
from subprocess import call
import re
from PIL import Image
from PIL import ImageDraw
import os
from pytesseract import image_to_string
IMG_HEIGHT = 600
current_image = 0
testURL = 'https://www.reddit.com/r/entitledparents/comments/ctks38/any_posts_or_comments_that_encourage_or_call_for/'
prevLength = 0
def outImgAndSound(URL,number):

    URL = testURL
    options = webdriver.ChromeOptions()
    options.headless = True

    driver = webdriver.Chrome(options=options)
    driver.get(URL)
    print(URL)

    S = lambda X: driver.execute_script('return document.body.parentNode.scroll'+X)
    driver.set_window_size(S('Width'),S('Height')) # May need manual adjustment
    #el = driver.find_element_by_xpath('//*[@data-test-id="post-content"]/div[5]')
    el = driver.find_element_by_xpath('//*[@data-click-id="text"]')

    path_img_temp = './images/scrape{}.png'.format(number)
    el.screenshot(path_img_temp)
    im = Image.open(path_img_temp)
    h = im.size[1]
    lastHeight=0
    i = 0
    global current_image
    while lastHeight<h and lastHeight!=-1:
        lastHeight = imageCovered(path_img_temp,number,lastHeight+1,i)
        if lastHeight//IMG_HEIGHT !=current_image:
            current_image = lastHeight//IMG_HEIGHT
            i=1
            continue
        i+=1

    #all the pictures should be saved by now. We just have to find a way to do voice for each picture

    # for j in range(0):
    #     str = str+""+str_list[j]
    #     path_img = './images/scrape{}_{}_{}.png'.format(number,imageNum,str_count)
    #     path_voice = './sounds/sound{}_{}_{}.aiff'.format(number,imageNum,str_count)
    #     str_count +=1
    #
    #     call(['say','-v','Daniel','-o',path_voice,str_list[j]])
    #
    #     path_video = './videos/video{}_{}_{}.mp4'.format(number,imageNum,str_count)
    #             #call(['ffmpeg', '-loop', '1', '-i', path_img, '-i', path_voice, '-c:v', 'libx264', '-tune', 'stillimage', '-c:a', 'aac', '-b:a', '192k', '-pix_fmt', 'yuv420p', '-shortest',path_video])
    #     call(['ffmpeg', '-loop','1','-y', '-i', path_img, '-i' ,path_voice, '-shortest', path_video])


            #do voice here



    driver.quit()

def imageCovered(imgPath,number,lastHeight,interval):
    img = Image.open(imgPath)

    #calculate the new height
    newH = getHeight(img,lastHeight)
    if newH==-1:
        return -1
    #make new image file
    imageNumber = newH//IMG_HEIGHT
    global current_image
    if imageNumber!=current_image:
        interval = 0
    imgPath = './images/scrape{}_{}_{}.png'.format(number,imageNumber,interval)
    img.save(imgPath)

    #get width and height for cover
    w = img.size[0]
    h = img.size[1]
    #get heights for cropping
    h2 = (imageNumber+1)*IMG_HEIGHT
    h1 = (imageNumber)*IMG_HEIGHT
    if h2>img.size[1]:
        h2=img.size[1]
    #open new image
    img = Image.open(imgPath)
    draw = ImageDraw.Draw(img)
    draw.rectangle([0,newH,w,h],fill=(255,255,255))
    img = img.crop((0,h1,w,h2))
    img.save(imgPath)

    img = Image.open(imgPath)
    img = img.resize((w*5,h*5), Image.LANCZOS)

    str = image_to_string(img)
    str = str.replace("\n","")
    global prevLength
    str_to_read = str[prevLength:]
    print(str_to_read)
    prevLength = len(str)
    path_voice = './sounds/sound{}_{}_{}.aiff'.format(number,imageNumber,interval)
    #call(['say','-v','Daniel','-o',path_voice,str_to_read])

    return newH

#make a standard width
def makeWidth(imgPath):
    basewidth = 450
    img = Image.open(imgPath)
    wpercent = (basewidth/float(img.size[0]))
    hsize = int((float(img.size[1])*float(wpercent)))
    img = img.resize((basewidth,hsize), Image.ANTIALIAS)
    img.save(imgPath)

#returns height based on pixel hitscan
def getHeight(img,lastHeight):
    startH = lastHeight
    rgb_im = img.convert('RGB')
    xMax = img.size[0]
    yMax = img.size[1]
    x=0
    y=startH
    hitBlack = False

    #while loop to find first black from start height
    while y<yMax:
        r,g,b = rgb_im.getpixel((x,y))
        if(r<100 or b<100 or g<100): #not white
            hitBlack=True
            print("Found black at ", x,y)
            startH = y
            break
        else:
            x+=1
            if x==xMax:
                x=0
                y+=1

    #return fail if we found no black
    if hitBlack==False:
        return -1

    #while loop to keep going until we hit only white in a line
    x=0
    while x<xMax:
        r,g,b = rgb_im.getpixel((x,startH)) #later do for whole line
        if(r<100 or b<100 or g<100): #not white
            startH+=1
            #print("increasing start h because of colors: ", r,g,b, "at pixels ",x,startH)
            x=0
        else:
            x+=1

    return startH


if __name__ == '__main__':
    options = webdriver.ChromeOptions()
    options.headless = True
    driver = webdriver.Chrome(options=options)
    driver.get('https://www.reddit.com/r/entitledparents/new')
    list = driver.find_elements_by_css_selector('.SQnoC3ObvgnGjWt90zD9Z._2INHSNB8V5eaWp4P0rY_mE')
    for i in range(len(list)):
        a = list[i]
        link = a.get_attribute("href")
        outImgAndSound(link,i)
        if i>=0:
            break
    driver.quit()
