import requests
from .models import BankAccount
from django.conf import settings
from paystackapi.paystack import Paystack

def get_country_name(country_code):
    url = f"https://restcountries.com/v2/alpha/{country_code}"
    response = requests.get(url)

    if response.status_code == 200:
        country_data = response.json()
        country_name = country_data['name']
        return country_name

    return None

def get_supported_banks():
    url = 'https://api.paystack.co/bank'
    headers = {
        'Authorization': f'Bearer {settings.PAYSTACK_SECRET_KEY}',
        'Content-Type': 'application/json',
    }

    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        banks = response.json()['data']
        return banks
    else:
        response_data = response.json()
        error_message = response_data.get('message', 'An error occurred')
        raise Exception(f"API Error: {error_message}")

def get_country_by_currency(currency_code):
    base_url = 'https://openexchangerates.org/api/currencies.json'
    response = requests.get(base_url)

    if response.status_code == 200:
        currencies = response.json()
        country_code = None

        for code, currency in currencies.items():
            if currency_code == currency:
                country_code = code
                break

        if country_code:
            country_url = f'https://restcountries.com/v2/alpha/{country_code}'
            response = requests.get(country_url)

            if response.status_code == 200:
                country_data = response.json()
                return country_data

    return None

def check_currency_exists(currency_code):
    url = f'https://api.paystack.co/transaction/verify/{currency_code}'
    headers = {
        'Authorization': f'Bearer {settings.PAYSTACK_SECRET_KEY}',
        'Content-Type': 'application/json',
    }

    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        response_data = response.json()
        status = response_data.get('status')
        if status:
            return True
        else:
            return False
    else:
        response_data = response.json()
        error_message = response_data.get('message', 'An error occurred')
        raise Exception(f"API Error: {error_message}")

def check_currency_acceptance(currency_code):
    paystack_secret_key = settings.PAYSTACK_SECRET_KEY
    paystack = Paystack(secret_key=paystack_secret_key)

    response = paystack.transaction.initialize(
        currency = currency_code,
        amount = 1000,
        email = settings.EMAIL_HOST_USER,
        transaction_charge=0,
        timeout = 18000,
    )

    if response['status']  == True:
        return True
    else:
        return response['message']

def match_country_to_currency(country_name, currency_code):
    url = f"https://restcountries.com/v2/name/{country_name}"
    response = requests.get(url)
    
    if response.status_code == 200:
        countries = response.json()
        
        for country in countries:
            currencies = country['currencies']
            
            for currency in currencies:
                if currency['code'] == currency_code:
                    return True
    return False

def get_country_name(country_code):
    url = f"https://restcountries.com/v2/alpha/{country_code}"
    response = requests.get(url)

    if response.status_code == 200:
        country_data = response.json()
        country_name = country_data['name']
        return country_name

    return None

def get_dialing_code(country_code):

    url = 'http://country.io/phone.json'
    response = requests.get(url)

    if response.status_code == 200:
        content = response.json()
        return content[country_code]
    else:
        return None
    
def get_country_code(country_name):
    url = f'https://restcountries.com/v3.1/name/{country_name}'
    response = requests.get(url)

    if response.status_code == 200:
        country = response.json()
        country_code = [country['cca2'] for country in country]
        return country_code[0]

def get_bank_name(bank_code):
    try:
        bank_list = get_supported_banks()
        
        for i in bank_list:
            if i['code'] == bank_code:
                return i['name']
    except Exception:
        return None

def get_user_accounts(wallet):
    try:
        accounts = BankAccount.objects.filter(wallet=wallet)
        if accounts.exists():
            banks = []
            for account in accounts:
                banks.append({
                    'id': account.id,
                    'account_number': account.account_number,
                    'bank_code': account.bank_code,
                    'account_name': account.account_name,
                    'bank_name': account.bank_name
                })
            return banks
        else:
            return []
    except Exception as e:
        return str(e)
