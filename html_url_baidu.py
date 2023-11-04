from datetime import datetime
from bs4 import BeautifulSoup
import requests
from urllib.parse import unquote
import json
from zhconv import convert
import csv
from findDescription import main
import re

def remove_citations(text):
    # 使用正则表达式匹配引用符号并替换为空字符串
    # cleaned_text = re.sub(r'\[\d+\]', '', text)
    cleaned_text = re.sub(r'\[\d+(?:-\d+)?\]', '', str(text))
    cleaned_text = re.sub(r'\s+', '', cleaned_text).strip()
    return cleaned_text

def extract_baidu_baike_content(url, target_class="lemmaSummary_qwEmi J-summary"):
    try:
        # 发送 GET 请求
        response = requests.get(url)
        # 检查响应状态码
        response.raise_for_status()
        # 使用 BeautifulSoup 解析网页内容
        soup = BeautifulSoup(response.text, 'html.parser')
        # 根据类别选择器提取目标元素
        target_element = soup.find('div', class_=target_class)

        if target_element:
            content = target_element.get_text().strip()

            return content
        else:
            return None
    except requests.exceptions.RequestException as e:
        pass
    except Exception as e:
        pass

"""读取html文件"""
def extract_links_and_names_from_html(html_file_path):
    with open(html_file_path, 'r', encoding='utf-8') as file:
        html_content = file.read()

    soup = BeautifulSoup(html_content, 'html.parser')

    # 初始化一个空列表，用于存储 (url, name) 元组
    url_name_pairs = []

    # 找到所有带有href属性的<a>标签
    for a_tag in soup.find_all('a', href=True):
        url = a_tag['href']
        name = a_tag.get_text(strip=True)  # 获取标签内的文本内容，去除空白字符
        url_name_pairs.append((url, name))

    return url_name_pairs

"""判断是否是维基百科并补全链接，目前观察到的维基百科的url分两种，一种是 /wiki/名词代码，一种是/wiki/Category:名词代码"""
def is_wikipedia_url(url):
    wikipedia_domains = ["/item/",]  # 可添加其他语言维基百科的关键字
    if url is None:
        return False
    # 检查URL是否以维基百科的域名开头
    for domain in wikipedia_domains:
        if domain not in url:
            return False
        else:
            return True
    return False

"""繁体字转换"""
def traditional_to_simplified(traditional_text): # 繁体转简体
    simplified_text = convert(traditional_text, 'zh-hans')
    return simplified_text

"""URL编解码"""
def decode_wiki_link(encode_link):
    link = encode_link.split("/item/")[-1]
    new_link = encode_link

    if '?' in link:
        new_link = link.split('?')[0]
        if encode_link[:8] != "https://":  # 如果url不完整
            encode_link = "https://baike.baidu.com/item/" + new_link  # 补全url
        else:
            encode_link = encode_link.split('?')[0]

    if "/" in link:
        link = link.split("/")[0]
    elif "?" in link:
        link = link.split("?")[0]
    decoded_link = unquote(link)
    simplified_decoded_link = traditional_to_simplified(decoded_link)
    final_link = encode_link.replace(link,simplified_decoded_link)

    return simplified_decoded_link,final_link


"url去重"
def remove_duplicate_dicts(dict_list):
    seen_urls = set()
    unique_dicts = []

    for d in dict_list:
        # 检查字典中的URL是否已经存在
        if d['url'] not in seen_urls:
            seen_urls.add(d['url'])
            unique_dicts.append(d)
    return unique_dicts


"""存放csv"""
def write_csv_file(name,head,relationship,tail):
    # 打开文件，使用 'w' 模式表示写入
    name = name + ".csv"
    with open(name, 'w', newline='', encoding='utf-8') as csvfile:
        # 创建 CSV 写入对象
        csv_writer = csv.writer(csvfile)

        # 写入标题行
        csv_writer.writerow(['head', 'relationship', 'tail'])

        # 遍历列表，并将数据写入 CSV 文件
        for item in tail:
            csv_writer.writerow([head, relationship, item])

# if __name__ == "__main__":
    # 直接输入URlhttps://baike.baidu.com/item/%E5%9B%BE%E8%AE%BA/1433806
def mains(index,name):
    html = f"https://baike.baidu.com/item/{name}" # HTML页面的URL

    response = requests.get(html)
    html_content = response.text
    # 创建BeautifulSoup对象
    soup = BeautifulSoup(html_content, 'html.parser')

    # 提取包含URL的实体
    entities = soup.find_all('a')  # 假设URL包含在<a>标签中


    # 最终输出的列表
    nodes = [] # json
    relationships = [] # csv
    # 把主页信息存为第一个
    main_page = {}
    main_page["name"],main_page["url"]= decode_wiki_link(html)
    descr = extract_baidu_baike_content(html)
    main_page["des"] = descr
    main_page["des"] = remove_citations(main_page["des"])
   # main_page["timestamp"] = datetime.now().strftime("%Y%m%d")
    nodes.append(main_page)
    # 黑名单
    exc_list=['秒懂本尊答','秒懂大师说','秒懂看瓦特','秒懂五千年','秒懂全视界','百科热词团队','百度百科：多义词','百度','百度热词团队','百度百科：本人词条编辑服务','义项','本人编辑','热词团',"多义词",'义项','锁定']
    del_list = []
    for entity in entities:
        result_dict = {}
        entity_name = entity.text
        entity_url = entity.get('href')
        print('实体名称:', entity_name)
        print('对应URL:', entity_url)

        if is_wikipedia_url(entity_url) is False:  # 判断是否是维基百科
            continue
        else:  # 如果是一个wiki百科
            # print(entity_url)
            result_dict["name"] = traditional_to_simplified(entity_name)  # 存放简体名称
            # print(result_dict["name"])

            # if result_dict["name"] in exc_list:
            #
            #     continue
            state = False
            for name in exc_list:
                if name in result_dict["name"]:
                    del_list.append(result_dict["name"])
                    state=True
                    break
            if state is True:
                continue
            if result_dict["name"] == "":
                continue
            _,result_dict["url"] = decode_wiki_link(entity_url) # 存放url
            # print(result_dict["url"])
            # result_dict["timestamp"] = datetime.now().strftime("%Y%m%d") #存放时间戳
            if main_page["name"].split('/item/')[-1].split('/')[0] != result_dict["url"].split('/item/')[-1].split('/')[0] :
                last_slash_index = result_dict["url"].rfind('/') # 去掉最后的编码
                url = result_dict["url"][:last_slash_index] # 这里先使用url暂代，不对result_dict["url"]直接修改，不然下面提取描述的时候，遇到多义词会因为没有编码而出现错误
                relationships.append(url)

            result_dict["des"] = extract_baidu_baike_content(result_dict["url"])
            search = 0
            while result_dict["des"] is None and search<= 10:
                result_dict["des"] = extract_baidu_baike_content(result_dict["url"])
                search += 1
                # print(f"执行第{search}次搜索")
            last = result_dict["url"].rfind('/')
            result_dict["url"] = result_dict["url"][:last]
            result_dict["des"] = remove_citations(result_dict["des"])
            nodes.append(result_dict)

    nodes = remove_duplicate_dicts(nodes)
    relationships = [x for i, x in enumerate(relationships) if x not in relationships[:i]] # 列表url去重
    # json_name = main_page["name"]+"baidu_nodes.json"
    # csv_name = main_page["name"]
    # print(f"该主页为:{csv_name}")

    with open(f"./data/Baidubaike/nodes/{index+1}", "w", encoding="utf-8") as json_file: # 保存json
        json.dump(nodes, json_file, ensure_ascii=False, indent=2)

    write_csv_file(f"./data/Baidubaike/relationships/{index+1}",main_page["url"],"Contain",relationships) #保存为CSV
    # print("本次删除的无效条目有：")
    # for i in del_list:
    #     print(i)

name_list = ['吴信东',
'倪岳峰',
'杨善林',
'周志华',
'合肥工业大学',
'南京大学',
'数据挖掘',
'机器学习',
'郑磊/59821',
'图论/1433806?fromModule=disambiguation',
'人工智能',
'中国工程院院士']

for index,name in enumerate(name_list):
    print(name)
    mains(index,name)