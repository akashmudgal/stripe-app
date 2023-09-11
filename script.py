import json
import random
import logging
import requests

#get the details from json file
parsed_details=json.load(open('appdata.json'))

#the test payment url to visit
url=parsed_details['payment_url']

#the credit card details to use
cards=parsed_details['cards']

#user data to be filled
user_data=parsed_details['user_data']


#The API Key
key="pk_test_51MhExUAebRllQQxLbT9xHAoMyNqqIFMgfpzIZsCPt8NbMkh2PZOuhPmf5mfPG8ep7PLPXMvgQP4XMyVkvVZucsIl0008OoO8jF"


#The common headers
#common headers
headers = {
    'authority': 'api.stripe.com',
    'accept': 'application/json',
    'accept-language': 'en-US,en;q=0.9',
    'content-type': 'application/x-www-form-urlencoded',
    'origin': 'https://checkout.stripe.com',
    'referer': 'https://checkout.stripe.com/',
}

def create_payment_method(cards,user_data):
    #Select a card at random
    card=random.choice(cards)

    #the url for request
    url = 'https://api.stripe.com/v1/payment_methods'

    data = {
    'type': 'card',
    'card[number]': card['number'],
    'card[cvc]': card['cvc'],
    'card[exp_month]': card['expiry_date'].split("/")[0],
    'card[exp_year]': card['expiry_date'].split("/")[1],
    'billing_details[name]': user_data['name'],
    'billing_details[email]': user_data['email'],
    'billing_details[address][country]': user_data['country'],
    'billing_details[address][postal_code]': user_data['zipcode'],
    'key': key,
    'payment_user_agent': 'stripe.js/5fafadf87b; stripe-js-v3/5fafadf87b; payment-link; checkout'
    }

    response=requests.post(url=url,headers=headers,data=data).json()

    return response['id']

def create_payment_session(url: str,amount: str):
    #get the payment link
    response=requests.get(url)
    plink_url=response.url

    # create the payment session
    plink=plink_url.rsplit("/",1)[1].split('#')[0]

    data={
        "key": key,
        "payment_link": plink
    }
    url='https://api.stripe.com/v1/payment_pages/for_plink'

    payment_page_response = requests.post(url, headers=headers, data=data).json()

    #update payment session to expect set payment amount
    data={
        'key': key,
        'updated_line_item_amount[line_item_id]': payment_page_response['line_item_group']['line_items'][0]['id'],
        'updated_line_item_amount[unit_amount]': amount+'00'
    }

    response=requests.post(f'https://api.stripe.com/v1/payment_pages/{payment_page_response["session_id"]}',headers=headers,data=data)
    
    return payment_page_response['session_id']

def make_payment(amount: str) -> bool:
    #create the payment method and get id
    payment_method_id=create_payment_method(cards,user_data)

    #create the payment session and get session_id
    session_id=create_payment_session(url,amount)

    # make the payment API call
    #Make the payment
    payment_url=f'https://api.stripe.com/v1/payment_pages/{session_id}/confirm'
    data = {
        'eid': 'NA',
        'payment_method': payment_method_id,
        'expected_amount': amount+'00',
        'expected_payment_method_type': 'card',
        'key': key,
    }

    response = requests.post(payment_url, headers=headers, data=data)

    if response.status_code == 200:
        logging.info(f'Payment succeeded! Amount: {amount}')
    else:
        logging.error(f'The API call for payment failed.')