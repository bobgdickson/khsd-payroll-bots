# khsd-payroll-bots
Playwright based bots to assist payroll processing team.  All legacy Power Automate flows will be migrated here.  New functionality will be added as team requests and focus time allows.

# Uncheck Bot
Used to navigate PeopleSoft HCM and uncheck Ok to pay, Job Pay boxes for a list of emplids when the hours field is zero/blank.

## Setup
`Ctrl-Shift-P` and create new environment

```bash
pip install -r requirements.txt
```

Create `.env` file with:
- PEOPLESOFT_USERNAME
- PEOPLESOFT_PASSWORD
- PEOPLESOFT_ENV
- PEOPLESOFT_TEST_ENV

## Gather EMPLID List
Currently EMPLIDs are run manually, dynamic list creation will be implemented in the future.

## Run bot
```bash
 python -m app.bots.uncheck    
 ```
