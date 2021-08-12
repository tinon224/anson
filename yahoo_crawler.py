import requests 
from bs4 import BeautifulSoup as bs
import json
import re
import time
import pandas as pd

'''
windows10
-*- coding:utf-8 -*-
作者：Anson
创建：2021-08-09
更新：2019-08-12
用意：yahoo_shop抓取找尋關鍵字之對應商品資料
限制：無法抓取限制級商品(內網無法進行登入)
'''

class yahoo_shop_crawl:
	def __init__(self):                                                        
		pass
		


	def get_html(self,filter_params = &,item, order_params = None, is_url = False, page = 1):                 #requests.get()
		headers = {'headers,cookies'}
		if is_url:
			html = requests.get(item,headers = headers)	                         #get all goods detail info, item should be a URL.
		else:
			html = requests.get('https://tw.buy.yahoo.com/search/product?{}p={}&pg={}&{}'.format(filter_params,item,page,order_params))     # get the search page info, item is the search keyword, page is number of the page

		if html.status_code != requests.codes.ok:
			print(f'requests_error：{item}')
		try:
			data = html.text
		except Exception as e:
			print(e)
			return None
		return data



	def html_soup(self,html):               #soup
		self.html = html                    #HTML.text
		soup = bs(html,"html.parser")      
		 #some web need to encode copy this code >>> soup.encoding = 'UTF-8'
		return soup

	def get_max_pages(self,soup):
		self.soup = soup
		pages = list(self.soup.find('div',class_="Pagination__numberContainer___2oWVw"))    #page_button
		max_pages = (pages[len(pages)-1].text)                                              #the last button in current page
		if int(max_pages) > 5:                                                     #to limit getting top 5 pages info only  
			return 5
		else:
			return max_pages

	def get_item_url(self,soup):

		self.soup = soup
		contents = self.soup.find('div',id="isoredux-data")                       #product data >>> div id="isoredux-data" data-state="
		contents_str = str(contents)
		product_id_list = []
		product_url_list = []

		if "&quot;" in contents_str[0:50] :	                                     #IDK why sometime will had HTML code on soup but sometime didn't
			pattern_id = re.compile(r'ec_productid&quot;:&quot;(?:[\w+\d*])+')   #get product id
			len_drop_word = 25
		else:
			pattern_id = re.compile(r'"ec_productid":"(?:[0-9])+')
			len_drop_word = 16


		product_ids = re.findall(pattern_id, contents_str)
			


		for product_id in product_ids:
			product_id = product_id[len_drop_word:]                              
			product_id_list.append(product_id)


		return product_id_list
				

	def get_gd_info(self,id_,url):
		self.url = url                                                      
		html = self.get_html(self.url,is_url = True)                             #sending URL to function_get_html
		soup = self.html_soup(html)                                              #soup
		item = str(soup.find_all('script')[3])                                   #product detail info (json)>>>>> </div><script>window.__APOLLO_STATE__=..  (could be better, but I am tired)
		info = str(item[32:-53])
		json_data = json.loads(info)                                             #to type(dict)
		
		json_detail_info = json_data['Shopping_Product:{}'.format(id_)]          
		specifics = json_detail_info['detailDescription']['specifics({"filters":["FILTER_SHOPPING_ITEMDETAIL"]})']
		specifics_rep = ""
		if len(specifics) < 10 :                                               # if len(specifics) < 10 mean product had no specification info 
			specifics_dict ={}
		else:
			for word in specifics:
				if word == '"':
					continue
				else:
					specifics_rep+=word

			if specifics[0:4] == "<ul>":                                       #data isn't inside the table

				specifics_rep = re.sub('<ul>','{"',specifics_rep)
				specifics_rep = re.sub('</ul>',"",specifics_rep)
				specifics_rep = re.sub('<li>',"",specifics_rep)
				specifics_rep = re.sub('</li>','","',specifics_rep)
				specifics_rep = re.sub('：','":"',specifics_rep)
				specifics_rep = specifics_rep[:-2]

		
			else:	                                                            #data in the table
				specifics_rep = re.sub("<table>",'{"',specifics_rep) 
				specifics_rep = re.sub("<tr>",'',specifics_rep)
				specifics_rep = re.sub("</tr>",'',specifics_rep)
				specifics_rep = re.sub("<th>",'',specifics_rep)
				specifics_rep = re.sub("<td>",'',specifics_rep)
				specifics_rep = re.sub("</th>",'":"',specifics_rep)
				specifics_rep = re.sub("</td>",'","',specifics_rep)
				specifics_rep = re.sub("</table>",'',specifics_rep)
				specifics_rep = specifics_rep[:-2]
		
			specifics_rep += '}'			
			specifics_dict = json.loads(specifics_rep)                         # to dict


		price = (json_detail_info['currentPrice'])
		brand = json_detail_info['brand']
		product_name = json_detail_info['title({"filters":["FILTER_REVERT_YIV"]})']
		desc = json_detail_info['description']
		return product_name,brand,price,desc,specifics_dict

	def set_save_path(self,path):
		self.save_path = path+"/"
		

	def get_save_path(self):
		try:
			return self.save_path
		except:
			print('non_save_path_setted')


	def dict_to_excel(self,dictionary,file_name):                          # DataFrame to Excel
		try:
			df = pd.DataFrame(dictionary)
			df.to_excel(self.get_save_path()+file_name+".xlsx")
			return print("Done")
		except:
			return print(dictionary)

				

	def main(self,item):                                                  # main trigger
		data = self.get_html(item)
		soup = self.html_soup(data)
		max_pages = self.get_max_pages(soup)
		product_name_list = []
		brand_list = []
		price_list = []
		desc_list = []
		url_list = []
		id_list = []
		all_specifics_dict = {}
		detail_info = {'product_id':id_list,'product_name':product_name_list,'product_url':url_list,'brand':brand_list,'price':price_list,'desc':desc_list}    #<<< data you need
		page_count = 1

		for page in range(int(max_pages)):
			items_count = 1
			data_page = self.get_html(item,page = page+1)
			soup_page = self.html_soup(data_page)
			product_id_list = self.get_item_url(soup_page)
			
			for product_id in product_id_list: 
				try:                                       				
					product_url = 'https://tw.buy.yahoo.com/gdsale/gdsale.asp?gdid={}'.format(product_id)       #URL of the product page 
					product_name,brand,price,desc,specifics_dict = (self.get_gd_info(product_id,product_url))
				except:
					print("page:{},goods:{},無法抓取。".format(page_count,items_count))
					items_count+=1
					continue
				id_list.append(product_id)
				url_list.append(product_url)
				product_name_list.append(product_name)
				brand_list.append(brand)
				price_list.append(price)
				desc_list.append(desc)
				for key in list(specifics_dict.keys()):                                              #because the specifics info is json(dict), therefore have to merge all the specifics keys in one dict
					if key in list(all_specifics_dict.keys()):                                       #if current product specification keys already in merged dict
						all_specifics_dict[key].append(specifics_dict[key])
					else:
						key_data_list= []                                                            #if current product specification keys isn't in merged dict
						for n in range(len(product_name_list)-1):
							key_data_list.append(None)                                               #add None 
						key_data_list.append(specifics_dict[key])                                    #add current product info
						all_specifics_dict[key] = key_data_list                                      #add to merged dict

				noinfo_keys =list(set(list(all_specifics_dict.keys())) ^ set(list(specifics_dict.keys())))   #the keys merged dict had but current product didn't
				for noinfo_key in noinfo_keys:
					all_specifics_dict[noinfo_key].append(None)                                          

				items_count+=1
				time.sleep(2)
				

			page_count+=1
		detail_info.update(all_specifics_dict)                                                      #final combine all_specifics_dict and detail_info
		return detail_info



yahoo_shop_crawl = yahoo_shop_crawl()
#data = yahoo_shop_crawl.get_html("水冷扇")
#soup = yahoo_shop_crawl.html_soup(data)
dict_prod_info = yahoo_shop_crawl.main("ps5主機預購")
yahoo_shop_crawl.set_save_path('your_path')
#yahoo_shop_crawl.get_save_path()
yahoo_shop_crawl.dict_to_excel(dict_prod_info,"ps5主機預購_")
