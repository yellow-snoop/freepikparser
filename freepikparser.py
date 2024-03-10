from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import StaleElementReferenceException, ElementClickInterceptedException, NoSuchElementException
from selenium.webdriver.chrome.options import Options
import time
import requests
import IPython
import re
from functools import wraps


# Декоратор попыток

def retry(attempts = 3, delay=1, exceptions=(Exception,)):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            nonlocal attempts
            last_exception = None
            for attempt in range(attempts):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    print(f"Ошибка: {str(e)}. Повторная попытка {attempt+1}")
                    last_exception = e
                    time.sleep(delay)
            raise last_exception
        return wrapper
    return decorator


# Основной объект Парсера

class FreepikParser:

    def __init__(self):

        self.browser_driver = None
        self.browser_options = None
        self.prompt = None
        self.main_page_url = None
        self.page_info_block_selector = None
        self.page_info_text = None
        self.current_page = None
        self.total_pages = None

        self.images_block_selector = None
        self.images = None
        self.current_image = None
        self.next_image_selector = None
        self.next_image = None
        self.images_preview_selector = None
        self.image_preview_to_be_clickable = None
        self.image_preview = None
        self.image_url = None

        self.response = None
        self.next_page_selector = None
        self.next_page_selector_to_be_clickable = None
        self.next_page = None
        self.main_page_url = 'https://ru.freepik.com/search?file_type=svg&format=search&last_filter=file_type&last_value=svg&query={}&selection=1&style=flat&type=vector'

    def scroll_up_n_down(self):        
        self.browser_driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        self.browser_driver.execute_script("window.scrollTo(0, 0);")

    def close_chrome(self):
        try:
            self.browser_driver.close()
        except:
            pass

    def open_chrome(self): 

        self.close_chrome()

        self.browser_options = Options()
        self.browser_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        self.browser_options.add_argument("--auto-open-devtools-for-tabs")

        self.browser_driver = webdriver.Chrome(options=self.browser_options)

    @retry()
    def open_freepik_page(self, url:str = None, prompt:str = 'finance'):

        self.prompt = prompt    
        if url:
            self.browser_driver.get(url)
        else:
            self.browser_driver.get(self.main_page_url.format(prompt))


    @retry()
    def find_page_num(self):

        self.page_info_block_selector = '/html/body/div[1]/div[4]/div[3]/div/div[5]/div[2]'
        self.page_info_text = self.browser_driver.find_element(By.XPATH, self.page_info_block_selector).text
        pattern = '^\w+\s(\d+)\s\w{2}\s(\d+)$'
        self.current_page, self.total_pages = [int(e) for e in re.search(pattern, self.page_info_text).groups()]
        
    @retry()
    def find_images_on_page(self):
        
        self.images_block_selector = "div[class='_1286nb12il _1286nb12jv _1286nb128l _1286nb129v _1286nb11a9 _1286nb11q3 _1286nb1m _1286nb15'] a figcaption"
        self.images = self.browser_driver.find_elements(By.CSS_SELECTOR, self.images_block_selector)

    @retry()
    def go_to_image(self, index:int):
        dependent_attributes = self.current_page, self.total_pages, self.page_info_block_selector, self.page_info_text
        if any(attr == None for attr in dependent_attributes):
            self.find_page_num()
        try:
            self.current_image = self.images[index]
            self.current_image.click()
        except:
            self.find_images_on_page()
            self.go_to_first_image()

    @retry()
    def close_current_image(self):
        self.close_image_button_selector = 'div[data-state="open"] div[role="dialog"] button'
        self.close_image_button_to_be_clickable = EC.element_to_be_clickable((By.CSS_SELECTOR, self.close_image_button_selector))
        self.close_image_button = WebDriverWait(self.browser_driver, 10).until(self.close_image_button_to_be_clickable)
        self.close_image_button.click()  

    @retry()
    def go_to_next_image(self):

        try: 
            self.next_image_selector = 'button[data-cy="next-video"]'
            self.next_image = self.browser_driver.find_element(By.CSS_SELECTOR, self.next_image_selector)
            self.next_image.click()
        except NoSuchElementException:
            self.close_current_image()
            self.current_image.click()
            self.go_to_next_image()
            
    @retry()
    def find_image_preview_url(self):

        self.images_preview_selector = "div[style='grid-area: preview;'] div div img"
        self.image_preview_to_be_clickable = EC.element_to_be_clickable((By.CSS_SELECTOR, self.images_preview_selector))
        self.image_preview = WebDriverWait(self.browser_driver, 10).until(self.image_preview_to_be_clickable)
        self.image_url = self.image_preview.get_attribute('src')

    @retry()
    def download_image_by_url(self, path:str):
        try:
            self.response = requests.get(self.image_url)
            if self.response.status_code == 200:
                with open(path, 'wb') as file:
                    file.write(self.response.content)
            else:
                print(f'Страница {self.current_page}. Картинка не была скачана. Ответ: {self.response}')
        except AttributeError:
            self.find_image_preview_url()
            self.download_image_by_url(path)

    @retry()
    def go_to_next_page(self):
        self.next_page_selector = 'a[title="Далее Страница"]', 'a[title="Далее Страница"] span', 'a[title="Далее Страница"] span svg', 'a[title="Далее Страница"] svg path'
        for selector in self.next_page_selector:
            try:
                self.next_page_selector_to_be_clickable = EC.element_to_be_clickable((By.CSS_SELECTOR, selector))
                self.next_page = WebDriverWait(self.browser_driver, 10).until(self.next_page_selector_to_be_clickable)
                self.next_page.click()
                break
            except:
                pass


