import datetime
import threading
import sqlite3
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException
from pathlib import Path

from db_function import database_dir_name, databasae_file_name


class ToolBelt:
    def __init__(self, service, webdriver, task_queue, worker_queue, sorted_hant2hans_map):
        self.database_dir_name = database_dir_name
        self.databasae_file_name = databasae_file_name
        self.shopee_all_categories_website = 'https://shopee.tw/all_categories'
        
        self.service = service
        self.webdriver = webdriver
        self.task_queue = task_queue
        self.worker_queue = worker_queue
        self.sorted_hant2hans_map = sorted_hant2hans_map

    # about the queues
    def get_a_task(self):
        now = datetime.datetime.now()
        time_string = now.strftime("%Y-%m-%d %H:%M:%S")
        print("=========================================")
        print("Get_a_task")
        print(f"Now: {time_string}")
        print(f"Tasks in queue: {self.task_queue.qsize()}")
        return self.task_queue.get()

    def publish_a_task(self, task):
        return self.task_queue.put(task)

    def count_task_number(self):
        return self.task_queue.qsize()

    def worker_check_out(self):
        return self.worker_queue.get()

    def worker_check_in(self, worker_name = 'Joey'):
        return self.worker_queue.put(worker_name)

    def count_worker_number(self):
        return self.worker_queue.qsize()

    def get_shoppe_category_link(self):
        return self.shopee_all_categories_website

    def get_sorted_hant2hans_map(self):
        return self.sorted_hant2hans_map

    def get_browser_service(self):
        return self.service

    def get_web_driver(self):
        return self.webdriver

    def get_database_connection_info(self):
        return f"{self.database_dir_name}/{self.databasae_file_name}"


class Crawler(threading.Thread):
    def __init__(self, tool_belt):
        super(Crawler, self).__init__()
        self.tool_belt = tool_belt
        self.webdriver = self.tool_belt.get_web_driver()
        self.service = self.tool_belt.get_browser_service()
        self.driver = self.webdriver.Chrome(service=self.service)

        self.sorted_hant2hans_map = self.tool_belt.get_sorted_hant2hans_map()
        self.database_connection = self.tool_belt.get_database_connection_info()

    def call_it_a_day(self):
        self.driver.quit()
        self.tool_belt.worker_check_out()

    # about crawling the website
    def get_all_category_links_from_Shopee(driver, shopee_all_categories_website):
        driver.get(shopee_all_categories_website)
        selector_all_categories = '#main > div > div:nth-child(3) > div:nth-child(2) > div > div.categories-content-card.container > div'
        top_div_of_all_category_elements = driver.find_element(by=By.CSS_SELECTOR, value=selector_all_categories)
        all_category_elements = top_div_of_all_category_elements.find_elements(By.CSS_SELECTOR, 'a')
        all_category_hrefs = list()
        for e in all_category_elements:
            all_category_hrefs.append(e.get_attribute('href'))
        return all_category_hrefs

    def get_all_sub_category_links_from_the_current_category(self):
        sub_category_hrefs = []
        # get upper sub-categories
        top_div_of_upper = self.driver.find_element(by=By.XPATH, value='//*[@id="main"]/div/div[3]/div/div[last()]/div[1]/div[1]/div/div/div[2]')
        upper_sub_category_elements = top_div_of_upper.find_elements(By.CSS_SELECTOR, 'a')
        for e in upper_sub_category_elements:
            sub_category_hrefs.append(e.get_attribute('href'))
        try:
            self.driver.find_element(by=By.XPATH, value='//*[@id="main"]/div/div[3]/div/div[last()]/div[1]/div[1]/div/div/div[2]/div')
        except NoSuchElementException:
            pass
        else:
            # get upper sub-categories
            top_div_of_lower = self.driver.find_element(by=By.XPATH, value='//*[@id="main"]/div/div[3]/div/div[last()]/div[1]/div[1]/div/div/div[2]/div/div[2]/div')
            lower_sub_category_elements = top_div_of_lower.find_elements(By.CSS_SELECTOR, 'a')
            for e in lower_sub_category_elements:
                sub_category_hrefs.append(e.get_attribute('href'))
        return sub_category_hrefs

    def get_product_elements_in_a_page(self):
        product_data = []
        for i in range(60):
            try:
                element_number = i + 1
                product_name_element = self.driver.find_element(By.XPATH, f'//*[@id="main"]/div/div[3]/div/div[last()]/div[2]/div/div[2]/div[{element_number}]/a/div/div/div[2]/div[1]/div/div')
                product_name = product_name_element.text
                product_price_element = self.driver.find_element(By.XPATH, f'//*[@id="main"]/div/div[3]/div/div[last()]/div[2]/div/div[2]/div[{element_number}]/a/div/div/div[2]/div[2]/div')
                product_price = product_price_element.text
                product_data.append((product_name, product_price))
            except:
                break
        return product_data

    # control the scroll bar going down slowly
    def move_to_the_bottom_of_the_page(self):
        self.driver.maximize_window() # maximize the browser window
        total_height = int(self.driver.execute_script("return document.body.scrollHeight"))
        for i in range(1, total_height, 5):
            self.driver.execute_script("window.scrollTo(0, {});".format(i))

    def go_to_the_next_page(self):
        try:
            action = self.webdriver.ActionChains(self.driver)
            next_page_element = self.driver.find_element(By.XPATH, f'//*[@id="main"]/div/div[3]/div/div[last()]/div[2]/div/div[3]/div/button[last()]')
            action.move_to_element(next_page_element)
            action.click(next_page_element).perform()
        except:
            return False
        else:
            return True

    def go_to_the_href(self, href):
        self.driver.get(href)

    # about dealing with the database
    def batch_insert_product_data(self, product_data):
        with sqlite3.connect(self.database_connection, check_same_thread=False) as conn:
            conn.cursor().executemany("insert into product(description, price) values (?,?)", product_data)

    # about translating traditional chinese to simple chinses
    def translate_traditional_chinese_to_simple_chinese(self, traditional_chinese_sentence):
        sentence_len = len(traditional_chinese_sentence)
        current_index = 0
        new_sentence = ''
        while(current_index < sentence_len):
            if traditional_chinese_sentence[current_index] in self.sorted_hant2hans_map:
                current_key = traditional_chinese_sentence[current_index]
                is_match = False
                for k, v in self.sorted_hant2hans_map[current_key].items():
                    sub_key_len = len(k)
                    if (sub_key_len + current_index) > sentence_len:
                        continue
                    else:
                        if k in traditional_chinese_sentence[current_index:current_index+sub_key_len]:
                            new_sentence += v
                            current_index += sub_key_len
                            is_match = True
                            break
                if not is_match:
                    new_sentence += traditional_chinese_sentence[current_index]
                    current_index += 1 
            else:
                new_sentence += traditional_chinese_sentence[current_index]
                current_index += 1
        return new_sentence

    def translate_product_data(self, product_data):
        translated_product_data = []
        for product_name, product_price in product_data:
            translated_product_data.append((self.translate_traditional_chinese_to_simple_chinese(product_name), product_price))
        return translated_product_data

    def run(self):
        self.tool_belt.worker_check_in()
        while self.tool_belt.count_task_number() > 0:
            number_of_task = self.tool_belt.count_task_number()
            main_category_href = self.tool_belt.get_a_task()
            print("============================================")
            print(f"Taking the task of the queue.(total: {number_of_task})")
            self.go_to_the_href(main_category_href)
            sub_category_hrefs = self.get_all_sub_category_links_from_the_current_category()
            sub_category_hrefs.append(main_category_href)
            for index, sub_category_href in enumerate(sub_category_hrefs):
                print("-------------------------------------------")
                print(f"Crawling the {index} url in the sub category href {len(sub_category_hrefs)}")
                self.go_to_the_href(sub_category_href)
                page_number = 0
                while(True):
                    print(f"Page number: {page_number}")
                    self.move_to_the_bottom_of_the_page()
                    product_data = self.get_product_elements_in_a_page()
                    translated_product_data = self.translate_product_data(product_data)
                    self.batch_insert_product_data(translated_product_data)
                    is_next_page_exist = self.go_to_the_next_page()
                    if is_next_page_exist:
                        page_number += 1
                    else:
                        break
        self.call_it_a_day()
