import praw
import re
from textdistance import damerau_levenshtein as dist
import time
from PIL import Image
import io
import pickle
import requests


with open('bd/data', 'rb') as f:
    data = list(pickle.load(f))

with open('bd/hash_bd', 'rb') as f:
    hash_bd = pickle.load(f)

def auth_reddit():
    print('Auth Reddit')
    UserAgent = ('Mozilla/5.0 (Windows NT 6.2; WOW64; rv:53.0) AppleWebKit/534.50.2 Firefox/'
                 '49.0 Chrome/58.0.2902.81 Chromium/49.0.2623.108 OPR/43.0.2442.849')
    
    client_id = input('client_id >>> ')

    client_secret = input('client_secret >>> ')
    return praw.Reddit(client_secret=client_secret,
                       client_id=client_id,
                       user_agent=UserAgent)

def distance(a, b):
    size = len(a) + len(b)
    y = round(((size - dist(a, b)) / size) * 100, 4)
    return y

def ahash(image, s1=32, s2=32):
    if isinstance(image, bytes):
        im = Image.open(io.BytesIO(image))
    else:
        im = Image.open(image)

    size = s1, s2
    im = im.resize(size, Image.ANTIALIAS)
    im = im.convert('L')
    pixels = list(im.getdata())
    average = sum(pixels) / len(pixels) / 3

    result = ''
    for pixel in pixels:
        if pixel > average * 5:
            result += '3'
        elif pixel > average * 3:
            result += '2'
        elif pixel > average * 1:
            result += '1'
        else:
            result += '0'

    f = ''
    ind = 0
    d = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ"
    r = ''
    for i in result:
        if i == f:
            ind += 1
        else:
            ind += 1
            f = i
            r += d[ind % 36]
            ind = 0

    return r[1:]  #

def dubles(data, item):
    out = []
    hash = ahash(data)
    for i in hash_bd.keys():
        if abs(len(i) - len(hash)) > 24:
            continue

        dis = distance(hash, i)

        if dis > 75:
            out.append([*item, dis])

    hash_bd[hash] = item

    return out

def get_dubles(item):
    res = requests.get(item[1], timeout=60).content
    dub = dubles(res, item)[:10]

    response = ''
    for j, i in enumerate(dub):
        response += f'{j}. {i[1][0]} {i[0]}%\n'

    return response


reddit = auth_reddit()
pikabu = reddit.subreddit('Pikabu')

while True:
    print('get dubles')
    pikabu_new = pikabu.new(limit=25)
    ind = 0
    try:
        for j, i in enumerate(pikabu_new):
            ind += 1
            if re.findall(r'i\.(imgur|redd)\.(com|it).*?\.(jpg|png|bmp)', i.url, flags=re.IGNORECASE):
                item = (i.shortlink, i.url)
                if item not in data:
                    dub = get_dubles(item)
                    if dub:
                        print(dub)
                        dub = '>>> ' + item[0] + '\n' + dub
                        with open('log.txt', 'a') as f:
                            f.write(dub)
                    data.append(item)

                else:
                    print('new post', j)
                    break

            time.sleep(0.2)

    except Exception as ex:
        print('ERROR', ex)

    with open('bd/data', 'wb') as f:
        pickle.dump(data, f)

    with open('bd/hash_bd', 'wb') as f:
        pickle.dump(hash_bd, f)

    time.sleep(60*10)
