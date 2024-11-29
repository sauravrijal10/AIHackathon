# import logging
from celery import shared_task

# logger = logging.getLogger(__name__)

# @shared_task(name='cronjob.task.my_scheduled_task')
# def my_scheduled_task():
#     print("This task runs every every day.")

# # from celery import Celery

# # app = Celery('cronjob')

# # @app.task
# # def my_scheduled_task():
# #     print("Task is running!")
import requests
from dotenv import load_dotenv
import pymysql
from pymysql.err import OperationalError
import os
import json


# Load environment variables from .env file
load_dotenv()


def format_invoice_string(invoice_data, phone):
   date_paid = invoice_data["datePaid"] if invoice_data["datePaid"] else "not paid yet"
   return (
       f"Phone: {phone}\n"
       f"Context: \n"
       f"Invoiceid: {invoice_data['displayId']}\n"
       f"status: {invoice_data['status']}\n"
       f"Invoice created on: {invoice_data['dateCreated']}\n"
       f"Invoice paid date: {date_paid}\n"
       f"Plan name for the invoice: {invoice_data['planName']}\n"
       f"Due date to pay invoice: {invoice_data['dueDate']}\n"
   )


def extract_invoice_data(invoice):
   return {
       "id": invoice["id"],
       "displayId": invoice["displayId"],
       "dateCreated": invoice["dateCreated"],
       "dueDate": invoice["dueDate"],
       "amount": invoice["amount"],
       "status": invoice["status"],
       "datePaid": invoice["datePaid"],
       "planName": invoice["items"][0]["subscription"]["plan"]["name"] if invoice["items"] else None
   }


def get_overdue_data_from_cases():
   url = "https://www.zohoapis.com/crm/v6/Cases/search?criteria=Status:equals:Overdue&fields=Tenant_Mobile,Days_Overdue,Status,Subject"
   access_token = os.getenv("ZOHO_AUTHORIZATION_TOKEN")
   headers = {
       "Authorization": f"Zoho-oauthtoken {access_token}",
       "Content-Type": "application/json",
       "Accept": "application/json"
   }
   response = requests.get(url, headers=headers)
   if response.status_code == 200:
       return response.json()
   else:
       print(f"Error: {response.status_code}")
       return None


def get_tenant_mobiles(data):
   tenant_mobiles = [item['Tenant_Mobile'] for item in data['data'] if item['Tenant_Mobile']]
   return tenant_mobiles


def get_user_id_by_phone(phone):
   try:
       db_config = {
           'user': 'root',
           'password': 'speedrent',
           'host': '127.0.0.1',
           'port': 3307,
           'database': 'speedmanage_beta'
       }
       connection = pymysql.connect(
           user=db_config['user'],
           password=db_config['password'],
           host=db_config['host'],
           port=db_config['port'],
           database=db_config['database']
       )
       cursor = connection.cursor()
       query = "SELECT id FROM users WHERE phone = %s"
       cursor.execute(query, (phone,))
       result = cursor.fetchone()
       cursor.close()
       connection.close()
       if result:
           return result[0]
       else:
           print(f"No user found for phone: {phone}")
           return None
   except OperationalError as e:
       print(f"Error: {e}")
       return None


def call_invoice_api(tenant_mobiles):
   access_token = os.getenv("SPEEDRENT_AUTHORIZATION_TOKEN")
   headers = {
       "Authorization": f"{access_token}",
       "Content-Type": "application/json",
       "Accept": "application/json"
   }
   responses = []
   for mobile in tenant_mobiles:
       user_id = get_user_id_by_phone(mobile)
       if user_id:
           try:
               url = f"https://api-beta.speedrent.com/speedmanage/api/invoice?userId={user_id}"
               response = requests.get(url, headers=headers)
               if response.status_code == 200:
                   invoice_data = response.json()
                   extracted_data = [extract_invoice_data(invoice) for invoice in invoice_data["content"]]
                   invoice_strings = [format_invoice_string(data, mobile) for data in extracted_data]
                   combined_invoice_string = "\n".join(invoice_strings)
                   ai_response = send_to_ai_endpoint(combined_invoice_string)
                   responses.append(ai_response)
               else:
                   print(f"Error: {response.status_code} for userId: {user_id}")
           except requests.RequestException as e:
               print(f"Request error: {e}")
   return responses


def send_to_ai_endpoint(invoice_string):
   if not invoice_string.strip():
       print("Invoice string is empty. Skipping API call.")
       return


   url = "https://aibot.speedrent.com/api/ai/simple-query"
   headers = {
       "Content-Type": "application/json",
       "Accept": "application/json"
   }
   payload = {
       "systemMessage": "You are rental collection agent for the rental platform called SPEEDHOME. You will be provided the invoice history of a tenant. Your task is to categorize the tenant based on the invoice history. Don't consider the cancelled invoices. Consider the invoices after 2023 December only. Invoice paid earlier than due date are also considered paid on time. You need to categorize them into two groups 1. High risk tenant. 2. Low risk tenant./nLow risk tenant:/nCategory 1: A tenant who always pays on time./nCategory 2: A tenant who pays late but always pays on the same date/nCategory 3: A tenant who is first time late/nHigh risk tenant/n1. Always delay /nYou response should be in following json structure: /n{ /n user_phone /ntenant_type: <type>/nreason:/n}",
       "userMessage": str(invoice_string),
       "model": "GEMINI_FLASH"
   }
   try:
    json_payload = json.dumps(payload)
    response = requests.post(url, data=json_payload, headers=headers)
    if response.status_code == 200:
           if response.content:
               managed = response.text.replace("```", "")
               managed = managed.replace("json", "")
               return json.loads(managed)
           else:
               print("Empty response received from AI endpoint")
    else:
           print(f"Error: {response.status_code} when sending to AI endpoint")
   except requests.RequestException as e:
       print(f"Request error: {e}")


# Main execution
# response_data = get_overdue_data_from_cases()
# if response_data:
#    tenant_mobiles = get_tenant_mobiles(response_data)
#    tenant_risk = call_invoice_api(tenant_mobiles)
#    print(tenant_risk)
@shared_task(name='cronjob.task.process_overdue_cases')
def process_overdue_cases():
    # Main execution
    response_data = get_overdue_data_from_cases()
    if response_data:
        tenant_mobiles = get_tenant_mobiles(response_data)
        tenant_risk = call_invoice_api(tenant_mobiles)
        print(tenant_risk)



