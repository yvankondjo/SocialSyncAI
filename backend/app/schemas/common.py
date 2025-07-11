from enum import Enum

class UserRole(str, Enum):
    ADMIN = "admin"
    USER = "user"
    MODERATOR = "moderator"

class OrganizationType(str, Enum):
    BUSINESS = "business"
    NON_PROFIT = "non_profit"
    GOVERNMENT = "government"
    EDUCATIONAL = "educational"

class SocialPlatform(str, Enum):
    FACEBOOK = "facebook"
    TWITTER = "twitter"
    INSTAGRAM = "instagram"
    LINKEDIN = "linkedin"
    YOUTUBE = "youtube"
    TIKTOK = "tiktok" 