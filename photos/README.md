This code is hardly robust as Meetup.com presents different photo albums differently.
I didn't want to implement to handle all those cases neatly, so I temporarily altered the code without committing those here.
Please be aware if you decides to use my code.
In a happy case, this should download 80+% of all meetup photos.

# How to Use

1. Run `pip install -r requirements.txt`
1. Create `.env` file
1. Add
    ```
    USERNAME=<YOUR_MEETUP_USERNAME>
    PASSWORD=<YOUR_MEETUP_PASSWORD>
    MEETUP_URL=<YOUR_MEETUP_GROUP_HOME_URL>
    ```
1. Replace the values in `<...>`
1. Run `python photo_scrape.py`
