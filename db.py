import firebase_admin
from firebase_admin import credentials, firestore

cred = credentials.Certificate('./credentials.json')
firebase_admin.initialize_app(cred)

db = firestore.client()

def create_new_account():
    doc_ref = db.collection('accounts').add({})
    print("New account created with id {0}.".format(doc_ref[1].id))
    return doc_ref[1].id

def update_name(account_id, name):
    db.collection('accounts').document(account_id).update({'name': name})
    print("Name updated for account {0} to {1}.".format(account_id, name))

def update_address(account_id, address):
    db.collection('accounts').document(account_id).update({'address': address})
    print("Address updated for account {0} to {1}.".format(account_id, address))

def update_email(account_id, email):
    db.collection('accounts').document(account_id).update({'email': email})
    print("Email updated for account {0} to {1}.".format(account_id, email))

def update_ssn(account_id, ssn):
    db.collection('accounts').document(account_id).update({'ssn': ssn})
    print("SSN updated for account {0} to {1}.".format(account_id, ssn))

def update_id(account_id, image):
    db.collection('accounts').document(account_id).update({'encoded_id_img': image})
    print("Encoded ID document image uploaded for account {0}.".format(account_id))

# Tests:
# account_id = create_new_account()
# update_name(account_id, 'Sayak')
# update_address(account_id, 'Kolkata')
# update_email(account_id, 'sayak@gmail.com')
# update_ssn(account_id, '123456789')