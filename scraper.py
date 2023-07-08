# imports
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from boto3 import resource
from requests import get
from os import remove
from datetime import datetime


# options
options: Options = Options()
options.add_argument('\
	user-agent=Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko)\
	Chrome/60.0.3112.50 Safari/537.36\
')
options.add_argument('--headless')
options.add_argument('--window-size=1920,1080')
options.add_argument('--no-sandbox')
options.add_argument('--deny-permission-prompts')
options.add_argument('--incognito')
options.add_argument('--single-process')
options.add_argument('--allow-running-insecure-content')
options.add_argument('--disable-dev-shm-usage')
options.add_argument('--disable-javascript')
options.add_argument('--disable-gpu')
options.add_argument("--disable-3d-apis")
options.add_argument('--ignore-certificate-errors')
options.add_experimental_option('excludeSwitches', ['enable-automation'])
options.add_experimental_option('useAutomationExtension', 0)

# service
service: Service = Service(ChromeDriverManager().install())

# others
timeout: int = 10
s3_bucket_name: str = 'htdf-vf'
s3_bucket_region: str = 'ap-southeast-1'
s3 = resource('s3')
s3_bucket = s3.Bucket(s3_bucket_name)


# utils
def initialize(url: str) -> tuple:
	driver: webdriver.Chrome = webdriver.Chrome(service=service, options=options)
	driver.get(url)
	action: ActionChains = ActionChains(driver)

	action.click().perform()

	return (driver, action)


def find_element(driver: webdriver.Chrome, by: By, selector: str) -> WebElement:
	return WebDriverWait(driver, timeout).until(EC.presence_of_element_located((by, selector)))


def find_element_existed(driver: webdriver.Chrome, by: By, selector: str) -> WebElement:
	try:
		return driver.find_element(by, selector)
	except:
		return None


def find_elements(driver: webdriver.Chrome, by: By, selector: str) -> list:
	WebDriverWait(driver, timeout).until(EC.presence_of_all_elements_located((by, selector)))

	return driver.find_elements(by, selector)


def find_elements_existed(driver: webdriver.Chrome, by: By, selector: str) -> list:
	try:
		return driver.find_elements(by, selector)
	except:
		return []


def click(action: ActionChains, element: WebElement) -> None:
	try:
		element.click()
	except:
		action.move_to_element(element).click().perform()


def click_element(driver: webdriver.Chrome, action: ActionChains, by: By, selector: str) -> None:
	try:
		click(action, WebDriverWait(driver, timeout).until(EC.element_to_be_clickable((by, selector))))
	except:
		click(action, WebDriverWait(driver, timeout).until(EC.element_to_be_clickable((by, selector))))


def click_element_existed(driver: webdriver.Chrome, action: ActionChains, by: By, selector: str) -> None:
	try:
		click(action, driver.find_element(by, selector))
	except:
		pass


def get_image_link(image_element: WebElement, image_name: str, i: int) -> str:
	image_src: str = image_element.get_attribute('src')
	image_type: str = image_src.split(".")[-1]

	if image_type == 'jpg' or image_type == 'png':
		image_dir: str = f'data/{image_name}{i}.{image_type}'
		image_url: str = f'chotot/{datetime.now().strftime("%Y/%m/%d")}/{image_name}/{image_name}{i}.{image_type}'

		with open(image_dir, 'wb') as image:
			image.write(get(image_src).content)

		s3_bucket.upload_file(
			image_dir, image_url, ExtraArgs={'ContentType': 'image/png' if image_type == 'png' else 'image/jpeg'}
		)

		remove(image_dir)

		return image_url

	return None