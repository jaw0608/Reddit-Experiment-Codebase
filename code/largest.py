from PIL import Image
from PIL import ImageFont
font_filename = './fonts/Raleway-Light.ttf'
font_size = 17
largest = [1,'0']
alphabet = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ1234567890?!@#$%^&*()-+_=\\][';/.,<>:\"`~"
for char in alphabet:
        font = ImageFont.truetype(font_filename, font_size)
        size = font.getsize(char)[1]
        if size>largest[0]:
            largest[0]=size
            largest[1]=char
print(largest)
