import os
import random
import string
import boto3
import re
import vincent
from collections import Counter
from datetime import datetime, timedelta
from pathlib import Path
import vincent
from django.conf import settings
from django.http import HttpResponse
from django.shortcuts import render
from social_core.pipeline import user

from .models import Leads

BASE_DIR = getattr(settings, "BASE_DIR", None)


def home(request):
    return render(request, 'signup.html')


def privacy(request):
    return render(request, 'privacy.html')


def login(request):
    return render(request, 'login.html')


# insert the user sign up information into the DynamoDB table "gsg-signup-table"
def signup(request):
    leads = Leads()
    status = leads.insert_lead(request.POST['fromAirport'], request.POST['toAirport'], request.POST['date'], request.POST['email'],
                               request.POST['notifications'],request.POST['username'])
    # if status == 200:
    #     leads.send_notification(request.POST['email'])
    return HttpResponse('', status=status)


# user dashboard: get data for route selection drop-down and chart
def dashboard(request):
    routeID = request.GET.get('routeID')
    user = request.user.username
    leads = Leads()
    if routeID:
        # get chart data for chosen route
        items = leads.get_priceData(routeID)
        pr = [float(i['price']) for i in items if 'price' in i]
        dt = [i['date'] for i in items if 'date' in i]
        data = {'data': pr, 'x': dt}
        print(data)
        bar = vincent.Bar(data, iter_idx='x')
        bar.axis_titles(x='Dates', y='Prices')

        # cleanup function: delete any locally existing priceChart files (from local testings)
        deleteTempFiles(os.path.join(BASE_DIR, 'static'), 'priceChart')

        # generate filename with id based on yyyyMMdd and a random 5-character string to distinguish chart data
        filename = 'priceChart' + generateUniqueName() + '.json';
        bar.to_json(os.path.join(BASE_DIR, 'static', filename))

        # send file to S3
        uploadToS3('priceChart', filename);

        return render(request, 'dashboard.html', {'items': items, 'filename': 'priceChart/' + filename})
    elif user:
        # get routes for drop-down menu

        items = leads.get_routeIDs(user)
        #for item in items:
           # clean = re.sub('[$]', ' ', item['routeID'])

        #return render(request, 'dashboard.html', {'routeIDs': items, 'cleanName': clean})
        return render(request, 'dashboard.html', {'routeIDs': items})
    else:
        return render(request, 'login.html')


# function for uploading the chart json file to S3
def uploadToS3(dir, filename):
    bucketName = getattr(settings, "AWS_STORAGE_BUCKET_NAME", None)
    s3 = boto3.resource('s3')
    data = open(os.path.join(BASE_DIR, 'static', filename), 'rb')
    s3.Bucket(bucketName).put_object(Key=dir + '/' + filename, Body=data)

# function for creating unique ID for dashboard chart files
def generateUniqueName():
    date = datetime.now().strftime("%Y%m%d");
    chars = random.choices(string.ascii_lowercase + string.digits, k=5);
    return date + '-' + ''.join(chars);


# cleanup function of old dashboard chart files on S3
def deleteTempFiles(path, prefix):
    for f in Path(path).glob(prefix + "_"):
        fileDateStr = f.name[len(prefix) + 1:f.name.index('-')]
        fileDate = datetime.strptime(fileDateStr, '%Y%m%d')

        # Use >= yesterday as comparison so it doesnt include files created today
        # which may include files still in use
        if fileDate <= datetime.now() - timedelta(days=1):
            os.remove(f)


