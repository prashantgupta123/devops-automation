# pip3 install pyjwt

import jwt
import datetime

# {"created_at":1741597965,"tags":null,"consumer":{"id":"bd18b225-a420-4d14-b52f-061d931d885f"},"id":"f0c21cdc-50bd-4b21-891d-3b1ef4c2143e","key":"4oskCMb9GvcHSG1JXRu6IkzuCARInEPY","algorithm":"HS256","secret":"XBLBrvswXdl0qBTRRWhQlqkc2kpMK7s8","rsa_public_key":null}

hours = 1

exp_time = datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(hours=hours)
# exp_time = datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(minutes=5)

print(exp_time)
print(exp_time.timestamp())

# Payload
payload = {
    "iss": "4oskCMb9GvcHSG1JXRu6IkzuCARInEPY",
    "exp": int(exp_time.timestamp())
}

# Encode token
token = jwt.encode(payload, "XBLBrvswXdl0qBTRRWhQlqkc2kpMK7s8", algorithm="HS256")
print(token)

# eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJZVlllbFFCZXBDVjJuT01wV1gzalJrdm42Z3B2ZWFEcyIsImV4cCI6MTc0MTM1ODI1Mn0.zma34jSBT2X-etSXvY0cf4MOdTB_BOxc5fFYGVUg8Mg

# Decode token
decoded = jwt.decode(token, "XBLBrvswXdl0qBTRRWhQlqkc2kpMK7s8", algorithms=["HS256"])
print(decoded)
