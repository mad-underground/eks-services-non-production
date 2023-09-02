"""
export APPCONFIG_APP_ID=lqhn8x7
export APPCONFIG_ENV_ID=aepsluc
export RABBITMQ_URI='amqps://proxysql:fmKX8xLE5eDrd64vUp@b-5b5d413e-a223-4c6c-8581-e8a347be8f86.mq.ap-southeast-1.amazonaws.com:5671/shared-services'
"""

# celery --app application.app worker --queues zeny.dev.q.proxysql --without-heartbeat --without-gossip --without-mingle --loglevel=INFO

import os
from string import Template
from celery import Celery
from kombu import Exchange, Queue
from app_config_profile import AppConfigProfile

# f'amqps://{MQ_USERNAME}:{MQ_PASSWORD}@{MQ_HOST}:{MQ_PORT}/{MQ_VHOST}'
rabbitmq_uri = os.getenv('RABBITMQ_URI', default='amqp://guest@localhost//')
app = Celery('proxysql-sidecar', broker=rabbitmq_uri)
default_exchange = Exchange('zeny.dev.e.proxysql', type='direct')
default_queue = 'zeny.dev.q.proxysql'
default_routing_key = 'default'
celery_config = {
    'task_ignore_result': True,
    'task_create_missing_queues': True,
    'worker_redirect_stdouts': False,
    'task_default_exchange': default_exchange,
    'task_default_exchange_type': 'direct',
    'task_default_queue': default_queue,
    'task_default_routing_key': default_routing_key,
    'task_queues': (
        Queue(default_queue, exchange=default_exchange, routing_key=default_routing_key),
    ),
    'task_routes': {
        'handle.message': { 'exchange': default_exchange, 'queue': default_queue, 'routing_key': default_routing_key },
    }
}

app.config_from_object(celery_config)

appconfig_app_id = os.getenv('APPCONFIG_APP_ID', default=None)
appconfig_env_id = os.getenv('APPCONFIG_ENV_ID', default=None)
secrets_profile_id = os.getenv('SECRETS_APPCONFIG_PROFILE_ID', default='3d694be')
proxysql_cnf_profile_id = os.getenv('PROXYSQL_CNF_APPCONFIG_PROFILE_ID', default='3wfq0vu')
appconfig_minimum_poll_interval = os.getenv('APPCONFIG_MINIMUM_POLL_INTERVAL', default=30)

secrets = AppConfigProfile(appconfig_app_id, secrets_profile_id, appconfig_env_id, minimum_poll_interval=appconfig_minimum_poll_interval, content_type='application/json')
proxysql_cnf = AppConfigProfile(appconfig_app_id, proxysql_cnf_profile_id, appconfig_env_id, minimum_poll_interval=appconfig_minimum_poll_interval, content_type='text/plain') 

@app.task(name='generate.proxysql.cnf', shared=False)
def generate_proxysql_cnf():
    try:
        secrets.fetch_configuration()
        proxysql_cnf.fetch_configuration()
        template = Template(proxysql_cnf.config)
        with open('proxysql.cnf', 'w') as f:
            f.write(template.substitute(secrets.config))
    except Exception as ex:
        print(f'Unexpected error occurred :: {repr(ex)}')


@app.task(name='handle.message', shared=False, bind=True)
def handle_message(msg):
    print(repr(msg))


if __name__ == '__main__':
    generate_proxysql_cnf.apply()