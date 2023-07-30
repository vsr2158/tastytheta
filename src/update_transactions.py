from src import module_tt, module_theta
import csv
import json
import re
import datetime

def scrubber(transactions_dict):
    # this function normalises the transaction data and removes sensitive info
    ignored_transaction_types = ['Money Movement']
    valid_sub_types = ['Sell to Open', 'Buy to Open', 'Sell to Close', 'Buy to Close',\
                       'Assignment','Cash Settled Assignment','Cash Settled Exercise', 'Transfer']
    transactions_list = transactions_dict["items"]
    transactions_dict_new = {}
    transactions_list_new = []

    for t in transactions_list:
        if (t['transaction-sub-type'] in valid_sub_types) and (t['transaction-type'] not in ignored_transaction_types):
            # initialise a new dict
            t_new = {}
            t_new['utag1'] = config['account-number']
            t_new['executed_at'] = t['executed-at']
            t_new['ledger_id'] = f"{t['id']}_{config['sub']}"
            t_new['symbol'] = t['underlying-symbol']
            t_new['qty'] = t['quantity']

            if (t['transaction-sub-type'] == 'Assignment') or (t['transaction-sub-type'] =='Cash Settled Assignment'):
                t_new['premium'] = '0.05'
                t_new['action'] = 'Close'
            elif (t['transaction-sub-type'] == 'Exercise') or (t['transaction-sub-type'] =='Cash Settled Exercise'):
                t_new['premium'] = '0.05'
                t_new['action'] = 'Buy'
            else:
                t_new['premium'] = t['price']
                t_new['action'] = t['action']

            t_new['description'] = t['description']
            t_new['exec_date'] = t['transaction-date']

            symbol = t["symbol"]
            t_new["ledger_id_grp"] = symbol.replace(" ", "_")
            t_new["ledger_id_grp"] = re.sub(r"_+", "_", t_new["ledger_id_grp"])

            if t['underlying-symbol'] == t['symbol']:
                t_new["type"] = 'EQTY'
                t_new["exp_date"] = t['transaction-date']
                t_new["strike"] = t['price']
                if 'Transfer' in t['transaction-sub-type']:
                    t_new['price'] = t['lots'][0]['price']
                    t_new["strike"] = t_new['price']
                    t_new["premium"] = t_new['price']

            else:
                expiry = symbol[-15:]
                expiry = expiry[:6]
                year = expiry[:2]
                year = '20' + year
                day = expiry[4:]
                month = expiry[2:][:2]

                expiry = year + '-' + month + '-' + day
                # expiry_date = datetime.date(int(year), int(month), int(day))
                t_new['exp_date'] = expiry

                strike = symbol[-8:]
                strike = float(strike) / 1000
                t_new['strike'] = strike

                type = symbol[-9:]
                type = type[:1]

                if type == 'C':
                    t_new["type"] = 'CALL'
                elif type == 'P':
                    t_new["type"] = 'PUT'

                else:
                    print('No Match of Type')

            if 'Buy' in t['transaction-sub-type'] :
                # commenting below as we are using Premium key not price and its handled in theta
                # t_new['price'] = str(float(t['price'])* -1)
                pass

            if 'Sell' in t['transaction-sub-type'] :
                t_new['qty'] = str(float(t['quantity'])* -1)

            if 'Cash Settled Exercise' in t['transaction-sub-type'] :
                t_new['qty'] = str(float(t['quantity']) * -1)
                # commenting below as we are using Premium key not price and its handled in theta
                # t_new['price'] = str(float(t['price'])* -1)

            if 'Transfer' in t['transaction-sub-type'] and 'Sell' in t['action']:
                t_new['qty'] = str(float(t['quantity']) * -1)

            else:
                pass

            transactions_list_new.append(t_new)
            transactions_dict_new['items'] = transactions_list_new
            transactions_dict_new['email'] = config['email']
            transactions_dict_new['sub'] = config['sub']

    return transactions_dict_new

def json_to_csv(transactions_dict):
    # Extract the items list from the JSON data
    items = transactions_dict['items']

    # Open the CSV file in write mode
    with open(f"../transactions_scrubbed_{a}.csv", mode='w', newline='') as csv_file:
        # Define the CSV writer
        csv_writer = csv.writer(csv_file)

        # Write the header row
        header_row = items[0].keys()
        csv_writer.writerow(header_row)

        # Write each item as a row in the CSV file
        for item in items:
            csv_writer.writerow(item.values())

    # close cs file
    csv_file.close()


if __name__ == "__main__":
    #Load config file
    try:
        with open('../config.json', 'r') as fp:
            config = json.load(fp)
    except:
        print('Config file not found!!')
        exit()
    # Get accounts for this user
    account_list = module_tt.tt_get_accounts(config)
    print('==========================================================')
    print('FOUND LIST OF ACCOUNTS :', account_list)

    d = input('How many days back should we fetch transactions for ? [Just enter for all]: ')
    if d:
        start_date = datetime.datetime.today() - datetime.timedelta(days=int(d))
    else:
        start_date = datetime.datetime.min

    start_date = start_date.strftime('%Y-%m-%d')
    print('==========================================================')
    print(f'Going to pull transactions from {start_date} till Today')
    print('==========================================================')
    symbol_filter = (input('Type in a symbol to filter transactions [Just enter for all]: ')).upper()

    # All inputs taken
    # Loop through the account list and fetch all positions
    for a in account_list:
        #Get transactions for this account
        transactions_dict = module_tt.tt_get_tranactions(a, config, start_date)
        transactions_dict = transactions_dict.get('data')

        #Scrub transactions to remove unnessary and sensitive info
        transactions_dict = scrubber(transactions_dict)

        # add condition if symbol_filter is not empty and transactions_dict is not empty
        if symbol_filter and 'items' in transactions_dict:
            transactions_dict["items"] = [item for item in transactions_dict["items"] if item["symbol"] == symbol_filter]
            print('Applied filter to transactions for symbol :', symbol_filter)

        with open(f"../transactions_scrubbed_{a}.json", "w") as fp:
            json.dump(transactions_dict, fp)
            # close json file
            fp.close()

        #write a csv file
        json_to_csv(transactions_dict)

        # Push to theta if not empty
        if len(transactions_dict['items']) !=0 :
            result = module_theta.theta_log_transaction(transactions_dict, config)
            print('==========================================================')
            print(result)
            print('==========================================================')
        else:
            print('==========================================================')
            print('Nothing to update to Theta!')
            print('==========================================================')



