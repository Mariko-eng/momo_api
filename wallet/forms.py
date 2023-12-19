# """
# Written by Keeya Emmanuel Lubowa
# On 1oth Sept, 2022
# Email ekeeya@oddjobs.tech
# """
# from django import forms
# # from smartmin.users.models import is_password_complex
# # from smartmin.users.views import UserForm

# from mondo.utils.fields import SelectWidget, InputWidget
# from mondo.utils.ussd import standard_urn
# from mondo.wallet.models import WalletAccount, User, TELECOMS, ACCOUNT_TYPES


# class UserRegisterForm(forms.ModelForm):
#     def __init__(self, org, *args, **kwargs):
#         super().__init__(*args, **kwargs)
#         self.org = org

#     password = forms.CharField(
#         widget=InputWidget(attrs={"password": True}))

#     confirm_password = forms.CharField(
#         widget=InputWidget(attrs={"password": True}))

#     account_type = forms.CharField(
#         widget=SelectWidget(
#             choices=ACCOUNT_TYPES
#         )
#     )
#     telephone = forms.CharField(
#         widget=InputWidget()
#     )

#     def clean_password(self):
#         password = self.cleaned_data['password']

#         # if they specified a new password
#         if password and not is_password_complex(password):
#             raise forms.ValidationError("Passwords must have at least 8 characters, including one uppercase, "
#                                         "one lowercase and one number")

#         return password

#     def clean_telephone(self):
#         try:
#             standard = standard_urn(self.cleaned_data["telephone"])
#             return standard
#         except Exception as error:
#             raise forms.ValidationError(str(error))

#     def clean_email(self):
#         email = self.cleaned_data["email"]
#         if email:
#             if User.objects.filter(email__iexact=email):
#                 raise forms.ValidationError("That email address is already used")

#         return email.lower()

#     def save(self, commit=True):
#         """
#         Overloaded so we can save any new password that is included.
#         """
#         confirm_password = self.cleaned_data['confirm_password']
#         password = self.cleaned_data['password']
#         if password != confirm_password:
#             raise forms.ValidationError("Entered passwords do not match")
#         is_new_user = self.instance.pk is None
#         instance = super().save(commit=False)
#         # new users should be made active by default
#         if is_new_user:
#             instance.is_active = True
#         if password:
#             instance.set_password(password)
#         instance.save()
#         return instance

#     class Meta:
#         model = User
#         exclude = ["is_active", "is_staff", "groups", "is_superuser", "user_permissions", "date_joined", "last_login", "username"]
#         widgets = {
#             "first_name": InputWidget(),
#             "last_name": InputWidget(),
#             "email": InputWidget(attrs={"type": "email"}),
#         }


# class AccountForm(forms.ModelForm):
#     def __init__(self, org, *args, **kwargs):
#         super().__init__(*args, **kwargs)
#         self.org = org

#     class Meta:
#         model = WalletAccount
#         exclude = ["is_active"]
#         widgets = {"account_type": SelectWidget(),
#                    "user": SelectWidget(),
#                    "telecom": SelectWidget(),
#                    "available_balance": InputWidget(attrs={"type": "number"}),
#                    "actual_balance": InputWidget(attrs={"type": "number"})
#                    }
