# coding=UTF-8
import os
import sys
import json
import time
import random
import requests
import configparser

headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko)'}


def parse_json(js):
    begin = js.find('{')
    end = js.rfind('}') + 1
    return json.loads(js[begin:end])


def save_image(resp, image_file):
    with open(image_file, 'wb') as f:
        for chunk in resp.iter_content(chunk_size=1024):
            f.write(chunk)


def open_image(image_file):
    if os.name == 'nt':
        os.system('start ' + image_file)
    else:
        if os.uname()[0] == 'Linux':
            if 'deepin' in os.uname()[2]:
                os.system('deepin-image-viewer ' + image_file)
            else:
                os.system('eog ' + image_file)
        else:
            os.system('open ' + image_file)


def cookies_to_string(cookies):
    try:
        cookies_dict = requests.utils.dict_from_cookiejar(cookies)
        string = ''
        for item in cookies_dict:
            string += item + '=' + cookies_dict[item] + ';'
        return string[:-1]
    except Exception as e:
        print(e)


def save_cookies(cookies, file_name='config.ini'):
    string = cookies_to_string(cookies)
    file = os.path.join(os.getcwd(), file_name)
    config = configparser.RawConfigParser()
    if not os.path.exists(file):
        config.add_section('account')
        with open(file_name, 'w') as f:
            config.write(f)
    config.read(file, encoding='utf-8-sig')
    sections = config.sections()
    if 'account' not in sections:
        config.add_section('account')
    options = config.options('account')
    config.set('account', 'cookies' + str(len(options) + 1), string)
    with open(file_name, 'w') as f:
        config.write(f)


def get_qr_code(session):
    url = 'https://qr.m.jd.com/show'
    payload = {
        'appid': 133,
        'size': 147,
    }
    try:
        resp = session.get(url=url, params=payload, headers=headers)
        if resp.status_code != requests.codes.OK:
            return False
        qr_code_file = 'qr_code.png'
        save_image(resp, qr_code_file)
        print('获取二维码成功，请打开京东APP扫描')
        open_image(qr_code_file)
        return True
    except Exception as e:
        print(e)


def get_qr_code_ticket(session):
    url = 'https://qr.m.jd.com/check'
    payload = {
        'appid': '133',
        'callback': 'jQuery{}'.format(random.randint(1000000, 9999999)),
        'token': session.cookies.get('wlfstk_smdl'),
    }
    headers['Referer'] = 'https://plogin.m.jd.com/login/login'
    try:
        resp = session.get(url=url, params=payload, headers=headers)
        if resp.status_code != requests.codes.OK:
            print('获取二维码扫描结果失败')
            return ''
        resp_json = parse_json(resp.text)
        print(resp_json)
        if resp_json.get('code') == 200:
            print('已完成手机客户端确认')
            return resp_json.get('ticket')
    except Exception as e:
        print(e)


def check_qr_code_ticket(session, ticket):
    url = 'https://passport.jd.com/uc/qrCodeTicketValidation?t={}'.format(ticket)
    headers['Referer'] = 'https://passport.jd.com/uc/login?ltype=logout'
    try:
        resp = session.get(url=url, headers=headers)
        if resp.status_code != requests.codes.OK:
            return False
        resp_json = json.loads(resp.text)
        if resp_json.get('returnCode') == 0:
            return True
        else:
            return False
    except Exception as e:
        print(e)


def get_user_info(session):
    url = 'https://passport.jd.com/user/petName/getUserInfoForMiniJd.action'
    headers['Referer'] = 'https://order.jd.com/center/list.action'
    try:
        resp = session.get(url=url, headers=headers)
        resp_json = json.loads(resp.text)
        return resp_json.get('nickName')
    except Exception:
        return 'jd'


def check_login(session):
    url = 'https://order.jd.com/center/list.action'
    try:
        resp = session.get(url=url, allow_redirects=False)
        if resp.status_code == requests.codes.OK:
            nick_name = get_user_info(session)
            print('登录成功用户【{}】'.format(nick_name))
            return True
        else:
            print('校验登录失败')
            return False
    except Exception as e:
        print(e)


def login_by_qr_code():
    session = requests.session()
    if not get_qr_code(session):
        print('获取二维码失败')
        sys.exit()
    for i in range(0, 80):
        ticket = get_qr_code_ticket(session)
        if ticket:
            break
        time.sleep(2)
    else:
        print('二维码过期，请重新获取扫描')
        sys.exit()
    if not check_qr_code_ticket(session, ticket):
        print('校验二维码信息失败')
        sys.exit()
    if check_login(session):
        save_cookies(session.cookies)
