from src.utils import sleep_with_progress_bar

accounts = [
    {"email": "", "password": "", "2FA": ""},
    {"email": "", "password": "", "2FA": ""},
    {"email": "", "password": "", "2FA": ""},
    {"email": "", "password": "", "2FA": ""},
    {"email": "", "password": "", "2FA": ""},
    {"email": "", "password": "", "2FA": ""},
]

accounts_copy = accounts.copy()


async def get_account():
    global accounts_copy

    if not accounts_copy:
        sleep_with_progress_bar(150)
        accounts_copy = accounts.copy()

    account = accounts_copy.pop(0)

    return account
