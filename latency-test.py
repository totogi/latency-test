import asyncio
from os import access, environ

import time
import json
import httpx
from datetime import datetime
from gql import gql, Client
from gql.transport.aiohttp import AIOHTTPTransport

import numpy as np
s = httpx.AsyncClient(http2=True, verify=False)

base_url = environ['TOTOGI_URL']
device_id = "ede7914e-4055-4484-9652-da46802266c2"
account_id = "ede7914e-4055-4484-9652-da46802266c2"
provider_id = "fc397a41-7bc8-3fa3-971b-2686c0d77c2f"

ten_megabytes = 10485760

# The number of N40 Start/Update/Terminate sessions to iterate (sequentially)
num_sessions = 100

# The number of Update calls for each session
updates_per_session = 5

async def get_token():
    url = "https://cognito-idp.us-east-1.amazonaws.com/us-east-1_us-east-1_bYrFO4DaR/"

    payload = {
        "AuthParameters": {
            "USERNAME": environ['TOTOGI_USERNAME'],
            "PASSWORD": environ['TOTOGI_PASSWORD']
        },
        "AuthFlow": "USER_PASSWORD_AUTH",
        "ClientId": "3bsr3p2j5ffn1cf05knuqc03v2"
    }
    headers = {
        "Content-Type": "application/x-amz-json-1.1",
        "X-Amz-Target": "AWSCognitoIdentityProviderService.InitiateAuth"
    }

    print('Getting access token')
    response = await s.request("POST", url, json=payload, headers=headers)
    token_json = response.json()
    access_token = token_json['AuthenticationResult']['AccessToken']
    print('Retrieved access token')

    return access_token

async def init(token):
    url = f"{base_url}/nchf-convergedcharging/v3/chargingData"
    request_time = f"{datetime.now().isoformat()[:-3]}Z"
    payload = {
        "invocationSequenceNumber": 1,
        "tenantIdentifier": provider_id,
        "subscriberIdentifier": device_id,
        "multipleUnitUsage": [
            {
                "requestedUnit": {"totalVolume": 300},
                "ratingGroup": 300
            }
        ],
        "locationReportingChargingInformation": {"pSCellInformation": {"nrcgi": {
                    "nrCellId": "11",
                    "nid": "12",
                    "plmnId": {
                        "mcc": "310",
                        "mnc": "005"
                    }
                }}},
        "nfConsumerIdentification": {"nodeFunctionality": "SMF"},
        "invocationTimeStamp": request_time
    }
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token}"
    }

    response = await s.request("POST", url, json=payload, headers=headers)
    headers = response.headers
    return_location = None
    if 'location' in headers:
        return_location = headers['location']

    print(f'{response.status_code}: {response.text}')
    return (return_location, response.status_code)

async def update(token, location_header, seq_num):
    url = f"{base_url}/nchf-convergedcharging/v3/chargingData/{location_header}/update"
    request_time = f"{datetime.now().isoformat()[:-3]}Z"
    payload = {
        "invocationSequenceNumber": seq_num,
        "tenantIdentifier": provider_id,
        "subscriberIdentifier": device_id,
        "multipleUnitUsage": [
            {
                "requestedUnit": {"totalVolume": ten_megabytes},
                "usedUnitContainer": [
                    {
                        "localSequenceNumber": 1,
                        "totalVolume": ten_megabytes
                    }
                ],
                "ratingGroup": 300
            }
        ],
        "locationReportingChargingInformation": {"pSCellInformation": {"nrcgi": {
                    "nrCellId": "11",
                    "nid": "12",
                    "plmnId": {
                        "mcc": "310",
                        "mnc": "170"
                    }
                }}},
        "nfConsumerIdentification": {"nodeFunctionality": "SMF"},
        "invocationTimeStamp": request_time
    }
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token}"
    }

    response = await s.request("POST", url, json=payload, headers=headers)
    return_location = None
    if 'location' in response.headers:
        return_location = response.headers['location']

    print(f'{response.status_code}: {response.text}')
    return (return_location, response.status_code)

async def terminate(token, location_header, seq_num):
    url = f"{base_url}/nchf-convergedcharging/v3/chargingData/{location_header}/release"
    request_time = f"{datetime.now().isoformat()[:-3]}Z"
    payload = {
        "invocationSequenceNumber": seq_num,
        "tenantIdentifier": provider_id,
        "subscriberIdentifier": device_id,
        "multipleUnitUsage": [
            {
                "usedUnitContainer": [
                    {
                        "localSequenceNumber": 2,
                        "totalVolume": 0
                    }
                ],
                "ratingGroup": 300
            }
        ],
        "locationReportingChargingInformation": {"pSCellInformation": {"nrcgi": {
                    "nrCellId": "11",
                    "nid": "12",
                    "plmnId": {
                        "mcc": "310",
                        "mnc": "170"
                    }
                }}},
        "nfConsumerIdentification": {"nodeFunctionality": "SMF"},
        "invocationTimeStamp": request_time
    }
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token}"
    }

    response = await s.request("POST", url, json=payload, headers=headers)

    print(f'{response.status_code}: {response.text}')
    return response.status_code

def get_gql_client(token):
    # Select your transport with a defined url endpoint
    gql_transport = AIOHTTPTransport(url="https://api.produseast1.totogi.app/graphql",
        headers={"Authorization": f"{token}"})

    # Create a GraphQL client using the defined transport
    gql_client = Client(transport=gql_transport, fetch_schema_from_transport=True)
    return gql_client

async def get_balance(gql_client):
    query = gql(
        """
        query GetAccount(
                $providerId: ID!,
                $accountId: ID!) {
            getAccount(  
                providerId: $providerId,
                accountId: $accountId) {
            ... on AccountNotFound {
            errorMessage
            providerId
            errorCode
            accountId
            }
            ... on Account {
            id
            customData
            providerId
            balance {
                customData
                value
                version
            }
                    activePlanVersions{
                        from
                        to
                        planVersion{
                            id
                            version
                planServices{
                                balanceName
                            }
                        }
                    }
                    archivedPlanVersions{
                        from
                        to
                        planVersion{
                            id
                            version
                planServices{
                                balanceName
                            }
                        }
                    }
                }
            }
        }
        """
    )
    params = {
        "providerId": provider_id,
        "accountId": account_id
    }
    
    result = await gql_client.execute_async(query, variable_values=params)
    balance_json_str = result['getAccount']['balance']['customData']
    balance = json.loads(balance_json_str)
    data = balance['balance']['data']

    return int(data['total'])

async def main():
    all_samples = []
    start_txn_samples = []
    update_txn_samples = []
    terminate_txn_samples = []

    access_token = await get_token()
    gql_client = get_gql_client(access_token)
    start_balance = await get_balance(gql_client)
    print(f"Starting balance = {start_balance}")
    last_balance = start_balance

    num_errors = 0

    for i in range(0, num_sessions):
        start = time.perf_counter_ns()
        (location, status_code) = await init(access_token)
        end = time.perf_counter_ns()
        all_samples.append(end-start)
        start_txn_samples.append(all_samples[-1])
        if status_code >= 400:
            num_errors += 1

        for j in range(0, updates_per_session):
            start = time.perf_counter_ns()
            (location, status_code) = await update(access_token, location, seq_num= j+2)
            end = time.perf_counter_ns()
            all_samples.append(end-start)
            update_txn_samples.append(all_samples[-1])
            if status_code >= 400:
                num_errors += 1

        start = time.perf_counter_ns()
        status_code = await terminate(access_token, location, seq_num = 2+updates_per_session)
        end = time.perf_counter_ns()
        all_samples.append(end-start)
        terminate_txn_samples.append(all_samples[-1])
        if status_code >= 400:
            num_errors += 1
        last_balance = await get_balance(gql_client)
        print(f"New balance = {last_balance}")

    if len(all_samples) > 0:
        print_array_summary("Start Transactions", start_txn_samples)
        print_array_summary("Update Transactions", update_txn_samples)
        print_array_summary("Terminate Transactions", terminate_txn_samples)
        print_array_summary("All Transactions", all_samples)
        print(f"Error count: {num_errors}")
        print(f"Error rate: {num_errors / len(all_samples)}")
        print(f"Start balance = {start_balance}, End balance = {last_balance}, Delta = {start_balance - last_balance}")
        

def print_array_summary(label, all_samples):
    # convert nanoseconds to milliseconds
    milli_samples = np.array(all_samples) / 1000000
    print(f"------------------ {label} ----------------------------------------")
    print(f"Number of samples: {len(milli_samples)}")
    print(f"Mean: {np.mean(milli_samples)}")
    print(f"Max: {np.max(milli_samples)}")
    print(f"Median: {np.median(milli_samples)}")
    print(f"Percentiles (p80, p95, p99): {np.percentile(milli_samples, [80,95,99])}")
    print("-------------------------------------------------------------------------")

if __name__ == "__main__":
    asyncio.run(main())
