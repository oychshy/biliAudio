import os
import json
import time
import requests
import HTTPRequests
import moviepy.editor as mp

# 浏览器cookies中找到SESSDATA的值。不填写也可以
setjar0 = {'SESSDATA':''}
# 下载路径
path = '/Users/js/Downloads/adio/'


# 查询用户投稿视频 pn:页码 ps:项数
def CheckUpload(uid,page):
    url = 'http://api.bilibili.com/x/space/arc/search?pn='+str(page)+'&ps=50&mid=' + str(uid)
    ret = HTTPRequests.HTTPGet(url)
    retDic = json.loads(ret)
    if retDic['code'] != 0:
        return False
    else:
        videoList = retDic['data']['list']['vlist']
        count = retDic['data']['page']['count']
        return True, videoList, count

def CheckChannelInfo(uid):
    url = 'http://api.bilibili.com/x/space/channel/list?mid='+str(uid)
    ret = HTTPRequests.HTTPGet(url)
    try:
        return json.loads(ret)
    except:
        return None

def CheckChannelDetail(uid,cid,number):
    count = int(number / 100) + 1 if number % 100 > 0 else 0
    for i in range(0,count):
        url = 'http://api.bilibili.com/x/space/channel/video?mid='+str(uid)+'&cid='+str(cid)+'&pn='+str(i+1)
        ret = HTTPRequests.HTTPGet(url)
        try:
            retDic = json.loads(ret)
            if retDic['code'] != 0:
                return None
            list = retDic['data']['list']['archives']
            return list
        except:
            return None

"""fnval:
    默认为0
    0 2：flv方式（可能会有分段）
    1：低清mp4方式（仅240P与360P，且限速65K/s）
    16 80：dash方式（音视频分流，支持H.265）
    
    dash->audio->id:
    30216	64K
    30232	132K
    30280	192K
"""
def CheckPlayerDetails(cid,bvid,isAudio):
    fnval = '80' if isAudio else '0'
    url = 'http://api.bilibili.com/x/player/playurl?cid=' + str(cid) + '&bvid=' + bvid +\
          '&qn=32&fnval='+ fnval +'&fnver=0&fourk=1'
    ret = HTTPRequests.HTTPGet(url, setjar0)
    try:
        retDic = json.loads(ret)
        if retDic['code'] != 0:
            return False
        audioInfos = retDic['data']['dash']['audio']
        # 默认最高192k,没有最高默认首位的音质
        for audioInfo in audioInfos:
            if audioInfo['id'] == 30280:
                print('192k')
                return True, audioInfo['baseUrl'], audioInfo['base_url']
        return True, audioInfos[0]['baseUrl'], audioInfos[0]['base_url']
    except:
        return False

def DownloadFlv(url,title):
    header = {
        'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/75.0.3770.142 Safari/537.36',
        'referer': 'https://www.bilibili.com'
    }
    ret = requests.get(url=url, verify=False, headers=header, timeout=20)
    if ret:
        dir = path + title + '.flv'
        fp = open(dir, 'wb')
        fp.write(ret.content)
        fp.close()
        print(title,'.flv dowload end')
        return True
    else:
        print(title,'.flv dowload false')
        return False

def DownloadPic(url,title):
    header = {
        'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/75.0.3770.142 Safari/537.36',
        'referer': 'https://www.bilibili.com'
    }
    ret = requests.get(url=url, verify=False, headers=header, timeout=20)
    if ret:
        dir = path + title + '.jpg'
        fp = open(dir, 'wb')
        fp.write(ret.content)
        fp.close()
        print(title, '.jpg dowload end')
        return True
    else:
        print(title, '.jpg dowload False')
        return False


def DownloadMusic(bvid,cid,title,picUrl):
    ret, downloadUrl, downloadUrl_backup = CheckPlayerDetails(cid, bvid, True)
    if ret:
        ret = DownloadFlv(downloadUrl, title)
        if ret:
            # 转成mp3
            clip = mp.AudioFileClip(path + title + '.flv')  # 替换实际路径
            clip.write_audiofile(path + title + '.mp3')  # 替换实际路径
            # 封面
            DownloadPic(picUrl, title)
        try:
            os.remove(path + title + '.flv')
        except:
            print(title, ' remove false')

        if ret:
            return True
        else:
            return False
    else:
        print('get download link error')
        return False


def GetVideoInfoWithBvid(bvid):
    url = 'http://api.bilibili.com/x/web-interface/view?bvid=' + bvid
    ret = HTTPRequests.HTTPGet(url)
    if ret:
        retDic = json.loads(ret)
        data = retDic['data']
        cid = data['cid']
        pic = data['pic']
        title = data['title']
        return True, cid,pic,title
    else:
        return False


def FindMusicFromUpperChannel(uid):
    # 频道列表
    ret = CheckChannelInfo(uid)
    if ret['code'] != 0:
        print(ret['message'])
        return

    getData = ret['data']
    print('找到' + str(getData['count']) + '个频道：')

    if getData['count'] == 0:
        return

    for i in range(0, len(getData['list'])):
        info = getData['list'][i]
        print(str(i + 1) + ': ' + info['name'])

    # 频道内容
    channelNum = int(input())
    if (channelNum - 1) < len(getData['list']):
        cid = getData['list'][channelNum - 1]['cid']
        number = int(getData['list'][channelNum - 1]['count'])
        detailList = CheckChannelDetail(uid, cid, number)
        if not detailList:
            print('get channel detail error')
            return

        for i in range(0, len(detailList)):
            detail = detailList[i]
            print(str(i + 1), ': ', detail['title'])

        musicNum = int(input())
        cid = detailList[musicNum - 1]['cid']
        bvid = detailList[musicNum - 1]['bvid']
        title = detailList[musicNum - 1]['title']
        picUrl = detailList[musicNum - 1]['pic']

        ret, downloadUrl, downloadUrl_backup = CheckPlayerDetails(cid, bvid, True)
        if ret:
            ret = DownloadFlv(downloadUrl, title)
            if ret:
                # 转成mp3
                clip = mp.AudioFileClip(path + title + '.flv')  # 替换实际路径
                clip.write_audiofile(path + title + '.mp3')  # 替换实际路径
                # 封面
                DownloadPic(picUrl, title)
            try:
                os.remove(path + title + '.flv')
            except:
                print(title, ' remove false')
        else:
            print('get download link error')
            return 
    else:
        print('error')
        return

def FindMusicFromUpperAllVideo(uid):
    errorcount = 3
    allVideo = []
    page = 1
    while True:
        ret, vlist, count = CheckUpload(uid,page)
        if not ret:
            if errorcount > 0:
                errorcount -= 1
                continue
            else:
                break
        else:
            errorcount = 3

        allVideo.extend(vlist)
        page += 1
        if len(allVideo) >= count:
            break
        time.sleep(1)

    for info in allVideo:
        bvid = info['bvid']
        ret, cid, pic, title = GetVideoInfoWithBvid(bvid)
        if not ret:
            print(bvid + 'info error')
            continue
        else:
            # print(cid)
            DownloadMusic(bvid, cid, title, pic)


def FindMusicFromBvid(bvid):
    ret, cid, pic, title = GetVideoInfoWithBvid(bvid)
    if not ret:
        print('video info error,retry')
        return
    else:
        DownloadMusic(bvid,cid,title,pic)

if __name__ == '__main__':
    uid = 10698584

    # up频道的投稿
    # FindMusicFromUpperChannel(uid)
    # up全部的投稿
    FindMusicFromUpperAllVideo(uid)
    # bvid
    # FindMusicFromBvid('BV1cf4y177w4')









