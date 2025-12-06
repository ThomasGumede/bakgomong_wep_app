import re
from django.core.validators import URLValidator, RegexValidator, ValidationError, RegexValidator
from django.core.validators import RegexValidator
from django.core.exceptions import ValidationError

def validate_fcbk_link(value):
    url_validator = URLValidator()
    facebook_regex = r'^https?://(www\.)?facebook\.com/.*$'
    if re.match(facebook_regex, value) == None:
        raise ValidationError('Invalid Facebook profile link')
    
def validate_twitter_link(value):
    url_validator = URLValidator()
    twitter_regrex = r'^https?://(www\.)?twitter\.com/.*$'
    if re.match(twitter_regrex, value) == None:
        raise ValidationError('Invalid Twitter profile link')

def validate_insta_link(value):
    url_validator = URLValidator()
    instagram_regex = r'^https?://(www\.)?instagram\.com/.*$'
    if re.match(instagram_regex, value) == None:
        raise ValidationError('Invalid Instagram profile link')
    
def validate_in_link(value):
    url_validator = URLValidator()
    linkedin_regex = r'^https?://(www\.)?linkedin\.com/.*$'
    if re.match(linkedin_regex, value) == None:
        raise ValidationError('Invalid LinkedIn profile link')

def validate_rsa_phone(value):

    cleaned_value = value.replace(" ", "")
    pattern = r'^(\+27|0)[1-9][0-9]{8}$'
    
    if not re.match(pattern, cleaned_value):
        raise ValidationError('Enter a valid South African phone number (e.g. +27831234567 or 0831234567).')

