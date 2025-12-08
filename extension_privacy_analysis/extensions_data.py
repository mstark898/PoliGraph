"""
Extension data definitions for privacy analysis pipeline.

This module contains the list of Chrome extensions to analyze, including:
- Extension IDs
- Privacy policy URLs
- Developer disclosure text (from Chrome Web Store)
"""

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class Extension:
    """Represents a Chrome extension for privacy analysis."""
    name: str
    extension_id: str
    privacy_policy_url: str
    developer_disclosure: str = ""
    chrome_webstore_url: str = field(init=False)

    def __post_init__(self):
        self.chrome_webstore_url = f"https://chromewebstore.google.com/detail/{self.extension_id}"


# Target extensions for analysis
EXTENSIONS = [
    Extension(
        name="PayPal Honey",
        extension_id="bmnlcjabgnpnenekpadlanbbkooimhnj",
        privacy_policy_url="https://www.joinhoney.com/privacy",
        developer_disclosure="""Privacy practices
PayPal Honey: Automatic Coupons & Cash Back has disclosed the following information regarding the collection and usage of your data. More detailed information can be found in the developer's privacy policy.

PayPal Honey: Automatic Coupons & Cash Back handles the following:
Personally identifiable information
For example: name, address, email address, age, or identification number

Financial and payment information
For example: transactions, credit card numbers, credit ratings, financial statements, or payment history

Authentication information
For example: passwords, credentials, security question, or personal identification number (PIN)

Website content
For example: text, images, sounds, videos, or hyperlinks

Web history
For example: browsing history, page visits or visit timestamps

User activity
For example: network monitoring, clicks, mouse position, scroll, or keystroke logging

This developer declares that your data is
Not being sold to third parties, outside of the approved use cases
Not being used or transferred for purposes that are unrelated to the item's core functionality
Not being used or transferred to determine creditworthiness or for lending purposes"""
    ),

    Extension(
        name="Capital One Shopping",
        extension_id="nenlahapcbofgnanklpelkaejcehkggg",
        privacy_policy_url="https://capitaloneshopping.com/privacy",
        developer_disclosure="""Privacy practices
Capital One Shopping: Save Now has disclosed the following information regarding the collection and usage of your data. More detailed information can be found in the developer's privacy policy.

Capital One Shopping: Save Now handles the following:
Personally identifiable information
For example: name, address, email address, age, or identification number

Financial and payment information
For example: transactions, credit card numbers, credit ratings, financial statements, or payment history

Web history
For example: browsing history, page visits or visit timestamps

User activity
For example: network monitoring, clicks, mouse position, scroll, or keystroke logging

Website content
For example: text, images, sounds, videos, or hyperlinks

This developer declares that your data is
Not being sold to third parties, outside of the approved use cases
Not being used or transferred for purposes that are unrelated to the item's core functionality
Not being used or transferred to determine creditworthiness or for lending purposes"""
    ),

    Extension(
        name="Keepa",
        extension_id="neebplgakaahbhdphmkckjjcegoiijjo",
        privacy_policy_url="https://keepa.com/#!disclaimer",
        developer_disclosure="""Privacy practices
Keepa - Amazon Price Tracker has disclosed the following information regarding the collection and usage of your data. More detailed information can be found in the developer's privacy policy.

Keepa - Amazon Price Tracker handles the following:
User activity
For example: network monitoring, clicks, mouse position, scroll, or keystroke logging

Website content
For example: text, images, sounds, videos, or hyperlinks

This developer declares that your data is
Not being sold to third parties, outside of the approved use cases
Not being used or transferred for purposes that are unrelated to the item's core functionality
Not being used or transferred to determine creditworthiness or for lending purposes"""
    ),

    Extension(
        name="Coupert",
        extension_id="mfidniedemcgceagapgdekdbmanojomk",
        privacy_policy_url="https://www.coupert.com/privacy",
        developer_disclosure="""Privacy practices
Coupert - Automatic Coupon Finder & Cashback has disclosed the following information regarding the collection and usage of your data. More detailed information can be found in the developer's privacy policy.

Coupert - Automatic Coupon Finder & Cashback handles the following:
Personally identifiable information
For example: name, address, email address, age, or identification number

Web history
For example: browsing history, page visits or visit timestamps

User activity
For example: network monitoring, clicks, mouse position, scroll, or keystroke logging

Website content
For example: text, images, sounds, videos, or hyperlinks

This developer declares that your data is
Not being sold to third parties, outside of the approved use cases
Not being used or transferred for purposes that are unrelated to the item's core functionality
Not being used or transferred to determine creditworthiness or for lending purposes"""
    ),

    Extension(
        name="Rakuten",
        extension_id="chhjbpecpncaggjpdakmflnfcopglcmi",
        privacy_policy_url="https://www.rakuten.com/help/article/privacy-policy-360002101688",
        developer_disclosure="""Privacy practices
Rakuten: Get Cash Back For Shopping has disclosed the following information regarding the collection and usage of your data. More detailed information can be found in the developer's privacy policy.

Rakuten: Get Cash Back For Shopping handles the following:
Personally identifiable information
For example: name, address, email address, age, or identification number

Location
For example: region, IP address, GPS coordinates, or information about things near the user's device

Web history
For example: browsing history, page visits or visit timestamps

User activity
For example: network monitoring, clicks, mouse position, scroll, or keystroke logging

Website content
For example: text, images, sounds, videos, or hyperlinks

This developer declares that your data is
Not being sold to third parties, outside of the approved use cases
Not being used or transferred for purposes that are unrelated to the item's core functionality
Not being used or transferred to determine creditworthiness or for lending purposes"""
    ),

    Extension(
        name="The Camelizer",
        extension_id="ghnomdcacenbmilgjigehppbamfndblo",
        privacy_policy_url="https://camelcamelcamel.com/privacy",
        developer_disclosure="""Privacy practices
The Camelizer has disclosed the following information regarding the collection and usage of your data. More detailed information can be found in the developer's privacy policy.

The Camelizer handles the following:
Website content
For example: text, images, sounds, videos, or hyperlinks

This developer declares that your data is
Not being sold to third parties, outside of the approved use cases
Not being used or transferred for purposes that are unrelated to the item's core functionality
Not being used or transferred to determine creditworthiness or for lending purposes"""
    ),

    Extension(
        name="CouponBirds",
        extension_id="pnedebpjhiaidlbbhmogocmffpdolnek",
        privacy_policy_url="https://www.couponbirds.com/privacy-policy",
        developer_disclosure="""Privacy practices
CouponBirds - SmartCoupon Coupon Finder has disclosed the following information regarding the collection and usage of your data. More detailed information can be found in the developer's privacy policy.

CouponBirds - SmartCoupon Coupon Finder handles the following:
Personally identifiable information
For example: name, address, email address, age, or identification number

Web history
For example: browsing history, page visits or visit timestamps

User activity
For example: network monitoring, clicks, mouse position, scroll, or keystroke logging

Website content
For example: text, images, sounds, videos, or hyperlinks

This developer declares that your data is
Not being sold to third parties, outside of the approved use cases
Not being used or transferred for purposes that are unrelated to the item's core functionality
Not being used or transferred to determine creditworthiness or for lending purposes"""
    ),

    Extension(
        name="Shein Coupon Finder",
        extension_id="janmadmcipjiaoenfkimihamjfipgmee",
        privacy_policy_url="https://www.shein.com/Privacy-Security-Policy-a-282.html",
        developer_disclosure="""Privacy practices
Shein Coupon Finder has disclosed the following information regarding the collection and usage of your data. More detailed information can be found in the developer's privacy policy.

Shein Coupon Finder handles the following:
Website content
For example: text, images, sounds, videos, or hyperlinks

This developer declares that your data is
Not being sold to third parties, outside of the approved use cases
Not being used or transferred for purposes that are unrelated to the item's core functionality
Not being used or transferred to determine creditworthiness or for lending purposes"""
    ),

    Extension(
        name="Cently",
        extension_id="kegphgaihkjoophpabchkmpaknehfamb",
        privacy_policy_url="https://couponfollow.com/privacy",
        developer_disclosure="""Privacy practices
Cently: Automatic Coupons + Cashback for Free has disclosed the following information regarding the collection and usage of your data. More detailed information can be found in the developer's privacy policy.

Cently: Automatic Coupons + Cashback for Free handles the following:
Personally identifiable information
For example: name, address, email address, age, or identification number

Web history
For example: browsing history, page visits or visit timestamps

User activity
For example: network monitoring, clicks, mouse position, scroll, or keystroke logging

Website content
For example: text, images, sounds, videos, or hyperlinks

This developer declares that your data is
Not being sold to third parties, outside of the approved use cases
Not being used or transferred for purposes that are unrelated to the item's core functionality
Not being used or transferred to determine creditworthiness or for lending purposes"""
    ),

    Extension(
        name="AliExpress Coupon Finder",
        extension_id="adanomdlalebngcphfbknoglbcdcbchb",
        privacy_policy_url="",  # No explicit privacy policy URL found
        developer_disclosure="""Privacy practices
The developer has disclosed that it will not collect or use your data.

This developer declares that your data is
Not being sold to third parties, outside of the approved use cases
Not being used or transferred for purposes that are unrelated to the item's core functionality
Not being used or transferred to determine creditworthiness or for lending purposes"""
    ),

    Extension(
        name="Grammarly",
        extension_id="kbfnbcaeplbcioakkpcpgfkobkghlhen",
        privacy_policy_url="https://www.grammarly.com/privacy-policy",
        developer_disclosure="""Privacy practices
Grammarly: AI Writing Assistant and Grammar Checker App has disclosed the following information regarding the collection and usage of your data. More detailed information can be found in the developer's privacy policy.

Grammarly: AI Writing Assistant and Grammar Checker App handles the following:
Personally identifiable information
For example: name, address, email address, age, or identification number

Personal communications
For example: emails, texts, or chat messages

Location
For example: region, IP address, GPS coordinates, or information about things near the user's device

User activity
For example: network monitoring, clicks, mouse position, scroll, or keystroke logging

Website content
For example: text, images, sounds, videos, or hyperlinks

This developer declares that your data is
Not being sold to third parties, outside of the approved use cases
Not being used or transferred for purposes that are unrelated to the item's core functionality
Not being used or transferred to determine creditworthiness or for lending purposes"""
    ),

    Extension(
        name="AdBlock",
        extension_id="gighmmpiobklfepjocnamgkkbiglidom",
        privacy_policy_url="https://getadblock.com/privacy/",
        developer_disclosure="""Privacy practices
The developer has disclosed that it will not collect or use your data.

This developer declares that your data is
Not being sold to third parties, outside of the approved use cases
Not being used or transferred for purposes that are unrelated to the item's core functionality
Not being used or transferred to determine creditworthiness or for lending purposes"""
    ),

    Extension(
        name="Hola VPN",
        extension_id="gkojfkhlekighikafcpjkiklfbnlmeio",
        privacy_policy_url="https://hola.org/legal/privacy",
        developer_disclosure="""Privacy practices
Hola VPN - Your Website Unblocker has disclosed the following information regarding the collection and usage of your data. More detailed information can be found in the developer's privacy policy.

Hola VPN - Your Website Unblocker handles the following:
Personally identifiable information
For example: name, address, email address, age, or identification number

Location
For example: region, IP address, GPS coordinates, or information about things near the user's device

Web history
For example: browsing history, page visits or visit timestamps

User activity
For example: network monitoring, clicks, mouse position, scroll, or keystroke logging

Website content
For example: text, images, sounds, videos, or hyperlinks

This developer declares that your data is
Not being sold to third parties, outside of the approved use cases
Not being used or transferred for purposes that are unrelated to the item's core functionality
Not being used or transferred to determine creditworthiness or for lending purposes"""
    ),
]


def get_extension_by_name(name: str) -> Optional[Extension]:
    """Get an extension by its name."""
    for ext in EXTENSIONS:
        if ext.name.lower() == name.lower():
            return ext
    return None


def get_extension_by_id(extension_id: str) -> Optional[Extension]:
    """Get an extension by its Chrome Web Store ID."""
    for ext in EXTENSIONS:
        if ext.extension_id == extension_id:
            return ext
    return None


if __name__ == "__main__":
    # Print summary of all extensions
    print(f"Total extensions: {len(EXTENSIONS)}\n")
    for ext in EXTENSIONS:
        print(f"- {ext.name}")
        print(f"  ID: {ext.extension_id}")
        print(f"  Privacy Policy: {ext.privacy_policy_url}")
        print()
