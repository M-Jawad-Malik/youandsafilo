import os
import csv
from playwright.sync_api import sync_playwright

SITE_URL = 'https://www.youandsafilo.com/'
REDIRECTION_URL = 'https://safilo.my.site.com/safilob2b/'
CATEGORY_URL = 'https://safilo.my.site.com/safilob2b/category/rootother/eyeglasses-man/0ZG7T000000CaS3WAK'
USER_NAME = 'arifeyerack@aol.com'
PASSWORD = 'bapmuD-ripsax-qybzy2'
ROOT_PATH = './data'
os.makedirs(ROOT_PATH, exist_ok=True)



def create_scrape_complete_file(file_directory):
    file_path = os.path.join(file_directory, 'scrape_complete.txt')
    
    with open(file_path, 'w') as file:
        pass

def save_to_csv(category_path, products_data):
    csv_file_path = 'products_data.csv'
    file_path = os.path.join(category_path, csv_file_path)

    with open(file_path, 'w', newline='') as csvfile:
        fieldnames = ['Brand', 'Model']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

        writer.writeheader()
        for data in products_data:
            writer.writerow(data)
    
    create_scrape_complete_file(category_path)
    print(f"Product data saved to {file_path}")
    

def scrape_and_save_products(category_path, page):
    load_all_products(page) 
    products = page.query_selector_all('.plp--product__item')
    
    product_data = []

    for product in products:
        brand = product.query_selector('.plp--product-brand span').inner_text()
        model = product.query_selector('.plp--product__name__wrapper span').inner_text()
            
        product_data.append({'Brand': brand, 'Model': model})

    save_to_csv(category_path, product_data)

def load_all_products(page):
    page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
    product_counter = page.query_selector('span.plp--items-out-of')

    if product_counter:
        text_content = product_counter.inner_text()
        values = [int(value) for value in text_content.split() if value.isdigit()]
        current_products = values[0]
        total_product = values[1]

        if current_products == total_product:
            return
        else:        
            load_more_button = page.query_selector('button.slds-p-around_medium.plp--load-more')
            load_more_button.click()
            page.wait_for_timeout(2000)

            load_all_products(page)
    else:
        return

def scrape_play_and_safilo():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context()
        page = context.new_page()
        page.goto(SITE_URL, wait_until='load')
        
        cookies_popup = page.query_selector('#cookie-bar-view-el')
        
        if cookies_popup:
            cookies_accept_btn = page.query_selector('button#acceptCookiesPolicy')    
            cookies_accept_btn.click()
        
        login_form_card = page.query_selector('.card-login-page')        
        
        login_success = False
        if login_form_card:
            username_field = page.query_selector('#emailField')
            password_field = page.query_selector('#passwordField')
            login_btn = page.query_selector('#send2Dsk')
            
            if username_field and password_field and login_btn:
                page.fill('input[name="emailField"]', USER_NAME)
                page.fill('input[name="passwordField"]', PASSWORD)

                login_btn.click()
                page.wait_for_url(REDIRECTION_URL)
                
                login_success = True
            else:
                print('Login form fields not found')
        else:
            print('login form not found')

        if login_success:
            page.wait_for_timeout(1000)
            categories = ['Eyeglasses', 'Sunglasses']
            
            for category in categories:
                scrape_category_products(category, page, 0)

is_scraped = lambda path: os.path.exists(os.path.join(path, 'scrape_complete.txt'))
def scrape_category_products(category, page, index):

    dropdown_selector = f'div.slds-dropdown-trigger.slds-dropdown-trigger_hover button.slds-button:has-text("{category}")'
    dropdown = page.query_selector(dropdown_selector)
    
    dropdown.click()
# > div.header-menu--category-related-dropdown__inner
    container_box = page.query_selector(f'{dropdown_selector} + div.header-menu--category-related-dropdown ')
    categories = container_box.query_selector_all('.header-menu--clickable-item')

    if index == len(categories):
        return 

    categories[index].click()
    page.wait_for_timeout(2000)
    page.reload()
    page.wait_for_timeout(5000)

    category_selector = page.wait_for_selector('h1[c-lexproductcategorybanner_lexproductcategorybanner]')
    if category_selector:
        category_name =category_selector.inner_text().lower().replace(' ', '-')
        category_path = os.path.join(f'{ROOT_PATH}/{category.lower()}', category_name.replace(f'{category.lower()}-', ''))
        os.makedirs(category_path, exist_ok=True)
        
        if not is_scraped(category_path):
            scrape_and_save_products(category_path, page)
        else:
            print(f'products for {category_name} already scrapped')

        scrape_category_products(category, page, index+1)
    else:
        print('Category Banner not found!')

if __name__ == '__main__':
    scrape_play_and_safilo()