from webdriver_manager.chrome import ChromeDriverManager
from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
import queue

from db_function import init_database
from utils import get_sorted_hant2hans_map
from objects import ToolBelt, Crawler


if __name__ == '__main__':
    sorted_hant2hans_map = get_sorted_hant2hans_map('resources/hant2hans.csv')
    init_database()

    task_queue = queue.Queue()
    worker_queue = queue.Queue()

    service = ChromeService(executable_path=ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service)

    tool_belt = ToolBelt(service, webdriver, task_queue, worker_queue, sorted_hant2hans_map)

    all_category_hrefs = Crawler.get_all_category_links_from_Shopee(driver, tool_belt.get_shoppe_category_link())
    for main_category_href in all_category_hrefs:
        tool_belt.publish_a_task(main_category_href)

    driver.quit()

    crawler_number = 3
    for crawler in range(crawler_number):
        Crawler(tool_belt).start()

    task_queue.join()
    worker_queue.join()
