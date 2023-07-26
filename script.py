import json
import random
import logging
import time
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.select import Select
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chromium.service import ChromiumService
filename="selenium.log"

#initialize the logging
logging.basicConfig(
    level=logging.DEBUG,
    filename=filename,
    format='[%(asctime)s][%(levelname)s] - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S')

#get the details from json file
parsed_details=json.load(open('appdata.json'))

#the test payment url to visit
url=parsed_details['payment_url']

#the credit card details to use
cards=parsed_details['cards']

#user data to be filled
form_data=parsed_details['form_data']


def make_payment(amount: str) -> bool:
    service=ChromiumService('/home/ubuntu/MyProjects/stripe-app/chromium.chromedriver')
    options=webdriver.ChromeOptions()
    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    driver=webdriver.Chrome(service=service,options=options)
    driver.maximize_window()
    driver.implicitly_wait(10)

    driver.get(url)
    amount_el=driver.find_element(By.CSS_SELECTOR,'input[name="customUnitAmount"]')
    amount_el.send_keys(amount)
    email_input=driver.find_element(By.ID,'email')
    email_input.send_keys(form_data['email'])
    card=random.choice(cards)

    card_number_input=driver.find_element(By.ID,'cardNumber')
    card_number_input.send_keys(card['number'])

    expiry_date_input=driver.find_element(By.ID,'cardExpiry')
    expiry_date_input.send_keys(card['expiry_date'])

    cvc_input=driver.find_element(By.ID,'cardCvc')
    cvc_input.send_keys(card['cvc'])

    billing_name_input=driver.find_element(By.ID,'billingName')
    billing_name_input.send_keys(form_data['username'])

    billing_country=driver.find_element(By.ID,'billingCountry')
    options=Select(billing_country)
    options.select_by_visible_text(form_data['country'])

    zip_input=driver.find_element(By.ID,'billingPostalCode')
    zip_input.send_keys(form_data['zipcode'])

    submit_button=WebDriverWait(driver,10).until(EC.element_to_be_clickable((By.CSS_SELECTOR,"button[type='submit']")))
    driver.execute_script("arguments[0].click();", submit_button)

    time.sleep(5)
    driver.save_screenshot(f'payment_status-{datetime.now().strftime("%Y-%m-%d-%H-%M-%S")}.png')
    print(f"Made a payment of amount {amount}")
    driver.quit()