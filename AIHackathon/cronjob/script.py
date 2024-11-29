import requests


def get_overdue_data_from_cases():
    # API endpoint
    url = "https://www.zohoapis.com/crm/v6/Cases/search?criteria=Status:equals:Overdue&fields=Tenant_Mobile,Days_Overdue,Status,Subject"

    # Authorization token
    access_token = "YOUR_ACCESS_TOKEN"

    # Headers
    headers = {
        "Authorization": f"Zoho-oauthtoken {access_token}",
        "Content-Type": "application/json",
        "Accept": "application/json"
    }

    # Making the GET request
    response = requests.get(url, headers=headers)
    print(response)
    # Checking the response
    if response.status_code == 200:
        print("Success!")
        print(response.json())  # Print response JSON
    else:
        print(f"Error: {response.status_code}")
        print(response.text)  # Print error details