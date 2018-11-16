import requests
import time as t
from PIL import Image, ImageDraw, ImageFont
from os import listdir, system, chdir, makedirs
from os.path import isfile, join, exists
import imageio

def make_gif(path, giffilename):
    # Take all images in the folder specified by mypath and turn them into a gif

    print "Turning images into a gif"
    onlyfiles = [f for f in listdir(path) if isfile(join(path, f))]

    with imageio.get_writer(giffilename, mode='I') as writer:
        for filename in onlyfiles:
            if '.png' in filename:
                image = imageio.imread(path + filename)
                writer.append_data(image)

def merge_images(file1, file2, file3, file4):
    # Merge four images into one, window-pane style
    # param file1: path to first (top-left) image file
    # param file2: path to second (top-right) image file
    # param file3: path to third (bottom-left) image file
    # param file4: path to fourth (bottom-right) image file
    # return: the merged Image object
    
    image1 = Image.open(file1)
    image2 = Image.open(file2)
    image3 = Image.open(file3)
    image4 = Image.open(file4)

    (width1, height1) = image1.size

    result1 = Image.new('RGB', (width1 * 2, height1))
    result2 = Image.new('RGB', (width1 * 2, height1))
    result1.paste(im=image1, box=(0, 0))
    result1.paste(im=image2, box=(width1, 0))
    result2.paste(im=image3, box=(0,0))
    result2.paste(im=image4, box=(width1,0))

    result = Image.new('RGB', (width1 * 2, height1 * 2))
    result.paste(im=result1,box=(0,0))
    result.paste(im=result2,box=(0,height1))

    return result

def doMerge(path):
    # Stitch together each set of four pictures in the main folder and put
    # them in the 'merged' folder. Also adds text to the file in (YY-MM-DD and
    # HH:MM:SS).
    print "Stitching images together"
    onlyfiles = [f for f in listdir(path) if isfile(join(path, f))]
    realfiles = []
    index = 0
    for file in onlyfiles:
        realfile = file[:-12]
        if realfile not in realfiles:
            realfiles.append(realfile)
    for file in realfiles:
        if "download" not in file:
            try:
                savefile = merge_images(file + "_002_000.png", file  + "_002_001.png", file  + "_003_000.png", file  + "_003_001.png")
                draw = ImageDraw.Draw(savefile)
                font = ImageFont.truetype("merged/arial.ttf", 24)
                imgtext = file[0:4] + "-" + file[4:6] + "-" + file[6:8] + " UTC " + file[9:11] + ":" + file[11:13] + ":" + file[13:15]
                draw.text((0, 0),imgtext,(255,0,0),font=font)
                savefile.save("merged1/img_" + '%04d'%index + ".png")
                index+=1
            except IOError:
                print "failed to merge images for {}".format(file)

def getDayPics(day, num1, num2):
    # Acquire all of the images from the Colorado State site for the GOES-16
    # satellite. Attempt to intelligently do this when possible by checking in
    # 5 minute intervals if a real URL is found, since this is the interval
    # the images are generally uploaded in. If it fails, goes back to checking
    # every second's worth of URLs until it finds another one. Only pulls the
    # 002_000, 002_001, 003_000, and 003_001 images since those are the only
    # ones relevant to the California fires.
    print "Acquiring images for day {}".format(day)
    minuteholder = 0
    hourholder = 0
    daystring = "{}".format("%02d"%day)
    for hour in range(0,23):
        if (hourholder != 0):
            hour = hourholder
            hourholder = 0
        if (hour >= 24):
            break
        for minute in range(0,60):
            if (hour == 24):
                break
            if (minuteholder != 0):
                minute = minuteholder
                minuteholder = 0
            for second in range(0,60):
                if (hour == 24):
                    break
                timestring = "%02d"%hour + "%02d"%minute + "%02d"%second
                try:
                    url = requests.get("http://rammb-slider.cira.colostate.edu/data/imagery/201811{}/goes-16---conus/natural_color/201811{}{}/03/00{}_00{}.png".format(daystring,daystring,timestring,num1,num2))
                except requests.exceptions.ProxyError:
                    t.sleep(10) # This is here because the server sometimes gets annoyed at being hit so fast, so we give it a break
                    url = requests.get("http://rammb-slider.cira.colostate.edu/data/imagery/201811{}/goes-16---conus/natural_color/201811{}{}/03/00{}_00{}.png".format(daystring,daystring,timestring,num1,num2))
                if (url.status_code == 200):
                    open("201811{}_{}_{}".format(daystring,timestring,str(url.url.split("/")[-1])), "wb").write(url.content)
                    while (url.status_code == 200):
                        minute += 5
                        if minute > 60:
                            minute -= 60
                            hour += 1
                        timestring = "%02d"%hour + "%02d"%minute + "%02d"%second
                        try:
                            url = requests.get("http://rammb-slider.cira.colostate.edu/data/imagery/201811{}/goes-16---conus/natural_color/201811{}{}/03/00{}_00{}.png".format(daystring,daystring,timestring,num1,num2))
                        except requests.exceptions.ProxyError:
                            t.sleep(10)
                            url = requests.get("http://rammb-slider.cira.colostate.edu/data/imagery/201811{}/goes-16---conus/natural_color/201811{}{}/03/00{}_00{}.png".format(daystring,daystring,timestring,num1,num2))
                        if (url.status_code == 200):
                            open("201811{}_{}_{}".format(daystring,timestring,str(url.url.split("/")[-1])), "wb").write(url.content)
                        minuteholder = minute
                        hourholder = hour

def main():
    # First, download all of the images
    for day in range(8,16):
        for num1 in range(2,4):
            for num2 in range(0,2):
                getDayPics(day, num1, num2)

    # create subdir for the merged images
    if not exists('./merged1'):
        makedirs('./merged1')

    # Stich all of the sets of 4 images into single images for that timestamp
    # and add text for date and time
    doMerge('.') # This path is the current directory

    # Turn the images into a gif
    # Decided not to do this because the file is too big. Instead, use ffmpeg
    # to make it a video. Original line:
    #
    #   make_gif('merged', 'fires.gif')
    #
    # New code below.

    chdir('./merged1')
    system('ffmpeg -r 12 -i img_%04d.png -c:v libx264 -vf fps=25 -pix_fmt yuv420p out1.mp4')

    # If you wanted to make a gif, it would be:
    #
    #   system('ffmpeg -r 12 -i img_%04d.png fps=25 out1.gif')
    #
    # But it's ridiculously large file size so probably not worth.
    # Also Windows craps itself when you try to open a gif that big, fun fact.

    print "Done!"

if __name__== "__main__":
    main()

