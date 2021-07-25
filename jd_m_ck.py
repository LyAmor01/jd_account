# coding=UTF-8
import os
import re
import sys
import json
import time
import qrcode
import requests
import configparser

headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko)'}


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


def get_qr_code(m_token):
    url = 'https://plogin.m.jd.com/cgi-bin/m/tmauth?appid=300&client_type=m&token=' + m_token
    img = qrcode.make(url)
    img.save('qr_code.png')
    print('获取二维码成功，请打开京东APP扫描')
    open_image('qr_code.png')


def get_s_token(session):
    state = str(int(time.time()))
    url = 'https://plogin.m.jd.com/cgi-bin/mm/new_login_entrance?lang=chs&appid=300&returnurl=https://wq.jd.com/passport/LoginRedirect?state=' + state + \
          '&returnurl=https://home.m.jd.com/myJd/newhome.action?sceneval=2&ufc=&/myJd/home.action&source=wq_passport'
    headers[
        'Referer'] = 'https://plogin.m.jd.com/login/login?appid=300&returnurl=https://wq.jd.com/passport/LoginRedirect?state=' + state + \
                     '&returnurl=https://home.m.jd.com/myJd/newhome.action?sceneval=2&ufc=&/myJd/home.action&source=wq_passport'
    try:
        resp = session.get(url=url, headers=headers)
        resp_json = json.loads(resp.text)
        return resp_json.get('s_token')
    except Exception as e:
        print(e)


def get_m_okl_token(session, s_token):
    state = str(int(time.time()))
    url = 'https://plogin.m.jd.com/cgi-bin/m/tmauthreflogurl?remember=true&v=' + state + '&s_token=' + s_token
    data = {
        'lang': 'chs',
        'appid': '300',
        'returnurl': 'https://wqlogin2.jd.com/passport/LoginRedirect?state=' + state +
                     '&returnurl=//home.m.jd.com/myJd/newhome.action?sceneval=2&ufc=&/myJd/home.action',
    }
    headers[
        'Referer'] = 'https://plogin.m.jd.com/login/login?appid=300&returnurl=https://wq.jd.com/passport/LoginRedirect?state=' + state + \
                     '&returnurl=https://home.m.jd.com/myJd/newhome.action?sceneval=2&ufc=&/myJd/home.action&source=wq_passport'
    try:
        resp = session.post(url=url, data=data, headers=headers)
        resp_json = json.loads(resp.text)
        cookies = resp.headers.get('set-cookie')
        return resp_json.get('token'), cookies[10:18]
    except Exception as e:
        print(e)


def check_token(session, m_token, okl_token):
    state = str(int(time.time()))
    url = 'https://plogin.m.jd.com/cgi-bin/m/tmauthchecktoken?&ou_state=0&token=' + m_token + '&okl_token=' + okl_token
    data = {
        'lang': 'chs',
        'appid': '300',
        'returnurl': 'https://wqlogin2.jd.com/passport/LoginRedirect?state=' + state +
                     '&returnurl=//home.m.jd.com/myJd/newhome.action?sceneval=2&ufc=&/myJd/home.action',
    }
    headers[
        'Referer'] = 'https://plogin.m.jd.com/login/login?appid=300&returnurl=https://wqlogin2.jd.com/passport/LoginRedirect?state=' + state + \
                     '&returnurl=//home.m.jd.com/myJd/newhome.action?sceneval=2&ufc=&/myJd/home.action&source=wq_passport'
    try:
        resp = session.post(url=url, data=data, headers=headers)
        resp_json = json.loads(resp.text)
        print(resp_json)
        if resp_json.get('errcode') == 0:
            print('已完成手机客户端确认')
            return True
        else:
            return False
    except Exception as e:
        print(e)


def get_user_info(session):
    url = 'https://me-api.jd.com/user_new/info/GetJDUserInfoUnion'
    try:
        resp = session.get(url=url, headers=headers)
        resp_json = json.loads(resp.text)
        return resp_json.get('data', {}).get('userInfo', {}).get('baseInfo', {}).get('nickname')
    except Exception:
        return 'jd'


def check_login(session):
    url = 'https://wq.jd.com/user/info/GetUserAllPinInfo?sceneval=2'
    headers['Referer'] = 'https://wqs.jd.com/'
    try:
        resp = session.get(url=url, headers=headers)
        if re.findall('no login', resp.text):
            print('校验登录失败')
            return False
        else:
            nick_name = get_user_info(session)
            print('登录成功用户【{}】'.format(nick_name))
            return True
    except Exception as e:
        print(e)


def login_by_qr_code():
    session = requests.session()
    s_token = get_s_token(session)
    m_token, okl_token = get_m_okl_token(session, s_token)
    if not (s_token and m_token and okl_token):
        print('获取token失败')
        sys.exit()
    get_qr_code(m_token)
    for i in range(0, 80):
        if check_token(session, m_token, okl_token):
            break
        time.sleep(2)
    else:
        print('二维码过期，请重新获取扫描')
        sys.exit()
    if check_login(session):
        save_cookies(session.cookies)
