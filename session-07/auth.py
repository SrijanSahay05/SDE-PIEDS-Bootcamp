"""
POST /register
    REQUEST:
    1. Full Name (two people can have the same name, so how will differentiate)
    2. email / userName / phone
    3. password (we will explore if this should a string or this should should be hashed before saving) || confirm_password
    RESPONSE:
    1. HTTP STATUS CODE : 200 | 500 | 429
    2. MSG: "User account registered"


POST /login
    1. userName
    2. password 

    1. ACCESS TOKEN
    2. REFRESH TOKEN
    3. USER (details)

/ask (authentication & authorization) [role: student | professor]
"""

