import firebase_admin
from firebase_admin import credentials, firestore, storage

cred = credentials.Certificate('./credentials.json')
firebase_admin.initialize_app(cred, {
    'storageBucket': 'fast-kyc.appspot.com'
})

db = firestore.client()

bucket = storage.bucket()

def create_new_account():
    doc_ref = db.collection('accounts').add({})
    print("New account created with id {0}.".format(doc_ref[1].id))
    return doc_ref[1].id

def upload_file_to_storage(file_path, file_name):
    blob = bucket.blob(file_name)
    with open(file_path, "rb") as file:
        blob.upload_from_file(file, content_type='image/jpeg')
    print("File {0} uploaded.".format(file_name))
    return blob.public_url

def create_idv_results(account_id, idv_results):
    db.collection('accounts').document(account_id).update({'idv_results': idv_results})
    print("IDV results created for account {0}.".format(account_id))

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

def update_id(account_id, file_url):
    db.collection('accounts').document(account_id).update({'id_': file_url})
    print("ID document image updated for account {0} at url {1}".format(account_id, file_url))

# Tests:
# account_id = create_new_account()
# update_name(account_id, 'Sayak')
# update_address(account_id, 'Kolkata')
# update_email(account_id, 'sayak@gmail.com')
# update_ssn(account_id, '123456789')