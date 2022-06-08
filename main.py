import time
from parsel import Selector
import re
from SeleniumGetCookies import SeleniumGetCookies
import myTool
import os


class TaoBao:
    def __init__(self, session):
        self.session = session
        
        self.list_url = 'https://beihuanjj.tmall.com/i/asynSearch.htm?mid=w-23290845082-0'
        
        self.file_name = ''

    def get_html(self, url):
        resp = self.session.get(url)
        return resp

    def get_name(self, commodity_html):
        try:
            name = re.findall(r'<meta name="keywords" content="(.*?)"', commodity_html)[0]
            return name
        except:
            return False

    def dowm_img(self, img_url, path):
        con = self.get_html(img_url).content
        with open(path, 'wb') as f:
            f.write(con)

    def get_preview_img(self, selector):
        preview_list = selector.css('#J_UlThumb li')
        for index, preview in enumerate(preview_list):
            preview_url = preview.css('img::attr(src)').get()
            preview_url = 'https:' + preview_url.replace('60x60q', '430x430q').replace('https:', '')
            path = self.file_name + '/主图/' + str(index) + '.jpg'
            self.dowm_img(preview_url, path)

    def get_spec_img(self, selector):
        spec_list = selector.css('ul.tb-img li')
        for spec in spec_list:
            spec_name = spec.css('span::text').get()
            spec_name = myTool.set_file_name(spec_name)
            try:
                spec_url = spec.css('a::attr(style)').get()
                spec_url = re.findall(r'background:url\((.*?)\)', spec_url)[0]
                spec_url = 'https:' + spec_url.replace('40x40q', '430x430q').replace('https:', '')
                path = self.file_name + '/规格/' + spec_name + '.jpg'
                self.dowm_img(spec_url, path)
            except:
                pass

    def get_big_img(self, commodity_html):
        icoss = re.findall('"descUrl":"(.*?)"', commodity_html)[0]
        big_url = 'https:' + icoss
        big_html = self.get_html(big_url).text
        big_urls = re.findall('(https://img.alicdn.com.*?)"', big_html)
        for index, big_img in enumerate(big_urls):
            path = self.file_name + '/详情/' + str(index) + '.jpg'
            self.dowm_img(big_img, path)

    def extract_url(self):
        while True:
            text = self.get_html(self.list_url).text
            if 'default render error' in text:
                print('default render error--等60秒试试吧')
                time.sleep(60)
            else:
                break
        urls = re.findall(r'//detail.tmall.com/item.htm(.*?)\\', text)
        urls = set(urls)
        for url in urls:
            while True:
                commodity_url = 'https://detail.tmall.com/item.htm' + url
                commodity_html = self.get_html(commodity_url).text
                selector = Selector(text=commodity_html)
                name = self.get_name(commodity_html)
                if not name:
                    print(commodity_html)
                    print('出现了滑块问题--等60秒试试吧')
                    time.sleep(60)
                else:
                    break
            self.file_name = myTool.set_file_folder(name)
            if not self.file_name:
                print('已爬取，跳过！')
                continue
            os.mkdir(self.file_name + '/主图')
            os.mkdir(self.file_name + '/规格')
            os.mkdir(self.file_name + '/详情')
            self.get_preview_img(selector)
            self.get_spec_img(selector)
            self.get_big_img(commodity_html)
            print(self.file_name + '---爬取完毕！')
            time.sleep(10)


if __name__ == '__main__':
    s = SeleniumGetCookies('tb9762414031', 'cht618618')
    session = s.run()
    t = TaoBao(session)
    t.extract_url()
