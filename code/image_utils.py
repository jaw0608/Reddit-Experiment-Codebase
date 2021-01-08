#!/usr/bin/env python
# -*-coding: utf-8 -*-

# Copyright 2011 Álvaro Justen [alvarojusten at gmail dot com]
# License: GPL <http://www.gnu.org/copyleft/gpl.html>

from PIL import Image
from PIL import ImageDraw
from PIL import ImageFont


class ImageText(object):
    def __init__(self, filename_or_size, mode='RGBA', background=(0, 0, 0, 0),overlay = None,overlay_height=500
                 ,border=50,encoding='utf8'):
        if border<50:
            border=50
        if isinstance(filename_or_size, str):
            self.filename = filename_or_size
            self.image = Image.open(self.filename)
            self.size = self.image.size
            if overlay!=None:
                overlay_size = [self.size[0]-(2*border)+5,int(overlay_height)] #+5 since text sometimes goes over
                over = Image.new(mode, (overlay_size[0],overlay_size[1]), color=overlay)
                hBorder = (self.size[1]-overlay_size[1])/2
                if hBorder<0:
                    print("Overlay height to large, wen't negative.")
                    hBorder=0
                self.image.paste(over,(border,int(hBorder)), over)
        elif isinstance(filename_or_size, (list, tuple)):
            self.size = filename_or_size
            self.image = Image.new(mode, self.size, color=background)
            self.filename = None
        self.draw = ImageDraw.Draw(self.image)
        self.encoding = encoding
        user=None
        if user!=None:
            upvote = Image.open("../static/img/ud.png")
            hBorder = (self.size[1]-overlay_height)//2
            self.image.paste(upvote,(int(20),int(hBorder+20)),upvote)
            self.write_text_box((border+15,hBorder-5),user,box_width=self.size[0],font_filename = '../static/fonts/Raleway-Light.ttf',font_size = 25,color = (255, 255, 255))


    def stamp_arrows(self,x,y):
        upvote = Image.open("../static/img/ud.png")
        self.image.paste(upvote,(int(20),int(y)),upvote)

    def save(self, filename=None):
        self.image.save(filename or self.filename)

    def get_image(self):
	       return self.image

    def get_font_size(self, text, font, max_width=None, max_height=None):
        if max_width is None and max_height is None:
            raise ValueError('You need to pass max_width or max_height')
        font_size = 1
        text_size = self.get_text_size(font, font_size, text)
        if (max_width is not None and text_size[0] > max_width) or \
           (max_height is not None and text_size[1] > max_height):
            raise ValueError("Text can't be filled in only (%dpx, %dpx)" % \
                    text_size)
        while True:
            if (max_width is not None and text_size[0] >= max_width) or \
               (max_height is not None and text_size[1] >= max_height):
                return font_size - 1
            font_size += 1
            text_size = self.get_text_size(font, font_size, text)

    def write_text(self, coord, text, font_filename, font_size=11,
                   color=(0, 0, 0), max_width=None, max_height=None):
        x = coord[0]
        y = coord[1]
        if isinstance(text, str):
            text = text
        if font_size == 'fill' and \
           (max_width is not None or max_height is not None):
            font_size = self.get_font_size(text, font_filename, max_width,
                                           max_height)
        text_size = self.get_text_size(font_filename, font_size, text)
        font = ImageFont.truetype(font_filename, font_size)
        if x == 'center':
            x = (self.size[0] - text_size[0]) / 2
        if y == 'center':
            y = (self.size[1] - text_size[1]) / 2
        self.draw.text((x, y), text, font=font, fill=color)
        return text_size

    def get_text_size(self, font_filename, font_size, text):
        font = ImageFont.truetype(font_filename, font_size)
        return font.getsize(text)

    def write_text_box(self, coord, text, box_width, font_filename,
                       font_size=11, color=(0, 0, 0), place='left',
                       justify_last_line=False,getHeight=0):
        x = coord[0]
        y = coord[1]
        x1 = box_width
        x1_sat=True
        x1_fit = True
        try:
            x1=coord[2]
            x1_sat = False
            x1_fit = False
        except:
            x1=box_width
            x1_sat = True
            x1_fit = False

        lines = []
        line = []
        words = text.split()
        for word in words:
            new_line = ' '.join(line + [word])
            size = self.get_text_size(font_filename, font_size, new_line)
            text_height = size[1]
            if x1_sat==False and size[0]<=box_width-x1:
                #print("Added '{}' to line".format(word))
                #print("Total size: {}".format(size[0]+x1))
                line.append(word)
            elif x1_sat==False:
                if len(line)==0:
                    #print("Added: {} since {} was to big for {}".format(line,size[0],box_width-x1))
                    x1_fit = False
                    y+=text_height
                else:
                    #print("Added on previous: ",line)
                    x1_fit = True
                x1_sat = True
                lines.append(line)
                line = [word]
            elif size[0] <= box_width:
                line.append(word)
            else:
                #print("Added: ",line)
                lines.append(line)
                line = [word]
        if line:
            if x1_sat==False and size[0]<=box_width-x1:
                x1_fit = True
            elif x1_sat==False:
                y+=text_height
            #print("Added: ",line)
            lines.append(line)
        lines = [' '.join(line) for line in lines if line]
        height = y
        lastWidth = box_width
        text_height = 0
        for index, line in enumerate(lines):
            line = " "+line
            line = line.replace("~"," ")
            text_height =self.get_text_size(font_filename, font_size, line)[1]
            #print(index)
            if index==0 and x1_fit==True:
                total_size = self.get_text_size(font_filename, font_size, line)
                lastWidth = x1+total_size[0]
                self.write_text((x1, height), line, font_filename, font_size,
                                color)
            elif place == 'left':
                total_size = self.get_text_size(font_filename, font_size, line)
                lastWidth = total_size[0]+x
                self.write_text((x, height), line, font_filename, font_size,
                                color)
            elif place == 'right':
                total_size = self.get_text_size(font_filename, font_size, line)
                x_left = x + box_width - total_size[0]
                lastWidth = total_size[0]+x_left
                self.write_text((x_left, height), line, font_filename,
                                font_size, color)
            elif place == 'center':
                total_size = self.get_text_size(font_filename, font_size, line)
                x_left = int(x + ((box_width - total_size[0]) / 2))
                lastWidth = total_size[0]+x_left
                self.write_text((x_left, height), line, font_filename,
                                font_size, color)
            elif place == 'justify':
                words = line.split()
                if (index == len(lines) - 1 and not justify_last_line) or \
                   len(words) == 1:
                    self.write_text((x, height), line, font_filename, font_size,
                                    color)
                    continue
                line_without_spaces = ''.join(words)
                total_size = self.get_text_size(font_filename, font_size,
                                                line_without_spaces)
                space_width = (box_width - total_size[0]) / (len(words) - 1.0)
                start_x = x
                for word in words[:-1]:
                    self.write_text((start_x, height), word, font_filename,
                                    font_size, color)
                    word_size = self.get_text_size(font_filename, font_size,
                                                    word)
                    start_x += word_size[0] + space_width
                last_word_size = self.get_text_size(font_filename, font_size,
                                                    words[-1])
                last_word_x = x + box_width - last_word_size[0]
                self.write_text((last_word_x, height), words[-1], font_filename,
                                font_size, color)
                lastWidth = last_word_x
            height += text_height
        if getHeight==0:
            height-=text_height
        return (lastWidth, height)
