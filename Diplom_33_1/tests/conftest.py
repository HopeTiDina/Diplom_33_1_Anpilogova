import os
import pytest
import uuid
import allure
from selenium import webdriver


@pytest.fixture(scope="function")
def chrome_browser_instance(request):
    options = webdriver.ChromeOptions()
    browser = webdriver.Chrome(options=options)
    browser.maximize_window()
    yield browser
    log_file = os.path.join(os.getcwd(), "cookie_log.txt")
    with open(log_file, "w") as f:
        before_cookies = browser.get_cookies()
        f.write("Cookies before deletion:\n")
        for cookie in before_cookies:
            f.write(str(cookie) + "\n")
        browser.delete_all_cookies()
        after_cookies = browser.get_cookies()
        f.write("Cookies after deletion:\n")
        for cookie in after_cookies:
            f.write(str(cookie) + "\n")
    browser.quit()


@pytest.fixture
def chrome_options(chrome_options):
    # chrome_options.binary_location = '/usr/bin/google-chrome-stable'
    # chrome_options.add_argument('--headless')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--log-level=DEBUG')

    return chrome_options


@pytest.hookimpl(hookwrapper=True, tryfirst=True)
def pytest_runtest_makereport(item, call):
    # Эта функция помогает обнаружить, что какой-либо тест не прошел успешно
    # и передать эту информацию в teardown:

    outcome = yield
    rep = outcome.get_result()
    setattr(item, "rep_" + rep.when, rep)
    return rep


@pytest.fixture
def web_browser(request, selenium):
    browser = selenium
    browser.set_window_size(1400, 1000)

    # Вернуть экземпляр браузера в тестовый пример:
    yield browser

    # Выполнить разборку (этот код будет выполняться после каждого теста):

    if request.node.rep_call.failed:
        # Сделайте снимок экрана, если тест не удался.:
        try:
            browser.execute_script("document.body.bgColor = 'white';")

            # Сделайте снимок экрана для локальной отладки:
            browser.save_screenshot('screenshots/' + str(uuid.uuid4()) + '.png')

            # Приложите скриншот к отчету Allure:
            allure.attach(browser.get_screenshot_as_png(),
                          name=request.function.__name__,
                          attachment_type=allure.attachment_type.PNG)

            # Для успешной отладки:
            print('URL: ', browser.current_url)
            print('Browser logs:')
            for log in browser.get_log('browser'):
                print(log)

        except:
            pass # просто игнорируйте любые ошибки здесь


def get_test_case_docstring(item):
    """ Эта функция получает строку doc из тестового примера и форматирует ее
    так, чтобы она отображалась в отчетах вместо имени тестового примера.
     """

    full_name = ''

    if item._obj.__doc__:
        # Удалите лишние пробелы из строки документа:
        name = str(item._obj.__doc__.split('.')[0]).strip()
        full_name = ' '.join(name.split())

        # Сгенерировать список параметров для параметризованных тестовых случаев:
        if hasattr(item, 'callspec'):
            params = item.callspec.params

            res_keys = sorted([k for k in params])
            # Создать список на основе Dict:
            res = ['{0}_"{1}"'.format(k, params[k]) for k in res_keys]
            # Добавьте dict со всеми параметрами к названию тестового примера:
            full_name += ' Parameters ' + str(', '.join(res))
            full_name = full_name.replace(':', '')

    return full_name


def pytest_itemcollected(item):
    """ Эта функция изменяет названия тестовых наборов "on the fly"
     во время выполнения тестовых наборов.
     """

    if item._obj.__doc__:
        item._nodeid = get_test_case_docstring(item)


def pytest_collection_finish(session):
    """ Эта функция изменяет названия тестовых примеров "on the fly"
    , когда мы используем параметр --collect-only для pytest
    (чтобы получить полный список всех существующих тестовых примеров).
     """

    if session.config.option.collectonly is True:
        for item in session.items:
            # Если в тестовом примере есть строка doc, нам нужно изменить ее название на
            # это строка doc, чтобы отображать удобочитаемые отчеты и
            # автоматически импортировать тестовые примеры в систему управления тестированием.
            if item._obj.__doc__:
                full_name = get_test_case_docstring(item)
                print(full_name)

        pytest.exit('Done!')
