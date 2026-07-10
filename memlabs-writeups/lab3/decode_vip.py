import sys
import string
import base64

with open("./vip.txt","r") as f:
    ciphertext = f.read()

decoded_base64 = base64.b64decode(ciphertext)
plaintext = ""

for i in decoded_base64:
    plaintext += (chr(i^3))



print(plaintext)



