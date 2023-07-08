from scraper import *
from multiprocessing import Pool
from datetime import datetime
from json import dump


# Initializing
urls = {
	'apartments': 'https://www.nhatot.com/mua-ban-can-ho-chung-cu',
	'real_estates': 'https://www.nhatot.com/mua-ban-nha-dat',
	'lands': 'https://www.nhatot.com/mua-ban-dat',
	'transfers': 'https://www.nhatot.com/sang-nhuong-van-phong-mat-bang-kinh-doanh',
}
len_pages = 1


# Crawling one post
def crawl_post(driver, action):
	data_elements = find_elements(driver, By.CSS_SELECTOR, 'div[class="DetailView_adviewPtyItem__V_sof"]')

	# Crawling frequent data
	crawled_data = {
		'link': driver.current_url,

		'user': find_element(driver, By.CSS_SELECTOR, 'b[role="presentation"]').text,
		'phone': None,

		'title': find_element(data_elements[0], By.CSS_SELECTOR, 'h1').text,
		'price': find_element(data_elements[0], By.CSS_SELECTOR, 'span[itemprop="price"]').text.split()[0:2],
		'area': find_element(data_elements[0], By.CSS_SELECTOR, 'span[itemprop="price"]').text.split()[3:5],
		'address': find_element(data_elements[0], By.CSS_SELECTOR, 'span[class="fz13"]').text.split('\n')[0],
		'project': None,

		'images': [],
		'features': None,
		'description': None,
		'current_time': datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
		'ago_time': find_element(data_elements[0], By.CSS_SELECTOR,
			'div[itemprop="price"]>span>div>div:nth-of-type(2)'
		).text,
	}

	# Crawling images
	images_element = find_element(driver, By.CSS_SELECTOR, 'div[class="slick-list"]')
	crawled_data['images'] = [
		get_image_link(
			image_element,
			f'{crawled_data["link"].strip("https://www.nhatot.com/").split(".htm")[0].replace("/", "")}',
			i
		)
		for i, image_element in enumerate(find_elements(images_element, By.CSS_SELECTOR, 'img'))
	]
	crawled_data['images'] = [image for image in crawled_data['images'] if image]

	# Clicking show more buttons
	for button in find_elements_existed(driver, By.CSS_SELECTOR, 'button[class="styles_button__SVZnw"]'):
		click(action, button)

	# Crawling phone number
	while crawled_data['phone'] is None:
		click_element(driver, action, By.CSS_SELECTOR, 'div[class~="LeadButton_showPhoneButton__1BIwH"]')

		try:
			crawled_data['phone'] = find_element_existed(driver, By.CSS_SELECTOR,
				'div[class~="LeadButton_showPhoneButton__1BIwH"]'
			).text
		except: pass

	# Crawling occasional data
	try:
		crawled_data['project'] = find_element_existed(data_elements[0], By.CSS_SELECTOR,
			'span[itemprop="new_project"]'
		).text
	except: pass

	try:
		crawled_data['description'] = find_element_existed(data_elements[2], By.CSS_SELECTOR,
			'p[class="styles_adBody__vGW74"][itemprop="description"]'
		).text,
	except: pass

	# Crawling features
	features = find_elements(data_elements[1], By.CSS_SELECTOR, 'div[class="AdParam_adParamContainerVeh__Vz4Zt"]>div')
	crawled_data['features'] = {
		feature.text.split(':')[0].strip(): feature.text.split(':')[1].strip() for feature in features
	}

	# Checking if crawl was successful
	if len([v for v in crawled_data.values() if v is None]) > 1: raise Exception('crawl_failed')

	return crawled_data


# Crawling everything
def crawl(id, url):
	driver, action = initialize(url)

	for page in range(1, 1 + len_pages):
		posts_elements_path = 'div[class="ListAds_ListAds__rEu_9 col-xs-12 no-padding"]'
		len_posts_elements = len(find_elements(driver, By.CSS_SELECTOR, posts_elements_path))

		for i in range(1, 1 + len_posts_elements):
			lists_elements_path = f'{posts_elements_path}:nth-of-type({i})>ul'
			len_lists_elements = len(find_elements(driver, By.CSS_SELECTOR, lists_elements_path))

			for j in range(1, 1 + len_lists_elements):
				post_elements_path = f'{posts_elements_path}:nth-of-type({i})>ul:nth-of-type({j})>div[role="button"]'

				find_element(driver, By.CSS_SELECTOR, f'{posts_elements_path}:nth-of-type({i})>ul:nth-of-type({j})')
				if find_element_existed(driver, By.CSS_SELECTOR, post_elements_path) is None: continue

				len_post_elements = len(find_elements(driver, By.CSS_SELECTOR, post_elements_path))

				for k in range(1, 1 + len_post_elements):
					post_element_path = f'\
						//*[@id="__next"]/div/div[3]/div/div[3]/main/div/div[3]/div/\
						div[{i}]/ul[{j}]/div[@role="button"][{k}]/li/a\
					'

					# Crawling post
					crawled_data = None

					while crawled_data is None:
						click_element(driver, action, By.XPATH, post_element_path)

						print(id, page, i, j, k, find_element(driver, By.XPATH, post_element_path).text.split('\n')[1])

						try: crawled_data = crawl_post(driver, action)
						except Exception as e: print(e)

					# Going back
					driver.back()

					# Writing to file
					with open(f'data/chotot_{id}.json', 'a', encoding='utf-8') as file:
						dump(crawled_data, file, ensure_ascii=0, indent=4, separators=(',', ': '))
						file.write(',\n')

		# Going to next page
		driver.quit()
		driver, action = initialize(f'{url}?page={page}')


# Multiprocessing
def main():
	with Pool() as pool:
		pool.starmap(crawl, list(urls.items()))


if __name__ == '__main__': main()