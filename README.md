# baike_wiki
# 两个py文件分别处理baidu和wiki的网页信息
首先创建一个文件夹data 

# html_url_baidu.py
在第215行 name_list中添加要搜索的name
第153 exc_list 为“黑名单”，将不需要的字符段加入该列表，例如想屏蔽 “请编辑这个对象”，那么加入其中的连续字符例如“这个对象”即可


# html_url_wiki.py
在第202行 name_list中添加要搜索的name
第1139 exc_list 为“黑名单”，将不需要的字符段加入该列表

