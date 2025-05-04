#!/usr/bin/env python
# coding: utf-8

# In[1]:


import pandas as pd
import seaborn as sns
import numpy as np
import os
from tqdm import tqdm
import json
from openai import OpenAI
import re
pd.set_option('display.max_colwidth', None)


# In[2]:


# from nltk.stem import WordNetLemmatizer
# import nltk
# nltk.download('wordnet')
# nltk.download('omw-1.4')


# # Bank services provided on branches
# Here’s a list of services that typically require a person to visit a bank branch, though availability can vary depending on the bank and region:

# 1. Account Opening
# Identity Verification: Some banks require in-person verification to open accounts.
# Submission of Documents: Providing original documents like ID, proof of address, or other paperwork.
# 2. Loan Applications
# Mortgage or Business Loans: In-person meetings to discuss terms, conditions, and application submission.
# Document Submission: Submission of physical collateral or notarized documents.
# 3. Notarization or Signature Validation
# Bank-Mandated Signatures: For loan agreements, guarantees, or joint accounts.
# Notary Services: When required for certain banking activities.
# 4. Cash-Related Services
# Large Cash Withdrawals: Requests above daily ATM limits.
# Foreign Currency Exchange: Exchanging currency for international travel.
# Depositing Cash Over Limit: Large cash deposits that require teller validation.
# 5. Safe Deposit Box Services
# Access to Safe Deposit Box: Retrieving or storing items in a bank's secure vault.
# Renting a Safe Deposit Box: Registration and issuance of keys.
# 6. Account Closure
# For some banks, closing an account may require in-person verification or a signed request at the branch.
# 7. Disputes and Claims
# Fraud or Dispute Resolution: Handling disputes about transactions or fraudulent activities.
# Claiming Funds: For example, claiming funds from a deceased relative’s account.
# 8. Specialized Services
# Investments and Wealth Management: In-person consultations for investment or portfolio management.
# Certified Bank Statements: Obtaining an officially stamped and signed bank statement.
# 9. KYC (Know Your Customer) Updates
# Providing physical documents to update address, ID, or other personal information.
# 10. Other Legal or Regulatory Requirements
# Power of Attorney Setup: Authorizing someone to manage your account.
# Compliance Processes: Verifying compliance with local regulations.
# Banks often encourage digital or remote alternatives for many services, but certain procedures still demand a physical visit for security and legal reasons. Let me know if you’d like further insights or clarification!
# In[ ]:

def recommend_options(service_name):
  recommendations = {
        "Cash Deposits": ["If you're looking to make a cash deposit, you can either visit your nearest BK agent or use our digital channels (USSD *334#) to transfer funds from your mobile wallet to your BK account. For cheque deposits, please proceed with booking a slot at your nearest BK branch."],
        "Cash Withdrawal": ["You can easily withdraw cash directly from your BK Mobile App — no need to wait in line or rush to the ATM. With just a few taps, you can access your cash anytime, anywhere. Here's how: \n\n- Use an ATM if the amount is less than or equal to 400,000 RWF.\n\n- Use the Mobile App or USSD (*334#) to generate a cash withdrawal passcode and collect your cash at a BK Agent.\n\n- Book a slot at your nearest BK branch for larger transactions or special services."],
        "Bill Payment": ["Use our digital channels: Online banking, Mobile App, USSD, and Agent. For more details kindly follow https://bk.rw/support-and-updates/help-center"],
        "Transfers": ["Use our digital channels: Online banking, Mobile App, USSD, and Agent. For more details kindly follow https://bk.rw/support-and-updates/help-center"],
        "Account opening": ["1. Open account using BK Mobile APP\n2. Consult BK agent\n3. Visit nearest branch"],
        "Cards": ["For card-related services such as prepaid cash loading or credit card payments, please use BK digital channels (Internet Banking, Mobile App, or USSD *334#)."],
        "KYC": ["Kindly visit any BK branch to complete the necessary physical documents for updating your address, ID, or other personal information."],
        "Disputes and Claims": ["If you need assistance with disputes regarding transactions, fraudulent activities, or claiming funds \u2014 such as accessing a deceased relative\u2019s account \u2014 our CRM is available to support you and ensure a prompt resolution of your request or inquiry. Visit: https://bk.rw/support-and-updates/report-an-issue"]
    }
    # Normalize the service_name to match the dictionary keys
  service_name = service_name.strip().title()
  return recommendations.get(service_name, ["Visit the branch for assistance."])
  print(f"Recommendations for {service_name}: {result}")  # Debug statement
  return result
# In[27]:


data = {
  "DEPOSITS": " If you're looking to make a cash deposit, you can either visit your nearest BK agent or use our digital channels (USSD *334#) to transfer funds from your mobile wallet to your BK account. For cheque deposits, please proceed with booking a slot at your nearest BK branch.",
  "WITHDRAW": "You can easily withdraw cash directly from your BK Mobile App — no need to wait in line or rush to the ATM. With just a few taps, you can access your cash anytime, anywhere. Here's how: \n\n- Use an ATM if the amount is less than or equal to 400,000 RWF.\n\n- Use the Mobile App or USSD (*334#) to generate a cash withdrawal passcode and collect your cash at a BK Agent.\n\n- Book a slot at your nearest BK branch for larger transactions or special services.",
  "BILL PAYMENT": "Use our digital channels: Online banking, Mobile App, USSD, and Agent.",
  "TRANSFERS": "Use our digital channels: Online banking, Mobile App, USSD, and Agent.",
  "ACCOUNT OPENING": "1. Open account using BK Mobile APP\n2. Consult BK agent\n3. Visit nearest branch",
  "CARDS MANAGEMENT": "For card-related services such as prepaid cash loading or credit card payments, please use BK digital channels (Internet Banking, Mobile App, or USSD *334#).",
  "KYC": "Kindly visit any BK branch to complete the necessary physical documents for updating your address, ID, or other personal information.",
  "DISPUTES AND CLAIMS": "If you need assistance with disputes regarding transactions, fraudulent activities, or claiming funds — such as accessing a deceased relative’s account — our CRM is available to support you and ensure a prompt resolution of your request or inquiry."
}

# Save to a file
with open(r'bank_services.json', 'w') as f:
    json.dump(data, f, indent=4)


# In[3]:


with open(r'bank_services.json', 'r') as service_json:
    content = service_json.read()
    
# Replace single quotes with double quotes carefully
# content = re.sub(r"(?<!\\)'", '"', content)

# Now try loading
services_data = json.loads(content)
print(services_data)


# In[4]:


len(services_data)


# In[5]:


services_data.keys()


# In[6]:


services_data['DEPOSITS']


# def get_service_details(services, data):
#     """
#     This function accepts a list of keywords and returns a dictionary with more details about each keyword.
# 
#     Parameters:
#         keywords (list): A list of keywords to look up.
#         data (dict): A dictionary with keyword details.
# 
#     Returns:
#         dict: A dictionary with keywords as keys and details as values.
#     """
#     # Create a result dictionary
#     result = {}
# 
#     # Fetch details for each keyword
#     for service in services:
#         # Check if the lowercase version of the keyword exists in the data
#         service_lower = service.lower()
#         found = False
#         for key in data.keys():
#             if key.lower() == service_lower:
#                 result[service] = data[key]
# #                 print('SERVICES:', result[keyword])
#                 found = True
#                 break
#         
#         if not found:
#             result[keyword] = "For any services related to {}, kindly visit one of our branches for further details and clarification.".format(keyword)
# 
#     return result
# 
# # Example usage
# keywords = ["deposits"]
# details = get_service_details(keywords, services_data)
# for keyword, detail in details.items():
#     print(f"{keyword}: {detail}")
# 

# In[43]:


# def lemmatize_text(text):
#     lemmatizer = WordNetLemmatizer()
    
#     words = text.lower().split()
#     lemmatized_words = [lemmatizer.lemmatize(word, pos='n') for word in words]  # 'n' for noun lemmatization
    
#     return ' '.join(lemmatized_words)

# # Example Usage
# text = "The Cats is running in the fields."
# lemmatized_text = lemmatize_text(text)

# print(lemmatized_text)


# In[ ]:


# def normalize_text(text):
#     # Convert to lowercase to ignore case
#     text = text.lower()
    
#     # Strip plural 's' if the word ends with 's'
#     # This is a simple approach, and may need refinement for irregular plurals.
#     text = re.sub(r'\bs(\b|\s)', r'\1', text)  # Remove trailing 's' if word ends in 's'
    
#     return text

