import time
import requests
import getpass
import json

def authenticate() :
    login = input ('Tasty Trade UserID :')
    password = getpass.getpass('Tasty Trade Password : ',stream=None)

    h_header = {"Content-Type" : "application/json"}
    h_body = {
        "login": login,
        "password": password
    }
    uri = 'https://api.tastyworks.com/'
    path = 'sessions'
    url = uri + path
    response = requests.post(url, headers=h_header , json=h_body)
    print('SESSION TOKEN : ', response.json()['data']['session-token'])

    try:
        with open('../config.json', 'r') as f:
            config = json.load(f)
        config['session_token'] = response.json()['data']['session-token']
        with open('../config.json', 'w') as f:
            json.dump(config, f)
        print('Updated SESSION TOKEN in config.json for subsequent use, this will expire after 24 hours and you are required to login again')
    except:
        pass

    print('Config has been updated, rerun the program again to take effect')
    exit()

def tt_get_marketmetrics(symbol_list,config):
    uri_tt = config['uri_tt']
    h_header = {'Authorization': config['session_token']}
    symbol_string = ','.join(symbol_list)
    path = '/market-metrics/' + '?symbols=' + str(symbol_string)
    url_tt = uri_tt + path
    print(url_tt)
    resp_positions = requests.get(url_tt,headers=h_header)
    return resp_positions.json()

def tt_get_accounts(config):
    uri_tt = config['uri_tt']
    h_header = {'Authorization': config['session_token']}

    path = '/customers/me/accounts'
    url_tt = uri_tt + path
    resp_account = requests.get(url_tt,headers=h_header)
    if resp_account.status_code == 401:
        print('Session Token Expired')
        print(resp_account.status_code)
        print(resp_account.text)
        print('Initiating Authentication')
        authenticate()
        time.sleep(5)

    resp_account = requests.get(url_tt, headers=h_header)
    print(resp_account)
    resp_account_list = resp_account.json()['data']['items']
    account_list = []
    for a in resp_account_list:
        account_list.append(a['account']['account-number'])
    return account_list

def tt_get_positions(account_number,config):
    uri_tt = config['uri_tt']
    h_header = {'Authorization': config['session_token']}

    path = '/accounts/' + account_number + '/positions'
    url_tt = uri_tt + path
    resp_positions = requests.get(url_tt,headers=h_header)
    return resp_positions.json()

def tt_get_tranactions(account_number, config, start_date):
    uri_tt = config['uri_tt']
    h_header = {'Authorization': config['session_token']}

    path = '/accounts/' + account_number + '/transactions'
    url_tt = uri_tt + path
    body = {
        'per-page' : '1000',
        'sort': 'Asc',
        'start-date': start_date
    }
    resp_transanctions = requests.get(url_tt,headers=h_header, data=body)
    return resp_transanctions.json()

def tt_calculate_position_opened(positions_current, positions_previous):
    # compare posiotions_current and positions_previous
    # use symbol (Not underlying) and created)at keys to find uniques
    try:
        positions_current_list = positions_current['data']['items']
    except:
        positions_current_list = []
    try:
        positions_previous_list = positions_previous['data']['items']
    except:
        positions_previous_list = []

    positions_opened_list = []

    print('Positions in previous list :', len(positions_previous_list))
    print('Positions in current list :', len(positions_current_list))

    #for new positions opened compare new positions with previous positions
    for c_position in positions_current_list:
        for p_position in positions_previous_list:
            if c_position['symbol'] == p_position['symbol'] and c_position['created-at'] == p_position['created-at']:
                print('Position already exists')
                break
        else:
            print('New position found')
            positions_opened_list.append(c_position)
    return positions_opened_list

def tt_calculate_position_closed(positions_current, positions_previous):
    # compare posiotions_current and positions_previous
    # use symbol (Not underlying) and created)at keys to find uniques
    try:
        positions_current_list = positions_current['data']['items']
    except:
        positions_current_list = []
    try:
        positions_previous_list = positions_previous['data']['items']
    except:
        positions_previous_list = []

    positions_closed_list = []

    print('Positions in previous list :', len(positions_previous_list))
    print('Positions in current list :', len(positions_current_list))

    #for new positions opened compare new positions with previous positions
    for p_position in positions_previous_list:
        for c_position in positions_current_list:
            if p_position['symbol'] == c_position['symbol'] and p_position['created-at'] == c_position['created-at']:
                print('Position already exists')
                break
        else:
            print('position closed found')
            positions_closed_list.append(p_position)
    return positions_closed_list

