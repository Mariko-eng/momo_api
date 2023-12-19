import datetime
from django.utils import timezone


def is_access_token_expired(token):
    now = timezone.now().timestamp()
    modified_on = token.modified_on
    expires_in = token.expires_in
    valid_until = (modified_on + datetime.timedelta(seconds=expires_in)).timestamp()
    if now >= valid_until:
        token.expired = True
        token.save()
        return True
    else:
        return False