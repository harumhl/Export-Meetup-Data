# Export-Meetup-Data

Meetup is increasing its subscription fee by 80% in mid October 2024.
I've decided to sunset our org and migrate to a website and a Discord (since the website has been buggy and doesn't provide easy communication anyway).

I do want to export some previous event details for reference sake, but Meetup.com doesn't offer that.
So here's my attempt at making that happen.

I'm using ChatGPT to help me here so the coding standards may not be so great.

IF YOU DECIDE TO USE THIS, DON'T BE A CREEP AND SCRAPE DATA THAT YOU PROBABLY SHOULD NOT GATHER SO MUCH.
I DO NOT APPROVE SUCH USAGE.

# How to Use

1. Run `pip install -r requirements.txt`
1. Create `.env` file under `events` folder
1. Add
    ```
    USERNAME=<YOUR_MEETUP_USERNAME>
    PASSWORD=<YOUR_MEETUP_PASSWORD>
    MEETUP_URL=<YOUR_MEETUP_GROUP_HOME_URL>
    ```
1. Replace the values in `<...>`
1. Run `python events/meetup_scrape.py`