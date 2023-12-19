from abc import ABC


class BaseMomoProductAuth(ABC):
    """
        Represents a momo product
    """

    def create_user(self):
        """
            create an api user for momo api authentication
        """
        pass

    @staticmethod
    def get_user(api_user):
        """
            Get api created user
        """
        pass

    @staticmethod
    def generate_api_key(api_user):
        """
            generate api key
        """
        pass

    @staticmethod
    def generate_access_token(api_user, product_name, token_type):
        """
            generate access token
        """
        pass

    def bc_authorize(self, api_user, product_name):
        """
            This operation is uder to claim a consent for the requested scopes
        """
        pass
