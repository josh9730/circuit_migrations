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
        jira = Jira(
            url=self.jira_url,
            username=self.cas_user,
            password=self.cas_pass,
        )
        return jira

    def napalm_connect(self, hostname, device_type):
        """Returns NAPALM object, uses MFA credentials."""
        driver = get_network_driver(device_type)
        connection = driver(
            hostname=hostname,
            username=self.mfa_user,
            password=self.mfa_pass + self.otp.now(),
        )
        return connection

    def pyez_connect(self, hostname):
        """Returns PyEZ object, uses MFA credentials."""
        connection = Device(
            host=hostname,
            user=self.mfa_user,
            passwd=self.mfa_pass + self.otp.now(),
        )
        return connection

    # def netmiko_connect(self, hostname, device_type):
    #     """Returns Netmiko object, uses MFA credentials."""
    #     connection = ConnectHandler(
    #         device_type=device_type,
    #         host=hostname,
    #         username=self.mfa_user,
    #         password=self.mfa_pass + self.otp.now(),
    #     )
    #     return connection

    # def ncc_connect(self, hostname):
    #     """Returns NCCLient object, uses MFA credentials."""
    #     connection = manager.connect(
    #         host=hostname,
    #         username=self.mfa_user,
    #         password=self.mfa_pass + self.otp.now(),
    #         timeout=120,
    #         hostkey_verify=False,
    #     )
    #     return connection
