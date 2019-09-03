from django.shortcuts import render, HttpResponse
import requests
import time
import re
import json
# Create your views here.


CTIME = None
QCODE = None
TIP = 1
ticket_dict= {}
# 微信登录页
def login(request):
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
        redirect_uri = re.findall('window.redirect_uri="(.*)";', r1.text)[0]
        redirect_uri = redirect_uri + '&fun=new&version=v2'
        # 获取凭证
        r2 = requests.get(
            url=redirect_uri
        )
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(r2.text, 'html.parser')
        for tag in soup.find('error').children:
            ticket_dict[tag.name] = tag.get_text()
        print(ticket_dict)

        # 获取用户信息 post
        '''
        https://wx.qq.com/cgi-bin/mmwebwx-bin/webwxinit?r=235307466&lang=zh_CN&pass_ticket=Dt4BAFm5S9UocdagG23abJAi2kPEpcC79xQz8UaVQXoP5LUrQNle8zslKncWfLYm
        '''
        get_user_info_url = 'https://wx.qq.com/cgi-bin/mmwebwx-bin/webwxinit?r=235307466&lang=zh_CN&pass_ticket='+ticket_dict['pass_ticket']
        get_user_info_data = {
            'BaseRequest': {
                'Sid': ticket_dict['wxsid'],
                'Skey': ticket_dict['skey'],
                'Uin': ticket_dict['wxuin'],
                'DeviceID': 'e923129794136266'
            }
        }
        r3 = requests.post(
            url=get_user_info_url,
            json=get_user_info_data
        )
        # 编码
        r3.encoding = r3.apparent_encoding
        user_init_dict = json.loads(r3.text)
        print(user_init_dict)
        return HttpResponse('手机已点击登录')

