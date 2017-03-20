#! /usr/bin/env python3

import os
import json
import urllib
import argparse
import requests
import urllib.parse
from urllib.request import urlretrieve
from bs4 import BeautifulSoup
import shutil
from os.path import join
import http.client as httplib
import api_keys

MICROSOFT_VISION_API_KEY = api_keys.API_KEY
ALLOWED_IMAGE_EXTENSIONS = ['.jpeg', '.jpg', '.png']


def is_exists(path):
    if os.path.exists(path):
        return True
    else:
        print("Could not find the given file - ", path)
        return False


def get_all_images(url, dir):
    page = requests.get(url)
    soup = BeautifulSoup(page.text, "html.parser")
    images = []
    #os.mkdir('pic_temp', 777)
    for img in soup.select('img'):
        img_url = urllib.parse.urljoin(url, img['src'])
        temp_name = img['src'].split('/')[-1]
        urlretrieve(img_url, temp_name)
        images.append(temp_name)
        temp_path = os.path.abspath(temp_name)
        perm_path = dir + temp_name
        os.rename(temp_path, perm_path)
    return images


def get_extension(file):
    file, ext = os.path.splitext(file)
    return ext


def rename_img(old, new, base_dir):
    if is_exists(old):
        ext = get_extension(old).lower()
        os.rename(old, join(base_dir,str(new) + ext))
        print("Renaming ", old, "to ",  new + ext)


def get_caption(image_src):
    headers = {
        'Content-Type': 'application/json',
        'Ocp-Apim-Subscription-Key': MICROSOFT_VISION_API_KEY,
    }
    params = urllib.parse.urlencode({
        'maxCandidates': '1',
    })
    data = json.dumps({"Url": image_src}, separators=(',', ':'))
    try:
        conn = httplib.HTTPSConnection('api.projectoxford.ai')
        conn.request("POST", "/vision/v1.0/describe?%s" % params, data, headers)
        response = conn.getresponse()
        response_data = response.read().decode('utf-8')
        json_data = json.loads(response_data)
        caption_text = json_data['description']['captions'][0]['text']
        conn.close()
        return caption_text
    except Exception as e:
        print("Exception while communicating with vision api- ", e)


def upload(image_address):
    if is_exists(image_address):
        url = "http://uploads.im/api"
        files = {'media': open(image_address, 'rb')}
        request = requests.post(url, files=files)
        data = json.loads(request.text)
        image_url = data[u'data'][u'img_url']
        main_url = image_url.encode('ascii', 'ignore')
        return main_url.decode('utf-8')


def full_path(base, file):
    if base[-1] is not "/":
        return base + "/" + file
    else:
        return base + file


def init(url, dir):
    print(url)
    print(dir)
    images = get_all_images(url, dir)
    for image_name in images:
        file_path = dir + image_name
        print("Processing image - ", image_name)
        print(file_path)
        image_url = upload(file_path)
        new_name = get_caption(image_url)
        rename_img(image_name, new_name, dir)


def arg_parser():
    parser = argparse.ArgumentParser()
    parser.add_argument('url', help="Url of web page with images to scrape", type=str)
    parser.add_argument('dir', help="Directory to place the images", type=str)
    args = parser.parse_args()

    try:
        init(args.url, args.dir)
    except ValueError:
        print("Try again")


if __name__ == '__main__':
    arg_parser()
