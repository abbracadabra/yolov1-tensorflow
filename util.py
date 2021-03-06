import numpy as np
from config import *
import xml.etree.ElementTree as ET
import PIL.Image as Image
import PIL
import colorsys
from PIL import Image
from PIL import ImageDraw
from PIL import ImageFont

def loadlabel(lbpath,flip=False):
    mp={}
    tree = ET.parse(os.path.join(voclabeldir,lbpath))
    root = tree.getroot()
    size = root.find('size')
    w = int(size.find('width').text)
    h = int(size.find('height').text)
    mp['w']=w
    mp['h'] = h
    lzz = []
    for i, obj in enumerate(root.iter('object')):
        lz = []
        lz.append(obj.find('name').text)
        xmlbox = obj.find('bndbox')
        if flip:
            lz.append(w-float(xmlbox.find('xmax').text))
            lz.append(float(xmlbox.find('ymin').text))
            lz.append(w-float(xmlbox.find('xmin').text))
            lz.append(float(xmlbox.find('ymax').text))
        else:
            lz.append(float(xmlbox.find('xmin').text))
            lz.append(float(xmlbox.find('ymin').text))
            lz.append(float(xmlbox.find('xmax').text))
            lz.append(float(xmlbox.find('ymax').text))
        lzz.append(lz)
    mp['object'] = lzz
    return mp

def randomhue(im):
    imhsv = np.array(im.convert('HSV'))
    imhsv[..., 0] = (imhsv[..., 0] + np.random.randint(0, 30)) % 255
    imhsv[..., 1] = (imhsv[..., 0] + np.random.randint(0, 30)) % 255
    imhue = Image.fromarray(imhsv, mode='HSV').convert('RGB')
    return imhue

def constructlabel(im, lbmap, dim):
    newim = Image.new('RGB', (dim, dim), (0, 0, 0))
    w, h = im.size
    objs = lbmap['object']
    if w / dim > h / dim:
        nw = dim
        ratio = dim / w
        nh = int(h * ratio)
        im = im.resize((nw, nh))
    else:
        nh = dim
        ratio = dim / h
        nw = int(w * ratio)
        im = im.resize((nw, nh))
    offsetw = (dim-nw)//2
    offseth = (dim-nh)//2
    newim.paste(im, (offsetw,offseth))
    fms = dim//32
    xy = np.zeros(shape=[fms,fms,1,2])*0.5
    wh = np.zeros(shape=[fms,fms,1,2])
    mask = np.zeros(shape=[fms,fms,1,1])
    cls = np.zeros(shape=[fms,fms,20])
    #draw = ImageDraw.Draw(newim)
    for ob in objs:
        name = ob[0]
        xmin = ob[1]
        ymin = ob[2]
        xmax = ob[3]
        ymax = ob[4]
        w = (xmax-xmin)*ratio/dim
        h = (ymax - ymin) * ratio / dim
        wix = int(((xmin+xmax)//2 * ratio +offsetw)//32)
        hix = int(((ymin + ymax) // 2 * ratio+offseth) //32)
        x = (((xmin + xmax) // 2 * ratio + offsetw) % 32)/32
        y = (((ymin + ymax) // 2 * ratio + offseth) % 32)/32
        mask[hix,wix,0,0] = 1.
        xy[hix,wix,0] = [x,y]
        wh[hix,wix,0] = [w,h]
        cls[hix,wix,labels.index(name)] = 1.
        #draw.rectangle((((x/7+wix/7-(w**2)/2)*224,(y/7+hix/7-(h**2)/2)*224), ((x/7+wix/7+(w**2)/2)*224,(y/7+hix/7+(h**2)/2)*224)), width=1)
        #draw.text(tuple((xy - wh / 2) * 224), str(round(sc, 2)) + "/" + labels[cs], font=ImageFont.truetype("arial"))
        #print(1)
    #newim.show()
    return (np.array(newim),xy,wh,mask,cls)

def preparetest(impath,dim):
    im = Image.open(impath)
    newim = Image.new('RGB', (dim, dim), (0, 0, 0))
    w, h = im.size
    if w / dim > h / dim:
        nw = dim
        ratio = dim / w
        nh = int(h * ratio)
        im = im.resize((nw, nh))
    else:
        nh = dim
        ratio = dim / h
        nw = int(w * ratio)
        im = im.resize((nw, nh))
    offsetw = (dim-nw)//2
    offseth = (dim-nh)//2
    newim.paste(im, (offsetw,offseth))
    return np.array(newim),nw,nh

def loaddata(impaths, lbpaths,dim=224):
    ret = []
    for impath, lbpath in zip(impaths, lbpaths):
        im = Image.open(os.path.join(vocimdir,impath))
        #imf = im.transpose(PIL.Image.FLIP_LEFT_RIGHT)
        lbmap = loadlabel(lbpath,flip=False)
        #lbmapf = loadlabel(lbpath, flip=True)
        #imhue = randomhue(im)
        ret.append(constructlabel(im,lbmap,dim))
        #ret.append(constructlabel(imf, lbmapf,dim))
        #ret.append(constructlabel(imhue, lbmap,dim))
    return ret

def getbatch():
    imlist = os.listdir(vocimdir)
    imlist = np.random.permutation(imlist)
    labellist = [fn.split(".")[0]+".xml" for fn in imlist]
    pos = 0
    while pos < len(imlist):
        subimlist = imlist[pos:pos + trainbatch]
        sublabellist = labellist[pos:pos + trainbatch]
        pos += trainbatch
        res = loaddata(subimlist,sublabellist)
        yield (np.array(_) for _ in zip(*res))




