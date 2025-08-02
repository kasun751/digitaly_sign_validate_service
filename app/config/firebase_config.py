# # firebase_config.py
# import firebase_admin
# from firebase_admin import credentials, storage
#
# # Avoid re-initializing Firebase if already initialized
# if not firebase_admin._apps:
#     cred = credentials.Certificate("E:/Learning/testing_project_2/digitaly-sign-validate-service/app/config"
#                                    "/uvaexplore-firebase-adminsdk-fbsvc-9f8bd15cf5.json")
#     firebase_admin.initialize_app(cred, {
#         "storageBucket": "uvaexplore.firebasestorage.app"
#     })
