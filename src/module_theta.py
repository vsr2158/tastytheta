import requests
import json

def theta_log_trade(position, status):
    print(f"Going to update {status} Thetaseekers.club")

    #update sub in position
    position['sub'] = sub
    position['status'] = status

    url_theta = uri_theta + '/api/logtrade_tt'

    resp_theta = requests.post(url_theta,
                               data=json.dumps(position),
                               headers={'Content-Type': 'application/json'})
    print('Theta Update Done !!!!')

def theta_log_transaction(transactions, config):
    print(f"Going to push tranactions to Thetaseekers.club")

    uri_theta = config['uri_theta']
    url_theta = uri_theta + '/api/logtransactions_tt'
    resp_theta = requests.post(url_theta,
                               data=json.dumps(transactions),
                               headers={'Content-Type': 'application/json'})
    if resp_theta.status_code == 200:
        print('Theta Update Done !!!!')
        return (resp_theta.json())

    else:
        print('Error push tranactions to Thetaseekers.club ')
        print(resp_theta.status_code)
        print(resp_theta.url)



