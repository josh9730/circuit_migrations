from napalm.base import get_network_driver
from jnpr.junos import Device
from atlassian import Jira
import keyring
import pyotp

"""
Keyring:
- keyring set jira url {{ URL }}
- keyring set mfa {{ USERNAME }}
- keyring set otp {{ USERNAME }}
"""


class Login:
    def __init__(self):

        # credentials, via keyring
        self.cas_user = keyring.get_password("cas", "user")
        self.cas_pass = keyring.get_password("cas", self.cas_user)
        self.jira_url = keyring.get_password("jira", "url")

        self.mfa_user = self.cas_user + "mfa"
        self.mfa_pass = keyring.get_password("mfa", self.mfa_user)
        self.otp = pyotp.TOTP(keyring.get_password("otp", self.mfa_user))

    def jira_login(self):
        """Returns Jira object, uses CAS credentials."""
        return Jira(
            url=self.jira_url,
            username=self.cas_user,
            password=self.cas_pass,
        )

    def napalm_connect(self, hostname, device_type):
        """Returns NAPALM object, uses MFA credentials."""
        driver = get_network_driver(device_type)
        return driver(
            hostname=hostname,
            username=self.mfa_user,
            password=self.mfa_pass + self.otp.now(),
            timeout=1000,
        )

    def pyez_connect(self, hostname):
        """Returns PyEZ object, uses MFA credentials."""
        return Device(
            host=hostname,
            user=self.mfa_user,
            passwd=self.mfa_pass + self.otp.now(),
        )
