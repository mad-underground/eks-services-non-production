import os
import json
import boto3
import time
from string import Template
from botocore.exceptions import ClientError

config_client = boto3.client('appconfig', region_name='ap-southeast-1')
configdata_client = boto3.client('appconfigdata', region_name='ap-southeast-1')

class AppConfigProfile:

    def __init__(self, app_id, profile_id, env_id, minimum_poll_interval=30, content_type='text/plain'):
        self.app_id = app_id
        self.profile_id = profile_id
        self.env_id = env_id
        self.minimum_poll_interval = minimum_poll_interval
        self.content_type = content_type # examples: text/plain, application/json, application/yaml
        self.config_token = None
        self.config = None


    def start_configuration_session(self):
        print(f'[start_configuration_session][{self.profile_id}] starting configuration session')
        try:
            response = configdata_client.start_configuration_session(
                ApplicationIdentifier=self.app_id,
                EnvironmentIdentifier=self.env_id,
                ConfigurationProfileIdentifier=self.profile_id,
                RequiredMinimumPollIntervalInSeconds=self.minimum_poll_interval
            )
            return response['InitialConfigurationToken']
        except ClientError as ex:
            if ex.response['Error']['Code'] == 'ResourceNotFoundException':
                print(f'[start_configuration_session][{self.profile_id}] The requested config deployment (app: {self.app_id}, profile: {self.profile_id}, env: {self.env_id}) was not found')
            elif ex.response['Error']['Code'] == 'ThrottlingException':
                print(f'[start_configuration_session][{self.profile_id}] ThrottlingException :: {repr(ex)}')
            elif ex.response['Error']['Code'] == 'InternalServiceError':
                print(f'[start_configuration_session][{self.profile_id}] An error occurred on service side :: {repr(ex)}')
            elif ex.response['Error']['Code'] == 'BadRequestException':
                print(f'[start_configuration_session][{self.profile_id}] Bad request :: {repr(ex)}')
        except Exception as ex:
            print(f'[start_configuration_session][{self.profile_id}] Unexpected error occurred :: {repr(ex)}')
        return None


    def fetch_configuration(self):
        print(f'[fetch_configuration][{self.profile_id}] fetching configuration from aws')
        if self.config_token is None:
            self.config_token = self.start_configuration_session()
        response = configdata_client.get_latest_configuration(
            ConfigurationToken=self.config_token
        )
        self.config_token = response['NextPollConfigurationToken'] if 'NextPollConfigurationToken' in response else self.config_token
        if 'Configuration' in response:
            try:
                configuration = response['Configuration'].read().decode().strip()
                response['Configuration'].close()
                if configuration:
                    self.process_configuration(configuration)
                else:
                    print(f'[get_latest_configuration][{self.profile_id}] No updates')
            except Exception as ex:
                print(f'[get_latest_configuration][{self.profile_id}] Unexpected error occurred while reading configuration :: {repr(ex)}')
        else:
            print(f'[get_latest_configuration][{self.profile_id}] Cancelled operation, no configuration was found in the response')


    def process_configuration(self, configuration):
        print(f'[fetch_configuration][{self.profile_id}] processing configuration')
        try:
            if self.content_type == 'application/json':
                self.config = json.loads(configuration)
            else:
                self.config = configuration
        except Exception as ex:
            print(f'[process_configuration][{self.profile_id}] Unexpected error occurred while processing configuration :: {repr(ex)}')


    def fetch_configuration_profile(self):
        print(f'[fetch_configuration][{self.profile_id}] fetching configuration profile from aws')
        try:
            response = config_client.get_configuration_profile(
                ApplicationId=self.app_id,
                ConfigurationProfileId = self.profile_id
            )
            print(json.dumps(response, indent=2, default=repr))
        except ClientError as ex:
            if ex.response['Error']['Code'] == 'ResourceNotFoundException':
                print(f'[start_configuration_session][{self.profile_id}] The requested config deployment for (app: {self.app_id}) was not found')
            elif ex.response['Error']['Code'] == 'InternalServiceError':
                print(f'[start_configuration_session][{self.profile_id}] An error occurred on service side :: {repr(ex)}')
            elif ex.response['Error']['Code'] == 'BadRequestException':
                print(f'[start_configuration_session][{self.profile_id}] Bad request :: {repr(ex)}')
        except Exception as ex:
            print(f'[start_configuration_session][{self.profile_id}] Unexpected error occurred :: {repr(ex)}')
        return None


    def get_config(self):
        return self.config
