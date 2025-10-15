import time
from termcolor import colored

from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


class WebPage(object):

    _web_driver = None

    def __init__(self, web_driver, url=''):
        self._web_driver = web_driver
        self.get(url)

    def __setattr__(self, name, value):
        if not name.startswith('_'):
            self.__getattribute__(name)._set_value(self._web_driver, value)
        else:
            super(WebPage, self).__setattr__(name, value)

    def __getattribute__(self, item):
        attr = object.__getattribute__(self, item)

        if not item.startswith('_') and not callable(attr):
            attr._web_driver = self._web_driver
            attr._page = self

        return attr

    def get(self, url):
        self._web_driver.get(url)
        self.wait_page_loaded()

    def go_back(self):
        self._web_driver.back()
        self.wait_page_loaded()

    def refresh(self):
        self._web_driver.refresh()
        self.wait_page_loaded()

    def screenshot(self, file_name='screenshot.png'):
        self._web_driver.save_screenshot(file_name)

    def scroll_down(self, offset=0):
        """ Scroll the page down. """

        if offset:
            self._web_driver.execute_script('window.scrollTo(0, {0});'.format(offset))
        else:
            self._web_driver.execute_script('window.scrollTo(0, document.body.scrollHeight);')

    def scroll_up(self, offset=0):
        """ Прокрутите страницу вверх."""

        if offset:
            self._web_driver.execute_script('window.scrollTo(0, -{0});'.format(offset))
        else:
            self._web_driver.execute_script('window.scrollTo(0, -document.body.scrollHeight);')

    def switch_to_iframe(self, iframe):
        """ Переключиться на iframe по его имени. """

        self._web_driver.switch_to.frame(iframe)

    def switch_out_iframe(self):
        """ Отмените фокус на iframe. """
        self._web_driver.switch_to.default_content()

    def get_current_url(self):
        """ Возвращает текущий URL браузера. """

        return self._web_driver.current_url

    def get_page_source(self):
        """ Возвращает тело текущей страницы."""

        source = ''
        try:
            source = self._web_driver.page_source
        except:
            print(colored('Con not get page source', 'red'))

        return source

    def check_js_errors(self, ignore_list=None):
        """ Эта функция проверяет наличие ошибок JS на странице. """

        ignore_list = ignore_list or []

        logs = self._web_driver.get_log('browser')
        for log_message in logs:
            if log_message['level'] != 'WARNING':
                ignore = False
                for issue in ignore_list:
                    if issue in log_message['message']:
                        ignore = True
                        break

                assert ignore, 'JS error "{0}" on the page!'.format(log_message)

    def wait_page_loaded(self, timeout=60, check_js_complete=True,
                         check_page_changes=False, check_images=False,
                         wait_for_element=None,
                         wait_for_xpath_to_disappear='',
                         sleep_time=2):
        """ Эта функция ожидает полного загрузки страницы.
        Мы используем множество методов для определения, загружена ли страница:

        1) Проверка статуса JS
        2) Проверка изменений в исходном коде страницы
        3) Проверка, что все изображения полностью загружены
           (Примечание: эта проверка отключена по умолчанию)
        4) Проверка наличия ожидаемых элементов на странице
        """

        page_loaded = False
        double_check = False
        k = 0

        if sleep_time:
            time.sleep(sleep_time)

        # Получить исходный код страницы для отслеживания изменений в HTML:
        source = ''
        try:
            source = self._web_driver.page_source
        except:
            pass

        #Ожидание полной загрузки страницы (и прокрутка её, чтобы убедиться, что все объекты загрузились):
        while not page_loaded:
            time.sleep(0.5)
            k += 1

            if check_js_complete:
                # Прокрутите вниз и дождитесь полной загрузки страницы:
                try:
                    self._web_driver.execute_script('window.scrollTo(0, document.body.scrollHeight);')
                    page_loaded = self._web_driver.execute_script("return document.readyState == 'complete';")
                except Exception as e:
                    pass

            if page_loaded and check_page_changes:
                # Проверьте, был ли изменен исходный код страницы.
                new_source = ''
                try:
                    new_source = self._web_driver.page_source
                except:
                    pass

                page_loaded = new_source == source
                source = new_source

            # Подождите, пока какой-либо элемент не исчезнет.
            if page_loaded and wait_for_xpath_to_disappear:
                bad_element = None

                try:
                    bad_element = WebDriverWait(self._web_driver, 0.1).until(
                        EC.presence_of_element_located((By.XPATH, wait_for_xpath_to_disappear))
                    )
                except:
                    pass  # Игнорировать ошибки тайм-аута.

                page_loaded = not bad_element

            if page_loaded and wait_for_element:
                try:
                    page_loaded = WebDriverWait(self._web_driver, 0.1).until(
                        EC.element_to_be_clickable(wait_for_element._locator)
                    )
                except:
                    pass  # Игнорировать ошибки тайм-аута.

            assert k < timeout, 'The page loaded more than {0} seconds!'.format(timeout)

            # Проверьте дважды, что страница полностью загрузилась.
            if page_loaded and not double_check:
                page_loaded = False
                double_check = True

            # Вверх:
        self._web_driver.execute_script('window.scrollTo(document.body.scrollHeight, 0);')