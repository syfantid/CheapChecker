import sys
from django.db import models
import boto3
import os
import logging

import time
from calendar import timegm

# back-end tables
STARTUP_SIGNUP_TABLE = os.environ['STARTUP_SIGNUP_TABLE']
AWS_REGION = os.environ['AWS_REGION']
PRICE_LOG = os.environ['PRICE_LOG']

logger = logging.getLogger(__name__)


class Leads(models.Model):

    # sign-up form data
    def insert_lead(self, fromAirport, toAirport, date, email, notifications, username):
        try:
            dynamodb = boto3.resource('dynamodb', region_name=AWS_REGION)
            table = dynamodb.Table(STARTUP_SIGNUP_TABLE)
        except Exception as e:
            logger.error(
                'Error connecting to database table: ' + (e.fmt if hasattr(e, 'fmt') else '') + ','.join(e.args))
            return 403
        try:
            if not username:
                username = "anonymous"
            response = table.put_item(
                Item={
                    'routeID': fromAirport[0:fromAirport.find(",")] + '$' + toAirport[0:toAirport.find(",")] + '$' + date,
                    'date': timegm(time.strptime(date, "%Y-%m-%d")),
                    'lowestPrice': sys.maxsize,
                    'email': email,
                    'username': username,
                    'notifications': notifications,
                },
                ReturnValues='ALL_OLD',
            )
        except Exception as e:
            logger.error(
                'Error adding item to database: ' + (e.fmt if hasattr(e, 'fmt') else '') + ','.join(e.args))
            return 403
        status = response['ResponseMetadata']['HTTPStatusCode']
        if status == 200:
            if 'Attributes' in response:
                logger.error('Existing item updated to database.')
                return 409
            logger.error('New item added to database.')
        else:
            logger.error('Unknown error inserting item to database.')

        return status

    # priceData for chart on dashboard
    def get_priceData(self, routeID):
        try:
            dynamodb = boto3.resource('dynamodb', region_name=AWS_REGION)
            table = dynamodb.Table(PRICE_LOG)
        except Exception as e:
            logger.error(
                'Error connecting to database table: ' + (e.fmt if hasattr(e, 'fmt') else '') + ','.join(e.args))
            return None
        expression_attribute_values = {}
        FilterExpression = []
        if routeID:
            expression_attribute_values[':r'] = routeID
            FilterExpression.append('routeID = :r')
            response = table.scan(
                # FilterExpression=Key('routeID').eq(':r'),
                FilterExpression=' and '.join(FilterExpression),
                ExpressionAttributeValues=expression_attribute_values,
                ProjectionExpression="#dt, price",
                ExpressionAttributeNames={"#dt": "date"}
            )

        if response['ResponseMetadata']['HTTPStatusCode'] == 200:
            return response['Items']
        logger.error('Unknown error retrieving items from database.')
        return None

    # Drop-down menu of dashboard
    def get_routeIDs(self, user):
        try:
            dynamodb = boto3.resource('dynamodb', region_name=AWS_REGION)
            table = dynamodb.Table(os.environ['REQUESTS'])
        except Exception as e:
            logger.error(
                'Error connecting to database table: ' + (e.fmt if hasattr(e, 'fmt') else '') + ','.join(e.args))
            return None

        # filter only routes for current user
        expression_attribute_values = {}
        FilterExpression = []
        expression_attribute_values[':u'] = user
        FilterExpression.append('username = :u')
        response = table.scan(
            FilterExpression=' and '.join(FilterExpression),
            ExpressionAttributeValues=expression_attribute_values,
            ProjectionExpression='routeID',
        )

        if response['ResponseMetadata']['HTTPStatusCode'] == 200:
            return response['Items']
        logger.error('Unknown error retrieving items from database.')
        return None

        # # Drop-down menu of dashboard
        # def get_routeIDs(self, username):
        #     try:
        #         dynamodb = boto3.resource('dynamodb', region_name=AWS_REGION)
        #         table = dynamodb.Table(os.environ['PRICE_LOG'])
        #     except Exception as e:
        #         logger.error(
        #             'Error connecting to database table: ' + (e.fmt if hasattr(e, 'fmt') else '') + ','.join(e.args))
        #         return None
        #
        #     # filter only routes for current user
        #     expression_attribute_values = {}
        #     FilterExpression = []
        #     expression_attribute_values[':u'] = username
        #     FilterExpression.append('username = :u')
        #     response = table.scan(
        #         FilterExpression=' and '.join(FilterExpression),
        #         ExpressionAttributeValues=expression_attribute_values,
        #         ProjectionExpression='routeID',
        #     )
        #
        #     if response['ResponseMetadata']['HTTPStatusCode'] == 200:
        #         return response['Items']
        #     logger.error('Unknown error retrieving items from database.')
        #     return None