import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

USERNAME = ""
PASSWORD = ""

# Настройки браузера
options = webdriver.ChromeOptions()
# Для отладки можно отключить headless, чтобы видеть окно браузера:
options.add_argument("--headless")
options.add_argument("--disable-gpu")
options.add_argument("--no-sandbox")

# Инициализация драйвера
service = Service(ChromeDriverManager().install())
driver = webdriver.Chrome(service=service, options=options)

def login_itmo():
    login_url = (
        "https://id.itmo.ru/auth/realms/itmo/protocol/openid-connect/auth?"
        "protocol=oauth2&response_type=code&access_type&client_id=student-personal-cabinet&"
        "redirect_uri=https%3A%2F%2Fmy.itmo.ru%2Flogin%2Fcallback&"
        "scope=openid%20profile&state=fvGwMn6smN&code_challenge_method=S256&"
        "code_challenge=MwrX6rh1j20T1R8DFp7FudiPVD_wg11HP8WZWRHLKME"
    )
    driver.get(login_url)
    
    # Ждем появления формы логина
    WebDriverWait(driver, 10).until(EC.visibility_of_element_located((By.ID, "username")))
    
    driver.find_element(By.ID, "username").clear()
    driver.find_element(By.ID, "username").send_keys(USERNAME)
    driver.find_element(By.ID, "password").clear()
    driver.find_element(By.ID, "password").send_keys(PASSWORD)
    driver.find_element(By.ID, "kc-login").click()
    
    # Ждем редиректа на my.itmo.ru
    WebDriverWait(driver, 30).until(EC.url_contains("my.itmo.ru"))
    print("Авторизация прошла успешно. Текущий URL:", driver.current_url)

def set_language_ru():
    """
    Переключает язык страницы на русский, кликая по выпадающему меню языка.
    """
    try:
        # Ждем появления переключателя языка. Используем ID родительского li.
        lang_toggle = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "li#__BVID__49 a.dropdown-toggle"))
        )
        lang_toggle.click()
        # Ожидаем появления выпадающего меню и кликаем по опции "Русский"
        ru_option = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((
                By.XPATH,
                "//ul[@id='__BVID__49__BV_toggle_menu_']//a[contains(., 'Русский')]"
            ))
        )
        ru_option.click()
        print("Язык переключен на русский.")
        # Небольшая задержка для применения изменений
        time.sleep(2)
    except Exception as e:
        print("Ошибка при переключении языка:", e)

def search_person(query):
    driver.get("https://my.itmo.ru/persons")
    set_language_ru()
    # Находим поле ввода (селектор не зависит от языка)
    search_input = WebDriverWait(driver, 30).until(
        EC.visibility_of_element_located((
            By.CSS_SELECTOR,
            "input.form-control[type='text'][id^='__BVID__']"
        ))
    )
    print("Элемент ввода найден:", search_input.get_attribute("outerHTML"))
    search_input.clear()
    search_input.send_keys(query)
    
    # Находим кнопку "Поиск" и кликаем по ней
    search_button = WebDriverWait(driver, 10).until(
        EC.element_to_be_clickable((
            By.CSS_SELECTOR,
            "div.col-auto > button.btn.btn-primary"
        ))
    )
    print("Кнопка поиска найдена:", search_button.get_attribute("outerHTML"))
    search_button.click()
    print("Нажата кнопка поиска. Ожидаем загрузку страницы...")
    time.sleep(6)
    WebDriverWait(driver, 30).until(
        lambda d: d.execute_script("return document.readyState") == "complete"
    )
    print("Состояние страницы: complete")
    
    all_persons = []
    page_number = 1

    while True:
        print(f"\nОбрабатываем страницу {page_number}...")
        results_container = WebDriverWait(driver, 30).until(
            EC.visibility_of_element_located((
                By.CSS_SELECTOR,
                "div.row.mt-3.align-items-stretch"
            ))
        )
        cards = results_container.find_elements(By.CSS_SELECTOR, "div.col-xxl-3.col-md-6.col-xl-4.col-12")
        print(f"Найдено {len(cards)} карточек на странице {page_number}.")
        for card in cards:
            try:
                person_id = card.find_element(By.CSS_SELECTOR, "span.badge-primary-blue").text.strip()
                person_name = card.find_element(By.CSS_SELECTOR, "div.font-weight-bold").text.strip()
                person_info = card.find_element(By.CSS_SELECTOR, "div.text-sm.text-gray-60").text.strip()
                photo_element = card.find_element(By.CSS_SELECTOR, "div.person-card-photo")
                style_attr = photo_element.get_attribute("style")
                photo_url = ""
                if "url(" in style_attr:
                    photo_url = style_attr.split("url(")[1].split(")")[0].strip(' "\'')
                all_persons.append({
                    "id": person_id,
                    "name": person_name,
                    "info": person_info,
                    "photo": photo_url
                })
            except Exception as e:
                print("Ошибка при обработке карточки:", e)
                continue

        try:
            # Анализируем панель пагинации
            pagination_items = driver.find_elements(By.CSS_SELECTOR, "ul.pagination.mb-0 li.pagination-item")
            pages = [int(item.text.strip()) for item in pagination_items if item.text.strip().isdigit()]
            max_page = max(pages) if pages else 1

            active_item = driver.find_element(By.CSS_SELECTOR, "ul.pagination.mb-0 li.pagination-item.active")
            active_page = int(active_item.text.strip())
            print(f"Текущая страница: {active_page}, последняя страница: {max_page}")

            if active_page >= max_page:
                print("Достигнута последняя страница. Завершаем сканирование.")
                break

            next_button = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((
                    By.XPATH,
                    "//ul[contains(@class, 'pagination')]/li[normalize-space()='〉']"
                ))
            )
            print("Кнопка '〉' найдена. Переход на следующую страницу...")
            next_button.click()
            time.sleep(6)
            WebDriverWait(driver, 30).until(
                lambda d: d.execute_script("return document.readyState") == "complete"
            )
            page_number += 1
        except Exception as e:
            print("Пагинация не найдена или произошла ошибка. Завершаем сканирование.", e)
            break

    return all_persons

if __name__ == '__main__':
    try:
        login_itmo()
        # Переключаем язык на русский перед поиском
        search_query = "Иванова Анна"
        results = search_person(search_query)
        print(f"\nНайдено {len(results)} результатов по запросу '{search_query}':")
        for person in results:
            print("ID:", person["id"])
            print("Ф.И.О.:", person["name"])
            print("Информация:", person["info"])
            print("Фото:", person["photo"])
            print("----------")
    finally:
        driver.quit()