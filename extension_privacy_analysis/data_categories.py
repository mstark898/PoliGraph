"""
Data category mapping for extension privacy analysis.

Maps PoliGraph data types to the 7 analysis categories:
1. PII (Personally Identifiable Information)
2. Financial/Payment Data
3. Authentication Data
4. Location Data
5. Web History Data
6. User Activity Data
7. Website Content Data
"""

from enum import Enum
from typing import Set


class DataCategory(Enum):
    """The 7 main data categories for analysis."""
    PII = "pii"
    FINANCIAL = "financial"
    AUTHENTICATION = "authentication"
    LOCATION = "location"
    WEB_HISTORY = "web_history"
    USER_ACTIVITY = "user_activity"
    WEBSITE_CONTENT = "website_content"


# Mapping from PoliGraph data types to our 7 categories
CATEGORY_MAPPINGS = {
    DataCategory.PII: {
        # Core PII
        "personal information",
        "personal identifier",
        "personally identifiable information",
        "personal data",
        "pii",

        # Names
        "name",
        "real name",
        "full name",
        "first name",
        "last name",
        "maiden name",
        "nickname",
        "username",
        "account name",
        "display name",
        "user name",

        # Contact information
        "email address",
        "email",
        "phone number",
        "mobile phone number",
        "telephone number",
        "postal address",
        "home address",
        "shipping address",
        "billing address",
        "street address",
        "address",
        "zip code",
        "postal code",
        "contact information",
        "contact details",

        # Government IDs
        "government identifier",
        "social security number",
        "ssn",
        "passport number",
        "driver's license number",
        "driver license number",
        "national id",
        "identification number",

        # Demographic information
        "age",
        "date of birth",
        "birthday",
        "birthdate",
        "gender",
        "sex",
        "race",
        "ethnicity",
        "nationality",
        "marital status",
        "employment status",

        # Device identifiers (when linked to person)
        "device identifier",
        "device id",
        "unique device identifier",
        "udid",
        "imei",
        "mac address",
        "hardware identifier",
        "advertising identifier",
        "advertising id",
        "idfa",
        "android advertising id",

        # Profile information
        "profile photo",
        "profile picture",
        "avatar",
        "user profile",
        "account information",

        # Biometrics
        "biometric data",
        "biometrics",
        "fingerprint",
        "face recognition data",
        "voiceprint",
        "voice recording",

        # Communications (personal)
        "personal communications",
        "email content",
        "message content",
        "sms content",
        "chat messages",
        "communications",
    },

    DataCategory.FINANCIAL: {
        # Payment instruments
        "financial information",
        "payment information",
        "financial data",
        "payment data",
        "credit card number",
        "credit card",
        "debit card number",
        "debit card",
        "card number",
        "cvv",
        "cvc",
        "card security code",
        "card verification code",
        "expiration date",
        "card expiration",

        # Bank accounts
        "bank account number",
        "bank account",
        "routing number",
        "iban",
        "swift code",

        # Transaction data
        "transaction history",
        "transaction data",
        "transactions",
        "purchase history",
        "payment history",
        "billing history",
        "order history",
        "shopping history",
        "purchase data",

        # Financial standing
        "credit rating",
        "credit score",
        "credit report",
        "financial statements",
        "income",
        "salary",
    },

    DataCategory.AUTHENTICATION: {
        # Passwords and credentials
        "password",
        "passwords",
        "passcode",
        "passphrase",
        "passkey",
        "credentials",
        "login credentials",
        "authentication credentials",
        "login information",
        "authentication information",
        "authentication data",

        # Tokens and keys
        "authentication token",
        "auth token",
        "access token",
        "api key",
        "session token",
        "security token",

        # Security questions
        "security question",
        "security questions",
        "security answer",
        "secret question",

        # PIN
        "pin",
        "pin number",
        "personal identification number",

        # 2FA/MFA
        "two-factor authentication",
        "2fa code",
        "mfa code",
        "verification code",
        "one-time password",
        "otp",
    },

    DataCategory.LOCATION: {
        # General location
        "location",
        "location data",
        "location information",
        "geolocation",
        "geographic location",
        "geographical location",
        "geo-location",

        # Precise location
        "precise location",
        "precise geolocation",
        "gps coordinates",
        "gps location",
        "gps data",
        "latitude",
        "longitude",
        "coordinates",

        # Coarse location
        "coarse location",
        "coarse geolocation",
        "approximate location",
        "region",
        "city",
        "state",
        "country",
        "country of residence",
        "city-level location",

        # Network-based location
        "ip address",
        "ip-based location",
        "wifi location",
        "cell tower location",

        # Movement/tracking
        "travel history",
        "location history",
        "movement data",
    },

    DataCategory.WEB_HISTORY: {
        # Browsing data
        "browsing history",
        "web history",
        "browser history",
        "browsing data",
        "internet history",

        # Search data
        "search history",
        "search queries",
        "search terms",

        # Page visits
        "page visits",
        "visit history",
        "visited pages",
        "websites visited",
        "visit timestamps",
        "access times",
        "pages visited",

        # Cookies and tracking
        "cookies",
        "cookie data",
        "web beacons",
        "tracking pixels",
        "pixel tags",

        # HTTP data
        "http headers",
        "user agent",
        "referrer",
        "referer",

        # Log data
        "log data",
        "access logs",
    },

    DataCategory.USER_ACTIVITY: {
        # Interaction data
        "user activity",
        "user activity data",
        "online activity",
        "internet activity",
        "network activity",
        "activity data",
        "user behavior",

        # Click/mouse data
        "click data",
        "clicks",
        "mouse position",
        "mouse movements",
        "scroll data",
        "scroll position",

        # Keystroke data
        "keystroke logging",
        "keystroke data",
        "keystrokes",
        "typing data",

        # Network monitoring
        "network monitoring",
        "traffic data",
        "network traffic",

        # Usage data
        "usage data",
        "usage information",
        "usage patterns",
        "interaction data",

        # Application usage
        "application list",
        "installed applications",
        "app usage",
        "extension list",
    },

    DataCategory.WEBSITE_CONTENT: {
        # Page content
        "website content",
        "web content",
        "page content",
        "site content",

        # Text content
        "text",
        "text content",
        "page text",

        # Media content
        "images",
        "sounds",
        "videos",
        "audio",
        "media",
        "media content",

        # Links
        "hyperlinks",
        "links",
        "urls",

        # Form data
        "form data",
        "form content",
        "form inputs",

        # Document content
        "document content",
        "documents",
        "files",
        "file content",
    },
}


# Chrome Web Store disclosure category to our category mapping
CHROME_DISCLOSURE_MAPPINGS = {
    "Personally identifiable information": DataCategory.PII,
    "Personal communications": DataCategory.PII,
    "Financial and payment information": DataCategory.FINANCIAL,
    "Authentication information": DataCategory.AUTHENTICATION,
    "Location": DataCategory.LOCATION,
    "Web history": DataCategory.WEB_HISTORY,
    "User activity": DataCategory.USER_ACTIVITY,
    "Website content": DataCategory.WEBSITE_CONTENT,
    "Health information": None,  # Not in our categories
}


def get_category_for_datatype(datatype: str) -> DataCategory | None:
    """
    Given a PoliGraph data type string, return which category it belongs to.
    Returns None if the data type doesn't fit any category.
    """
    datatype_lower = datatype.lower().strip()

    for category, datatypes in CATEGORY_MAPPINGS.items():
        if datatype_lower in datatypes:
            return category

    # Try partial matching for compound terms
    for category, datatypes in CATEGORY_MAPPINGS.items():
        for dt in datatypes:
            if dt in datatype_lower or datatype_lower in dt:
                return category

    return None


def get_datatypes_for_category(category: DataCategory) -> Set[str]:
    """Get all data types that belong to a given category."""
    return CATEGORY_MAPPINGS.get(category, set())


def parse_chrome_disclosure_categories(disclosure_text: str) -> Set[DataCategory]:
    """
    Parse Chrome Web Store disclosure text and return the set of data categories mentioned.
    """
    categories = set()

    for chrome_category, our_category in CHROME_DISCLOSURE_MAPPINGS.items():
        if chrome_category.lower() in disclosure_text.lower():
            if our_category is not None:
                categories.add(our_category)

    return categories


def get_category_display_name(category: DataCategory) -> str:
    """Get human-readable display name for a category."""
    names = {
        DataCategory.PII: "PII",
        DataCategory.FINANCIAL: "Financial",
        DataCategory.AUTHENTICATION: "Auth",
        DataCategory.LOCATION: "Location",
        DataCategory.WEB_HISTORY: "Web History",
        DataCategory.USER_ACTIVITY: "User Activity",
        DataCategory.WEBSITE_CONTENT: "Website Content",
    }
    return names.get(category, category.value)


if __name__ == "__main__":
    # Test the category mappings
    print("Data Category Mappings Summary")
    print("=" * 50)

    for category in DataCategory:
        datatypes = CATEGORY_MAPPINGS.get(category, set())
        print(f"\n{get_category_display_name(category)}: {len(datatypes)} data types")
        print(f"  Examples: {', '.join(list(datatypes)[:5])}...")

    # Test Chrome disclosure parsing
    print("\n" + "=" * 50)
    print("Testing Chrome Disclosure Parsing")

    test_disclosure = """
    handles the following:
    Personally identifiable information
    Financial and payment information
    Location
    Web history
    User activity
    Website content
    """

    categories = parse_chrome_disclosure_categories(test_disclosure)
    print(f"Found categories: {[get_category_display_name(c) for c in categories]}")
