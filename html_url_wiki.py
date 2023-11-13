from datetime import datetime
from bs4 import BeautifulSoup
import requests
from urllib.parse import unquote
import json
from zhconv import convert
import csv
import os
import re
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
    wikipedia_domains = ["/wiki/",]  # 可添加其他语言维基百科的关键字
    if url is None:
        return False
    # 检查URL是否以维基百科的域名开头
    if url[:8] == "https://":
        if url.split("//")[-1].split("/")[0] != "zh.wikipedia.org" :
            return False

    for domain in wikipedia_domains:
        if domain not in url:
            return False
        elif url.split("/wiki/")[-1][0] == "%" or url.split("/wiki/")[-1].split(":")[0]=="Category":
            return True
    return False

"""繁体字转换"""
def traditional_to_simplified(traditional_text): # 繁体转简体
    simplified_text = convert(traditional_text, 'zh-hans')
    return simplified_text

"""URL编解码"""
def decode_wiki_link(encode_link):
    link = encode_link
    if encode_link[:8] != "https://":  # 如果url不完整
        encode_link= "https://zh.wikipedia.org" + encode_link  # 补全url

    if encode_link.split("/wiki/")[-1][0] == "%":
        link = encode_link.split("/wiki/")[-1]  # 获取链接最后的编码
    if encode_link.split("/wiki/")[-1].split(":")[0]=="Category" :
        link = encode_link.split("Category:")[-1]

    decoded_link = unquote(link)
    simplified_decoded_link = traditional_to_simplified(decoded_link)
    new_link = encode_link.replace(link,simplified_decoded_link)

    return simplified_decoded_link,new_link


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

def filter_dicts(my_list):
    filtered_list = [d for d in my_list if d.get('a') != d.get('c')]
    return filtered_list

# 示例用法

def remove_citations(text):
    # 使用正则表达式匹配引用符号并替换为空字符串
    # cleaned_text = re.sub(r'\[\d+\]', '', text)
    cleaned_text = re.sub(r'\[\d+(?:-\d+)?\]', '', str(text))
    cleaned_text = re.sub(r'\s+', '', cleaned_text).strip()
    return cleaned_text

import time
def main(name,index,exc_list,item_path,cat_path,csv_path):
    # 直接输入URl
    time.sleep(5)
    html = f"https://zh.wikipedia.org/wiki/{name}" # HTML页面的URL

    try:
        response = requests.get(html)
    except:
        for i in range(4):
            print(f"进行第{i}次尝试")
            response = requests.get(html)
            if response.status_code == 200:
                break
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
    main_page["name"] = name
    _,main_page["url"]= decode_wiki_link(html)
    main_page["des"] = ""
    nodes.append(main_page)
    for entity in entities:
        state = 0
        result_dict = {}
        entity_name = entity.text
        entity_url = entity.get('href')
        # print('实体名称:', entity_name)
        # print('对应URL:', entity_url)

        if is_wikipedia_url(entity_url) is False:  # 判断是否是维基百科
            continue
        else:  # 如果是一个wiki百科
            result_dict["name"] = traditional_to_simplified(entity_name)  # 存放简体名称
            # print(result_dict["name"])
            a = result_dict["name"]
            for i in exc_list:
                if i in result_dict["name"]:
                    state = 1
                    break
            if state ==1 :
                continue
            # if "条目" == result_dict["name"][-2:]:
            #     continue
            # if "页面" == result_dict["name"][-2:]:
            #     continue
            # if "日期" == result_dict["name"][-2:]:
            #     continue
            # if "不匹配" == result_dict["name"][-3:]:
            #     continue
            # if "(en)" == result_dict["name"][-4:]:
            #     continue

            _,result_dict["url"] = decode_wiki_link(entity_url) # 存放url
            # result_dict["timestamp"] = datetime.now().strftime("%Y%m%d") #存放时间戳
            if main_page["name"].split('/')[-1] != result_dict["url"].split('/')[-1]:
                # if result_dict["url"].split('/')[-1][:8] != "Category": # 移除了类别，后续考虑保留
                relationships.append(result_dict["url"])

            new_name = result_dict["url"].split('/')[-1]
            if "Category:" in new_name:
                new_name = new_name.split(':')[-1]
            if result_dict["name"].split('/')[-1] != new_name:
                a = result_dict["name"]
                b = new_name
                # print(f"把{a}改为{b}")
                result_dict["name"] = result_dict["url"].split('/')[-1]
            nodes.append(result_dict)


    nodes = remove_duplicate_dicts(nodes) # item_nodes
    cate_nodes = []
    item_nodes = []
    for dic in nodes:
        if "Category" in dic["url"]:
            cate_nodes.append(dic)
            # nodes.remove(dic)
        else:
            item_nodes.append(dic)


    relationships = [x for i, x in enumerate(relationships) if x not in relationships[:i]] # 列表url去重
    json_name = main_page["name"]+"wiki_nodes.json"
    csv_name = main_page["name"]

    with open(item_path+f"{index+1}.json", "w", encoding="utf-8") as json_file: # 保存json
        json.dump(item_nodes, json_file, ensure_ascii=False, indent=2)
    with open(cat_path+f"{index+1}.json", "w", encoding="utf-8") as json_file: # 保存json
        json.dump(cate_nodes, json_file, ensure_ascii=False, indent=2)

    write_csv_file(csv_path+f"{index+1}",main_page["url"],"Contain",relationships) #保存为CSV

name_list = ['吴信东',
'倪岳峰',
'杨善林',
'周志华_(计算机科学家)',
'合肥工业大学',
'南京大学',
'数据挖掘',
'机器学习',
'图论',
'人工智能',
'中国工程院院士']

exc_list = ["条目","页面","本人编辑","日期","不匹配","(en)","GND","HKCAN","ISNI","CALIS","NLC","LCCN","NTA","VIAF","AAT","BNE","J9U","BNF","LNB","NDL","NKC","SUDOC","NLA","互联网档案馆",
                "MSC分类标准","DBLP","本地和维基数据均无相关图片",'在世人物',"关系标识符","中华人民共和国省会列表"]

item_path = './data/Wikipedia/item_nodes/' # item路径
cat_path = './data/Wikipedia/Category_nodes/' # catgory路径
csv_path = './data/Wikipedia/relationships/' # 关系路径
#自动创建文件夹
if not os.path.exists(item_path):
    os.makedirs(item_path)
if not os.path.exists(cat_path):
    os.makedirs(cat_path)
if not os.path.exists(csv_path):
    os.makedirs(csv_path)


for index,name in enumerate(name_list):
    print(name)
    main(name,index,exc_list,item_path,cat_path,csv_path)