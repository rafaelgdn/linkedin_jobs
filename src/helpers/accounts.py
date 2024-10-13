# from src.utils import sleep_with_progress_bar

accounts = [
    # {"email": "thiviergeyamal@gmail.com", "password": "qxkcuhjmym96t5", "2FA": "WLXFUH7O23ACQBKYAS42LCA7VHQ2RDHW"},
    # {"email": "moodtrevino9@gmail.com", "password": "9z7xq0fgh:9z7xq0fgh", "2FA": "G4BCVPS6B5CWE7RNCQOCKHN3RAQCBYXZ"},
    # {"email": "rafaeldecarvalho.ps@gmail.com", "password": "Rafa2404#linkedin", "2FA": None},
    {"email": "asavcasfas@hotmail.com", "password": "zqjfm3E$259", "2FA": None},
]

accounts_copy = accounts.copy()


async def get_account():
    global accounts_copy

    if not accounts_copy:
        # sleep_with_progress_bar(150)
        accounts_copy = accounts.copy()

    account = accounts_copy.pop(0)

    return account
