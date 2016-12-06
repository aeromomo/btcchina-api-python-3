# -*- coding: utf-8 -*-
# import sys, os
# os.path.dirname(sys.executable)
# print(sys.path)
# print (sys.path[0])
''' 来自可爱的seenkitty
My Motto mot4f6e6c7920486973746f7279204a75646765732
help me with my food in BTC:   1MzAqFPkEro5Z4SJBtuTYm4DAc3WdzQAgc '''

import time
import re
import hmac
import hashlib
import base64
import http.client
import json
# import codecs
class BTCChina():
    def __init__(self,access=None,secret=None):
        # self.access_key=access
        self.access_key=bytearray(access.encode('utf-8'))
        # self.secret_key=secret
        self.secret_key=bytearray(secret.encode('utf-8'))
        self.conn=http.client.HTTPSConnection("api.btcchina.com")
        # print(self.conn)

    def _get_tonce(self):
        return int(time.time()*1000000)

    def _get_params_hash(self,pdict):
        pstring=""
        # The order of params is critical for calculating a correct hash
        fields=['tonce','accesskey','requestmethod','id','method','params']
        for f in fields:
            if pdict[f]:
                if f == 'params':
                    # Convert list to string, then strip brackets and spaces
                    # probably a cleaner way to do this
                    param_string=re.sub("[\[\] ]","",str(pdict[f]))
                    param_string=re.sub("'",'',param_string)
                    param_string=re.sub("True",'1',param_string)
                    param_string=re.sub("False",'',param_string)
                    param_string=re.sub("None",'',param_string)
                    pstring+=f+'='+param_string+'&'
                else:
                    pstring+=f+'='+str(pdict[f])+'&'
            else:
                pstring+=f+'=&'
        pstring=pstring.strip('&').encode('utf8')
        # print(bytearray(self.secret_key.encode('utf-8')))
        # now with correctly ordered param string, calculate hash
        # print(self.secret_key)
        # self.secret_key = self.secret_key.encode('utf8')
        # print(self.secret_key)
        phash = hmac.new(self.secret_key, pstring, hashlib.sha1).hexdigest()
        return phash

    def _private_request(self,post_data):
        #fill in common post_data parameters
        tonce=self._get_tonce()
        post_data['tonce']=tonce
        post_data['accesskey']=self.access_key.decode()
        post_data['requestmethod']='post'
        # If ID is not passed as a key of post_data, just use tonce
        if not 'id' in post_data:
            post_data['id']=tonce
        pd_hash=self._get_params_hash(post_data)
        # must use b64 encode
        # print(self.access_key)
        # print(pd_hash)
        # print()
        # auth_string='Basic '+base64.b64encode(self.access_key+':'+pd_hash)
        auth_string=b'Basic '+base64.b64encode(self.access_key + b":" + pd_hash.encode('utf-8'))
        auth_string=auth_string.decode()
        # print(auth_string)
        headers={'Authorization':auth_string,'Json-Rpc-Tonce':tonce}

        #post_data dictionary passed as JSON
        # print(post_data)
        self.conn.request("POST",'/api_trade_v1.php',json.dumps(post_data),headers)
        response = self.conn.getresponse()

        # check response code, ID, and existence of 'result' or 'error'
        # before passing a dict of results
        if response.status == 200:
            # this might fail if non-json data is returned
            #the orginal currency_symbol start "\\u" in bad utf8 with will be replaced by "currency_symbol"
            resp_dict = json.loads(response.read().decode('utf-8').replace("\\u", "currency_symbol"))
            # The id's may need to be used by the calling application,
            # but for now, check and discard from the return dict
            if str(resp_dict['id']) == str(post_data['id']):
                if 'result' in resp_dict:
                    # print(resp_dict['result'])
                    return resp_dict['result']
                elif 'error' in resp_dict:
                    # print("error")
                    return resp_dict['error']
        else:
            # not great error handling....
            print("status:",response.status)
            print("reason:",response.reason)

        return None

    def get_account_info(self,post_data={}):
        post_data['method']='getAccountInfo'
        post_data['params']=[]
        return self._private_request(post_data)

    def get_market_depth2(self,limit=10, market="btccny", post_data={}):
        post_data['method']='getMarketDepth2'
        post_data['params']=[limit, market]
        return self._private_request(post_data)

    def buy(self, price, amount, market="btccny", post_data={}):
        amountStr = "{0:.4f}".format(round(amount,4))
        post_data['method']='buyOrder2'
        if price == None:
            priceStr = None
        else:
            priceStr = "{0:.4f}".format(round(price,4))
        post_data['params']=[priceStr, amountStr, market]
        return self._private_request(post_data)

    def sell(self, price, amount, market="btccny", post_data={}):
        amountStr = "{0:.4f}".format(round(amount,4))
        post_data['method']='sellOrder2'
        if price == None:
            priceStr = None
        else:
            priceStr = "{0:.4f}".format(round(price,4))
        post_data['params']=[priceStr, amountStr, market]
        return self._private_request(post_data)

    def cancel(self,order_id, market = "btccny", post_data={}):
        post_data['method']='cancelOrder'
        post_data['params']=[order_id, market]
        return self._private_request(post_data)

    def request_withdrawal(self,currency,amount,post_data={}):
        post_data['method']='requestWithdrawal'
        post_data['params']=[currency,amount]
        return self._private_request(post_data)

    def get_deposits(self,currency='BTC',pending=True,post_data={}):
        post_data['method']='getDeposits'
        post_data['params']=[currency,pending]
        return self._private_request(post_data)

    def get_orders(self,id=None,open_only=True,market="btccny",details=True,post_data={}):
        # this combines getOrder and getOrders
        if id is None:
            post_data['method']='getOrders'
            post_data['params']=[open_only, market]
        else:
            post_data['method']='getOrder'
            post_data['params']=[id, market,details]
        return self._private_request(post_data)

    def get_withdrawals(self,id='BTC',pending=True,post_data={}):
        # this combines getWithdrawal and getWithdrawals
        try:
            id = int(id)
            post_data['method']='getWithdrawal'
            post_data['params']=[id]
        except:
            post_data['method']='getWithdrawals'
            post_data['params']=[id,pending]
        return self._private_request(post_data)

    def get_transactions(self,trans_type='all',limit=10,post_data={}):
        post_data['method']='getTransactions'
        post_data['params']=[trans_type,limit]
        return self._private_request(post_data)

    def get_archived_order(self,id,market='btccny',withdetail=False,post_data={}):
    	post_data['method']='getArchivedOrder'
    	post_data['params']=[id,market,withdetail]
    	return self._private_request(post_data)

    def get_archived_orders(self,market='btccny',limit=200,less_than_order_id=0,withdetail=False,post_data={}):
    	post_data['method']='getArchivedOrders'
    	post_data['params']=[market,limit,less_than_order_id,withdetail]
    	return self._private_request(post_data)
