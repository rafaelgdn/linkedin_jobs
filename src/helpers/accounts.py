from src.utils import sleep_with_progress_bar

accounts = [
    # {"email": "ErginKaya733@gmail.com", "password": "Bn@#9262853856286", "2FA": "WAG6NVZNXL5RY6QTGTE52UF3ZL2VT6XG"},
    # {"email": "reysisaydan371@gmail.com", "password": "Bn@#9262853856286", "2FA": "L3NTQPHTRTJMG24OCMX5XAWMPNFMVJFI"},
    # {"email": "fevzidege286@gmail.com", "password": "Bn@#9262853856286", "2FA": "MNCBPX4MDSWTQJKAEQBGFWHYEEC5FPLL"},
    # {"email": "aysecansucinar592@gmail.com", "password": "Bn@#9262853856286", "2FA": "KMW2IJA5Z4X7CAPOEROPCY53B54R4OYK"},
    # {"email": "caneraskar491@gmail.com", "password": "Bn@#9262853856286", "2FA": "XZ3LLWVLV4OOII44C4AAT3UIBJTJOWDE"},
    {"email": "NusretAkay033@gmail.com", "password": "Bn@#9262853856286", "2FA": "CH7KWEZB3CPE3MIQETVDZABUZQSFBBSU"},
    {"email": "kezibanyediel468@gmail.com", "password": "Bn@#9262853856286", "2FA": "SIEMCWS2WOLFKEUVPF6P4F6WQNLXTZKA"},
    {"email": "OrhanSezer177@gmail.com", "password": "Bn@#9262853856286", "2FA": "O55GSPH6QAJGQGKUTAU4BANLJWEROYXW"},
    {"email": "tekinakdemir21@gmail.com", "password": "Bn@#9262853856286", "2FA": "O63JGN6ZQVOIMVM6CEVIPGCZCGUG7F62"},
    {"email": "tekinakdemir14@gmail.com", "password": "Bn@#9262853856286", "2FA": "65TQ33OVGPLVFZIGBS3ILIZMVFWNYOCD"},
    {"email": "necatikantar75@gmail.com", "password": "Bn@#9262853856286", "2FA": "DWY3SK7E2CFI2RVVAV4N6PHPTDJZWI7Q"},
    {"email": "sefacanbay79@gmail.com", "password": "Bn@#9262853856286", "2FA": "TZOPZC3ATHBFRRWXYO2RB24CTBTEO2FL"},
    {"email": "samedakbulut24@gmail.com", "password": "Bn@#9262853856286", "2FA": "LP4YTEVVFL6V44WNNU46OR5HGAMWTPS3"},
    {"email": "samedakbulut58@gmail.com", "password": "Bn@#9262853856286", "2FA": "KAFVMFCUS7MKW62EUZFBVD3DTFIK63OT"},
    {"email": "halimaybakan503@gmail.com", "password": "Bn@#9262853856286", "2FA": "N3F2ERTGMROABW2JVQYJEF2UOY3NE3X6"},
    {"email": "rukiyekaygusuz813@gmail.com", "password": "Bn@#9262853856286", "2FA": "KO2VX7ITJXVDY3GC4BKOZRQUTD2C2FYZ"},
]

accounts_copy = accounts.copy()


async def get_account():
    global accounts_copy

    if not accounts_copy:
        await sleep_with_progress_bar(300)
        accounts_copy = accounts.copy()

    account = accounts_copy.pop(0)

    return account
