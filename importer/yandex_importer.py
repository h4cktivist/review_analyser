import datetime
import time

from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException
import undetected_chromedriver


class YandexParser:
    def __init__(self, driver):
        self.driver = driver

    def __scroll_to_bottom(self, elem) -> None:
        self.driver.execute_script(
            "arguments[0].scrollIntoView();",
            elem
        )
        time.sleep(1)
        new_elem = self.driver.find_elements(By.CLASS_NAME, "business-reviews-card-view__review")[-1]
        if elem == new_elem:
            return
        self.__scroll_to_bottom(new_elem)

    def __get_item_data(self, elem):
        try:
            date = elem.find_element(By.XPATH, ".//meta[@itemprop='datePublished']").get_attribute('content')
        except NoSuchElementException:
            date = None

        try:
            text = elem.find_element(By.CLASS_NAME, "business-review-view__body").text
        except NoSuchElementException:
            text = None

        return {
            "text": text,
            "date": date
        }

    def __get_reviews_data(self) -> list:
        reviews = []
        elements = self.driver.find_elements(By.CLASS_NAME, "business-reviews-card-view__review")
        if len(elements) > 1:
            self.__scroll_to_bottom(elements[-1])
            elements = self.driver.find_elements(By.CLASS_NAME, "business-reviews-card-view__review")
            for elem in elements:
                reviews.append(self.__get_item_data(elem))
        return reviews

    def __isinstance_page(self):
        try:
            xpath_name = ".//h1[@class='orgpage-header-view__header']"
            name = self.driver.find_element(By.XPATH, xpath_name).text
            return True
        except NoSuchElementException:
            return False

    def parse_reviews(self) -> dict:
        if not self.__isinstance_page():
            return {'error': 'Страница не найдена'}
        return {'company_reviews': self.__get_reviews_data()}


class YandexReviewsImporter:
    def __open_page(self, yandex_id: int):
        url: str = 'https://yandex.ru/maps/org/{}/reviews/'.format(str(yandex_id))
        opts = undetected_chromedriver.ChromeOptions()
        opts.add_argument('--no-sandbox')
        opts.add_argument('--disable-dev-shm-usage')
        opts.add_argument('headless')
        opts.add_argument('--disable-gpu')
        driver = undetected_chromedriver.Chrome(options=opts)
        parser = YandexParser(driver=driver)
        driver.get(url)
        return parser

    def parse_reviews(self, yandex_id: int):
        result = {}
        page = self.__open_page(yandex_id)
        time.sleep(4)

        try:
            result = page.parse_reviews()
        except Exception as e:
            print(e)
            return result
        finally:
            page.driver.close()
            page.driver.quit()
            return result

yandex_reviews_importer = YandexReviewsImporter()
