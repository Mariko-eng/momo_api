
from wallet.managers import MTN, AIRTEL
from wallet.models import PRODUCT, WalletAccount, WALLET, TELECOM, SYSTEM


class WalletActions:
    """
        Represents wallet actions
    """
    model = WalletAccount
    user = None
    product_or_app = None
    account_type = PRODUCT

    def __init__(self, telecom, **kwargs):
        self.telecom = telecom

        for kwarg in kwargs:
            setattr(self, kwarg, kwargs[kwarg])

    def get_product_wallet_account(self, product_or_app):
        if self.telecom == MTN:
            return self.model.accounts.get_account_by_product(product_or_app)
        else:
            return self.model.accounts.get_account_by_application(product_or_app)

    def get_user_wallet_account(self):
        return self.user.userprofile.wallet_account

    def get_user_telecom_account(self):
        return self.user.userprofile.telecom_account

    def create_user_accounts(self):
        """
            create a wallet account
        """
        product_app_options = dict()
        wallet_account_options = dict(account_type=WALLET)
        telecom_account_options = dict(account_type=TELECOM)
        if self.user:
            product_app_options.update(dict(user=self.user))
            wallet_account_options.update(dict(user=self.user, telecom=SYSTEM))
            telecom_account_options.update(dict(user=self.user, telecom=self.telecom))
            wallet_account = self.get_user_wallet_account()
            if not wallet_account:
                # we assume if one is missing then the other must be missing
                wallet_account = self.model.objects.create(**wallet_account_options)
                telecom_account = self.model.objects.create(**telecom_account_options)
            return wallet_account
        else:
            # If we do not have a user we must have a product
            if self.telecom == MTN:
                product_app_options.update(dict(product=self.product_or_app, account_type=self.account_type, telecom=MTN))
                account = self.get_product_wallet_account(self.product_or_app)
            else:
                product_app_options.update(dict(application=self.product_or_app, account_type=self.account_type,
                                                telecom=AIRTEL))
                account = self.get_product_wallet_account(self.product_or_app)
            return account if account else self.model.objects.create(**product_app_options)

