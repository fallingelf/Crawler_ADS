# 在ADS上检索并爬取文件
import requests
from urllib.request import urlopen, urlretrieve,Request
from bs4 import BeautifulSoup
import re, os
from urllib.error import *
import time, sys
from PyPDF2 import PdfFileReader

def check_pdf(pdf_file):
    try:
        PdfFileReader(pdf_file)
        return 1
    except :
        return 0

def double_check(pdf_file,lable_href, url_href, ads_paper):
    try:
        PdfFileReader(pdf_file)
    except :
        print('double check fails, re-download form Sci-Hub!')
        down_DOI(lable_href, url_href, ads_paper)


def report(count, blockSize, totalSize):
    percent = int(count * blockSize * 100 / totalSize)
    sys.stdout.write("\r%d%%" % percent + ' complete')
    sys.stdout.flush()

def url_decomposed(url):
    param_soup=url.replace(re.findall(re.compile('.*\?'), url)[0], '&')+'&'
    param={}
    try:
        while param_soup.index('='):
            key=param_soup[param_soup.index('&')+1:param_soup.index('=')]
            param_soup=param_soup.replace('&' + key + '=', '')
            param[key]=param_soup[0:param_soup.index('&')]
            param_soup = param_soup.replace(param_soup[0:param_soup.index('&')], '')
    except ValueError:
        return param

def mode_switch(url, filename):    #对于A&A可能需要由get变为post
    try:
        urlretrieve(url, filename, reporthook=report)
    except URLError:
        param = url_decomposed(url)
        obj=BeautifulSoup(requests.post(url, data=param).text,'html5lib')
        raw_paper_url = obj.find_all('dd')[0].find_all('a')[0]['href']
        raw_paper_url=raw_paper_url.replace(re.findall(re.compile('.*url=https%3a/'), raw_paper_url)[0],'https://')
        url =raw_paper_url.replace(re.findall(re.compile('\.pdf.*'), raw_paper_url)[0], '.pdf')
        urlretrieve(url, filename, reporthook=report)
    return

def auto_down(url, filename,lable_href,url_href, ads_paper):
    try:
        try:
            sys.stdout.write('\rFetching ' + filename + '  from  ' + url +'  ...\n')
            mode_switch(url, filename)
            #urlretrieve(url, filename, reporthook=report)
            sys.stdout.write("\rDownload complete, saved as %s" % (filename) + '\n\n')
            sys.stdout.flush()
        except ContentTooShortError:
            print('Network conditions is not good. Reloading...')
            auto_down(url, filename)
    except :# HTTPError:
        print('Try to download from Sci-Hub')
        down_DOI(lable_href,url_href, ads_paper)
        return

def get_context(url):
    bsobj = BeautifulSoup(urlopen( url), 'html5lib')
    return bsobj

def down_DOI(lable_href,url_href, ads_paper):
    print(lable_href,url_href)
    DOI = re.findall(re.compile('>(.*)</a>'),
                     str(get_context(url_href).find_all('a', {'href': re.compile('https:\/\/doi\.org\/.*')})))
    if DOI:
        param_sci = {'request': DOI[0]}
        url_list = BeautifulSoup(requests.post('http://sci-hub.tw/', data=param_sci).text, 'html5lib').find_all(
            'iframe')
        if url_list:
            url_tail = url_list[0]['src']
            if str(url_tail)[0:5] != 'http:':
                url_paper = 'http:' + url_tail
            else:
                url_paper = url_tail
            print(url_paper)
            auto_down(url_paper, path_paper + lable_href + '.pdf',lable_href,url_href, ads_paper)
            print(lable_href, DOI[0], url_paper)
            ads_paper.write(str(lable_href + ' ' + DOI[0] + ' ' + url_paper + '\n'))
        else:
            print(lable_href, DOI[0], 'SCI does not provide pdf file')
            ads_paper.write(str(lable_href + ' ' + DOI[0] + ' ' + 'SCI does not provide pdf file' + '\n'))
    else:
        print(lable_href, 'This paper does not have DOI')
        ads_paper.write(str(lable_href + '\n'))
    print('--------------------------------------------------------------------------------------------------------------')
    return None

def down_FXG(lable_single_paper,lable_href,url_single_paper,order_paper,url_href,i,ads_paper):
    if ['F'] in lable_single_paper:
        print(lable_href[order_paper[i]][0], 'F', url_single_paper[lable_single_paper.index(['F'])])
        auto_down(url_single_paper[lable_single_paper.index(['F'])],
                  path_paper + lable_href[order_paper[i]][0] + '.pdf', lable_href[order_paper[i]][0],
                  url_href[order_paper[i]], ads_paper)
        ads_paper.write(str(
            lable_href[order_paper[i]][0] + ' ' + 'F' + ' ' + url_single_paper[lable_single_paper.index(['F'])] + '\n'))
    elif ['X'] in lable_single_paper:
        print(lable_href[order_paper[i]][0], 'X', url_single_paper[lable_single_paper.index(['X'])])
        index = re.findall(re.compile('http://arxiv.org/pdf/(.*)" name="citation_pdf_url"/>'),
                           str(get_context(url_single_paper[lable_single_paper.index(['X'])])));
        print(index)
        try:
            auto_down('https://arxiv.org/pdf/' + index[0] + '.pdf', path_paper + lable_href[order_paper[i]][0] + '.pdf',
                      lable_href[order_paper[i]][0], url_href[order_paper[i]], ads_paper)
        except HTTPError:
            auto_down('https://arxiv.org/pdf/astro-ph/' + index[0] + '.pdf',
                      path_paper + lable_href[order_paper[i]][0] + '.pdf', lable_href[order_paper[i]][0],
                      url_href[order_paper[i]], ads_paper)
        ads_paper.write(str(lable_href[order_paper[i]][0] + ' ' + 'X' + ' ' + 'https://arxiv.org/pdf/astro-ph/' + index[
            0] + '.pdf' + '\n'))
    elif ['G'] in lable_single_paper:
        print(lable_href[order_paper[i]][0], 'G', url_single_paper[lable_single_paper.index(['G'])])
        url_sample = 'http://adsbit.harvard.edu/cgi-bin/nph-iarticle_query?XXX&defaultprint=YES&filetype=.pdf'
        auto_down(url_sample.replace('XXX', lable_href[order_paper[i]][0]),
                  path_paper + lable_href[order_paper[i]][0] + '.pdf', lable_href[order_paper[i]][0],
                  url_href[order_paper[i]], ads_paper)
        ads_paper.write(str(lable_href[order_paper[i]][0] + ' ' + 'G' + ' ' + url_sample.replace('XXX', lable_href[
            order_paper[i]][0]) + '\n'))
    else:
        ads_paper.write(str(lable_href[order_paper[i]][0] + ' ' + '!(FXG)' + '\n'))

def crawler_single_web(bsobj, path_paper, ads_paper):
    hrefs = bsobj.find_all('a', {'href': re.compile('http://adsabs.harvard.edu/cgi-bin/nph-data_query\?bibcode=.*')})
    order_paper = [];
    n_op = 0  # 含有文章名字的链接在hrefs中的位置
    url_href = [];
    lable_href = []
    for href in hrefs:
        lable_href.append(re.findall(re.compile('>(.*)</a>'), str(href)))
        url_href.append(href['href'])
        if len(str(lable_href[-1])) > 5:
            order_paper.append(n_op)
        n_op = n_op + 1
    order_paper.append(len(url_href)-1)
    for i in range(len(order_paper) - 1):
        lable_single_paper = lable_href[order_paper[i]:order_paper[i + 1]]
        url_single_paper = url_href[order_paper[i]:order_paper[i + 1]]
        pdf_file=path_paper + lable_href[order_paper[i]][0] + '.pdf'
        if lable_href[order_paper[i]][0] + '.pdf' not in os.listdir(path_paper):
            if ['F'] in lable_single_paper:
                print(lable_href[order_paper[i]][0], 'F', url_single_paper[lable_single_paper.index(['F'])])
                auto_down(url_single_paper[lable_single_paper.index(['F'])],path_paper + lable_href[order_paper[i]][0] + '.pdf',lable_href[order_paper[i]][0],url_href[order_paper[i]], ads_paper)
                double_check(pdf_file, lable_href[order_paper[i]][0], url_href[order_paper[i]], ads_paper)
                ads_paper.write(str(lable_href[order_paper[i]][0] + ' ' + 'F' + ' ' + url_single_paper[lable_single_paper.index(['F'])] + '\n'))
            elif ['X'] in lable_single_paper:
                print(lable_href[order_paper[i]][0], 'X', url_single_paper[lable_single_paper.index(['X'])])
                index =re.findall(re.compile('http://arxiv.org/pdf/(.*)" name="citation_pdf_url"/>'), str(get_context(url_single_paper[lable_single_paper.index(['X'])])));print(index)
                try:
                    auto_down('https://arxiv.org/pdf/'+index[0]+'.pdf',path_paper + lable_href[order_paper[i]][0] + '.pdf',lable_href[order_paper[i]][0],url_href[order_paper[i]], ads_paper)
                except HTTPError:
                    auto_down('https://arxiv.org/pdf/astro-ph/' + index[0] + '.pdf',path_paper + lable_href[order_paper[i]][0] + '.pdf',lable_href[order_paper[i]][0],url_href[order_paper[i]], ads_paper)
                ads_paper.write(str(lable_href[order_paper[i]][0] + ' ' + 'X' + ' ' + 'https://arxiv.org/pdf/astro-ph/'+index[0]+'.pdf' + '\n'))
            elif ['G'] in lable_single_paper:
                print(lable_href[order_paper[i]][0], 'G', url_single_paper[lable_single_paper.index(['G'])])
                url_sample='http://adsbit.harvard.edu/cgi-bin/nph-iarticle_query?XXX&defaultprint=YES&filetype=.pdf'
                auto_down(url_sample.replace('XXX', lable_href[order_paper[i]][0]),path_paper + lable_href[order_paper[i]][0] + '.pdf',lable_href[order_paper[i]][0],url_href[order_paper[i]], ads_paper)
                ads_paper.write(str(lable_href[order_paper[i]][0] + ' ' + 'G' + ' ' + url_sample.replace('XXX', lable_href[order_paper[i]][0]) + '\n'))
            else:
                ads_paper.write(str(lable_href[order_paper[i]][0] + ' ' + '!(FXG)' + '\n'))
        elif check_pdf(path_paper+lable_href[order_paper[i]][0] + '.pdf'):
                print(lable_href[order_paper[i]][0], '   This paper had been downloaded')
        else:
            down_FXG(lable_single_paper, lable_href, url_single_paper, order_paper, url_href, i, ads_paper)
            double_check(pdf_file, lable_href[order_paper[i]][0], url_href[order_paper[i]], ads_paper)
        print('-----------------------------------------------------------------------------------------')
    return None

params = {'db_key': '', 'sim_query': 'YES', 'ned_query': 'YES', 'adsobj_query': 'YES', 'aut_logic': 'OR',
          'obj_logic': 'OR', 'author': '', 'object': '', 'start_mon': '', 'start_year': '', 'end_mon': '',
          'end_year': '', 'ttl_logic': 'OR', 'title': '', 'txt_logic': 'OR', 'text': '', 'nr_to_return': '200',
          'start_nr': '1', 'jou_pick': 'ALL', 'ref_stems': '', 'data_and': 'ALL', 'group_and': 'ALL',
          'start_entry_day': '', 'start_entry_mon': '', 'start_entry_year': '', 'end_entry_day': '',
          'end_entry_mon': '', 'end_entry_year': '', 'min_score': '', 'sort': 'SCORE', 'data_type': 'SHORT',
          'aut_syn': 'YES', 'ttl_syn': 'YES', 'txt_syn': 'YES', 'aut_wt': '1.0', 'obj_wt': '1.0', 'ttl_wt': '0.3',
          'txt_wt': '3.0', 'aut_wgt': 'YES', 'obj_wgt': 'YES', 'ttl_wgt': 'YES', 'txt_wgt': 'YES', 'ttl_sco': 'YES',
          'txt_sco': 'YES', 'version': '1'}
#@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
params['object'] = ''                                                                                             # 指明查询的目标
params['author'] = '^Qian, S.-B.'                                                                      # 指明作者
params['start_year'] = ''                                                                                     #检索年份-开始
params['end_year'] = ''                                                                                      #检索年份-结束
path_paper = os.getcwd().replace('\\', '\\\\') + '\\' + params['author'][1:4] + '\\\\'   # 指明储存文件的目录名字
#@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
db_keys = {'PRE', 'PHY', 'AST'  }  #                                                        #指明查询的范围
if not path_paper:
    os.makedirs(path_paper)
ads_paper = open(path_paper + 'ads_paper.txt', 'w+')
for key in db_keys:
    params['db_key'] = key;print('#############################',key,'#############################')
    bsobj = BeautifulSoup(requests.post('http://adsabs.harvard.edu/cgi-bin/nph-abs_connect', data=params).text,
                          'html5lib')  # 表单提交
    crawler_single_web(bsobj, path_paper, ads_paper)  # 收集文章的url获得DOI用于爬取http://sci-hub.tw,并将结果储存
    if bsobj.find_all(text='next set of references'):  # 检查ADS检索出来的文章列表是否有下一页
        bsobj = get_context(
            re.findall(re.compile('href="(http://adsabs.harvard.edu/cgi-bin/nph-abs_connect?.*start_cnt.*)"'),
                       str(bsobj.find_all('h3')))[0])
        crawler_single_web(bsobj, path_paper, ads_paper)
print('-----------------------------------------------------------over-------------------------------------------------------------------------')
ads_paper.close()
