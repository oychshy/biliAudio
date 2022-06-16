import  requests
import urllib3
# import pickle
urllib3.disable_warnings()
jar = requests.cookies.RequestsCookieJar()

setHeader = {}

def get_proxy():
    return {"http": "http://127.0.0.1:8889","https": "http://127.0.0.1:8889"}

def HTTPGetData(urlpath ,encode = True):
    resp = requests.request("GET" , urlpath ,verify=False,cookies=jar)
    global setHeader
    setHeader = resp.headers
    requests.cookies.merge_cookies(jar,resp.cookies)
    return resp

def HTTPGet(urlpath ,header=None, setjar=None ,encode = True):
    if header and setjar:
        resp = requests.request("GET" , urlpath , headers = header,verify=False,cookies=setjar)
    elif header and not setjar:
        resp = requests.request("GET" , urlpath , headers = header,verify=False,cookies=jar)
    elif setjar and not header:
        resp = requests.request("GET" , urlpath , verify=False,cookies=setjar)
    else:
        resp = requests.request("GET" , urlpath , verify=False,cookies=jar)

    requests.cookies.merge_cookies(jar,resp.cookies)
    if encode:
        return resp.text.encode('utf-8')
    return resp.text

def HTTPPost(urlpath , params ,header ,encode = True):
    resp = requests.request("POST" , urlpath ,data = params ,headers = header,verify=False,cookies=jar)
    requests.cookies.merge_cookies(jar,resp.cookies)
    if encode:
        return resp.text.encode('utf-8')
    return resp.text

def HTTPPost2(urlpath , params ,header ,encode = True):
    resp = requests.request("POST" , urlpath ,data = params ,headers = header,verify=False,cookies=jar)
    requests.cookies.merge_cookies(jar,resp.cookies)
    return resp

def getCookie(key):
    cookies = requests.utils.dict_from_cookiejar(jar)
    return cookies[key]

def getCookies():
    cookies = requests.utils.dict_from_cookiejar(jar)
    return cookies

def getResponesHeader():
    return setHeader

def save_cookies(filename):
    with open(filename, 'wb') as f:
        pickle.dump(jar, f)

def load_cookies(filename):
    with open(filename, 'rb') as f:
        jar=pickle.load(f)