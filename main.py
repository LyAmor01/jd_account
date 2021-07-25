# coding=UTF-8
import os
import requests
import configparser
import jd_pc_ck
import jd_m_ck

headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko)'}


def get_account(file_name='config.ini'):
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
        with open(file_name, 'w') as f:
            config.write(f)
    return config.items('account')


def string_to_cookies(string):
    try:
        item_list = string.split(';')
        cookies_dict = {}
        for item in item_list:
            if item:
                name, value = item.strip().split('=', 1)
                cookies_dict[name] = value
        cookies = requests.utils.cookiejar_from_dict(cookies_dict, cookiejar=None, overwrite=True)
        return cookies
    except Exception as e:
        print(e)


if __name__ == '__main__':
    print('Power By JACK')
    account_list = get_account()
    mode = int(input('请选择模式（1.获取电脑端ck 2.获取手机端ck 3.验证电脑端ck 4.验证手机端ck）：'))
    if mode == 1:
        count = int(input('请输入账号数量'))
        for i in range(0, count):
            input("输入任意值后扫码登陆")
            jd_pc_ck.login_by_qr_code()
    elif mode == 2:
        count = int(input('请输入账号数量'))
        for i in range(0, count):
            input("输入任意值后扫码登陆")
            jd_m_ck.login_by_qr_code()
    elif mode == 3:
        for account in account_list:
            session = requests.session()
            cookies = string_to_cookies(account[1])
            session.headers = headers
            session.cookies = cookies
            print('【{}】'.format(account[0]))
            jd_pc_ck.check_login(session)
    elif mode == 4:
        for account in account_list:
            session = requests.session()
            cookies = string_to_cookies(account[1])
            session.headers = headers
            session.cookies = cookies
            print('【{}】'.format(account[0]))
            jd_m_ck.check_login(session)
    else:
        print('输入不合法')
    input("\n")
