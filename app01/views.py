from django.shortcuts import render, HttpResponse
import requests
import time
import re
import json
# Create your views here.


CTIME = None
QCODE = None
TIP = 1
TICKET_DOCT = {}
USER_INIT_IDCT = {}
ALL_COOKIE_DICT = {}

# 微信登录页
def login(request):
    '''
    获取二维码，并在页面显示
    :param request:
    :return:
    '''
    global CTIME
    CTIME = time.time()
    # 获取二维码
    response = requests.get(
        url='https://login.wx.qq.com/jslogin?appid=wx782c26e4c19acffb&fun=new&lang=zh_CN&_= %s' % CTIME
    )
    print(response.text)
    # 使用正则获取
    v = re.findall('uuid = "(.*)";', response.text)
    global QCODE
    QCODE = v[0]
    print(v)
    return render(request, 'login.html', {'qcode': QCODE})


# 检查是否用户扫描了
def check_login(request):
    '''
    监听用户是否扫描-
    监听用户是否已经点击确认-

    注意: url 和 状态码不同
    :param request:
    :return:
    '''
    global TIP
    ret = {'code': 408, 'data': None}
    r1 = requests.get(
        url='https://login.wx.qq.com/cgi-bin/mmwebwx-bin/login?loginicon=true&uuid=%s&tip=%s&r=243571826&_=%s' % (QCODE, TIP, CTIME)
    )
    print(r1.text)  # 如果一直没有扫描就一直是 window.code=408, 当用户扫描后 window.code=201
    if 'window.code=408' in r1.text:
        print('无人扫描')
        return HttpResponse(json.dumps(ret))
    elif 'window.code=201' in r1.text:
        print('已扫描')
        ret['code'] = 201
        avatar = re.findall("window.userAvatar = '(.*)';", r1.text)[0]
        ret['data'] = avatar
        TIP = 0
        return HttpResponse(json.dumps(ret))
    elif 'window.code=200' in r1.text:
        print('手机已点击登录')
        '''
        window.code = 200;
        window.redirect_uri = "https://wx.qq.com/cgi-bin/mmwebwx-bin/webwxnewloginpage?ticket=AQ80iunrV0mQXaIyo7P08XAv@qrticket_0&uuid=wZUADWi8cg==&lang=zh_CN&scan=1567425022";
        https://wx.qq.com/cgi-bin/mmwebwx-bin/webwxnewloginpage?ticket=AZ1luB1hPTnT_E947Xf1Vit0@qrticket_0&uuid=4dgK52lXjQ==&lang=zh_CN&scan=1567426351&fun=new&version=v2
        '''
        # 保存cookie
        ALL_COOKIE_DICT.update(r1.cookies.get_dict())
        redirect_uri = re.findall('window.redirect_uri="(.*)";', r1.text)[0]
        redirect_uri = redirect_uri + '&fun=new&version=v2'
        # 获取凭证
        r2 = requests.get(
            url=redirect_uri
        )
        ALL_COOKIE_DICT.update(r2.cookies.get_dict())
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(r2.text, 'html.parser')
        for tag in soup.find('error').children:
            TICKET_DOCT[tag.name] = tag.get_text()
        ret['code'] = 200
        return HttpResponse(json.dumps(ret))


def user(request):
    '''
    个人主页
    :param request:
    :return:
    '''

    # 获取用户信息 post
    '''
    https://wx.qq.com/cgi-bin/mmwebwx-bin/webwxinit?r=180441343&lang=zh_CN%2Fcgi-bin%2Fmmwebwx-bin%2Fwebwxgeticon%3Fseq%3D470012&pass_ticket=wZUYfN3LmfPtz2mPP3HNEv1Ie2vT8GZ7bbZy%252FX57WxgQoe6zvvipnTMqofiEh0e8
    '''
    print('获取用户信息')
    get_user_info_url = 'https://wx.qq.com/cgi-bin/mmwebwx-bin/webwxinit?r=180441343&lang=zh_CN%2Fcgi-bin%2Fmmwebwx-bin%2Fwebwxgeticon%3Fseq%3D470012&pass_ticket=' + TICKET_DOCT['pass_ticket']
    get_user_info_data = {
        'BaseRequest': {
            'Sid': TICKET_DOCT['wxsid'],
            'Skey': TICKET_DOCT['skey'],
            'Uin': TICKET_DOCT['wxuin'],
            'DeviceID': 'e923129794136266'
        }
    }
    r3 = requests.post(
        url=get_user_info_url,
        json=get_user_info_data
    )
    ALL_COOKIE_DICT.update(r3.cookies.get_dict())
    # 编码
    r3.encoding = r3.apparent_encoding
    user_init_dict = json.loads(r3.text)
    # global USER_INIT_IDCT
    # USER_INIT_IDCT = user_init_dict
    USER_INIT_IDCT.update(user_init_dict)

    for k, v in user_init_dict.items():
        print(k, v)
    return render(request, 'user.html', {'user_init_dict': user_init_dict})

def contact_list(request):
    '''
    获取所有联系人.并在页面中显示
    :param request: https://wx.qq.com/cgi-bin/mmwebwx-bin/webwxgetcontact?lang=zh_CN%2Fcgi-bin%2Fmmwebwx-bin%2Fwebwxgeticon%3Fseq%3D470012&pass_ticket=r48RFrk4UUrrpDhZP524Qu9LGhSBpxwNkgySt3atNbOU22OyrB4pvEg9RZc55REV&r=1567502049735&seq=0&skey=@crypt_adc7e416_a434605bb009644cc63d5e6f2f76278f
    :return:
    '''
    ctime = str(time.time())
    url = 'https://wx.qq.com/cgi-bin/mmwebwx-bin/webwxgetcontact?pass_ticket=%s&r=%s&seq=0&skey=%s' %(TICKET_DOCT['pass_ticket'], ctime, TICKET_DOCT['skey'])
    response = requests.get(
        url=url,
        cookies=ALL_COOKIE_DICT
    )
    response.encoding = 'utf-8'
    contact_list_dict = json.loads(response.text)
    return render(request, 'contact_list.html', {'contact_list_dict': contact_list_dict})


def send_msg(request):
    '''
    发送消息
    :param request:
    :return:
    '''

    to_user = request.GET.get('toUser').rstrip()
    msg = request.GET.get('msg')
    # https://wx.qq.com/cgi-bin/mmwebwx-bin/webwxsendmsg?lang=zh_CN%2Fcgi-bin%2Fmmwebwx-bin%2Fwebwxgeticon%3Fseq%3D470012&pass_ticket=stFaYRJ6BSxoSkL55PuDnZSDL8fUY6fCjtcwfvyCQ8daBOyo8c0HPJvfd%252BHQtx7N
    url = 'https://wx.qq.com/cgi-bin/mmwebwx-bin/webwxsendmsg?lang=zh_CN&pass_ticket=' + TICKET_DOCT['pass_ticket']
    ctime = str(time.time())
    post_dict = {
        'BaseRequest': {
            'Sid': TICKET_DOCT['wxsid'],
            'Skey': TICKET_DOCT['skey'],
            'Uin': TICKET_DOCT['wxuin'],
            'DeviceID': 'e742373796383392'
        },
        'Msg': {
            'ClientMsgId': ctime,
            'Content': msg,
            'FromUserName': USER_INIT_IDCT['User']['UserName'],
            'ToUserName': to_user,
            'LocalID': ctime,
            'Type': 1
        },
        'Scene': 0
    }

    print(post_dict)
    send = requests.post(
        url=url,
        data=json.dumps(post_dict, ensure_ascii=False).encode(encoding='utf-8'),
        cookies=ALL_COOKIE_DICT
    )
    print(send.text)
    return HttpResponse('ok')