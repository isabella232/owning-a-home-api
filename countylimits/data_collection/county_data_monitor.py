import os

from difflib import ndiff

import requests
from bs4 import BeautifulSoup as bs
from django.core.mail import send_mail

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
CENSUS_CHANGELOG = 'https://www.census.gov/geo/reference/county-changes.html'
LAST_CHANGELOG = '{}/last_changelog.html'.format(BASE_DIR)
CHANGELOG_ID = 'tab_2010'

changelog_response = requests.get(CENSUS_CHANGELOG)
soup = bs(changelog_response.text, 'lxml')
current_changelog = soup.find("div", {"id": CHANGELOG_ID}).text

with open(LAST_CHANGELOG, 'r') as f:
    base_changelog = f.read()


def get_lines(changelog):
    return [line.strip() for line in changelog.split('\n') if line]


def check_for_county_changes(email=None):
    """
    Check the census county changelog against a local copy of the last log
    to see whether updates have been added. If changes are detected,
    note the change and update our local 'last_changelog.html' file.
    """
    base_lines = get_lines(base_changelog)
    current_lines = get_lines(current_changelog)
    if base_lines == current_lines:
        msg = 'No county changes found, no emails sent.'
        return msg
    else:
        msg = ('County changes need to be checked at {}\n'
               'These changes were detected:'.format(CENSUS_CHANGELOG))
        with open(LAST_CHANGELOG, 'w') as f:
            f.write(current_changelog)
        diffsets = []
        diffset = ndiff(base_lines, current_lines)
        diffsets.append(
            d for d in diffset if d.startswith('- ') or d.startswith('+ '))
        for diffsett in diffsets:
            for diff in diffsett:
                msg += '\n{}'.format(diff)
        msg += "\n\nOur 'last_changelog.html' file has been updated."
        if email:
            send_mail(
                'Owning a Home alert: Change detected in census county data',
                msg,
                'tech@cfpb.gov',
                email,
                fail_silently=False
            )

        return (
            "Emails were sent to {} with the following message: \n\n"
            "{}".format(", ".join(email), msg)
        )
