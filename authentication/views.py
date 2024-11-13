from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.contrib.auth.models import User
from django.contrib import messages
from django.core.mail import EmailMessage, send_mail

from django.contrib.sites.shortcuts import get_current_site
from django.template.loader import render_to_string
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode
from django.utils.encoding import force_bytes, force_str
from django.contrib.auth import authenticate, login, logout
from . tokens import generate_token
from dateutil.parser import parse
from datetime import datetime

from django.shortcuts import render, redirect
from django.contrib.auth.models import User
from django.contrib import messages
# Create your views here.
import csv
from datetime import datetime
from pymongo import MongoClient
from django.http import HttpResponse
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
import json
from django.http import HttpResponse
from datetime import datetime
#from .models import SensorData  # Adjust this line based on your actual model or data-fetching method
from pymongo import MongoClient

def home(request):
    return render(request, "authentication/index.html")

from django.http import HttpResponse
import csv
from datetime import datetime, timezone
from django.conf import settings

mongo_uri = 'mongodb+srv://suryanshkgp:m3$JviM$d*X32cB@cluster0.lgvfa.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0'
from django.http import JsonResponse

from huggingface_hub import InferenceClient

import numpy as np

import pytz

def convert_iso_to_ist(iso_time):
    """Converts ISO 8601 time to IST (Indian Standard Time)"""

    # Parse the ISO 8601 string into a datetime object
    dt = datetime.fromisoformat(iso_time)

    # If the ISO string doesn't contain timezone information, assume UTC
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)

    # Convert to IST
    ist_timezone = pytz.timezone('Asia/Kolkata')
    ist_dt = dt.astimezone(ist_timezone)

    return ist_dt


from datetime import datetime
import pytz

def convert_ist_to_human_readable(ist_datetime):
    """Converts IST datetime to human-readable format."""

    # Format the datetime object to a human-readable string
    human_readable_datetime = ist_datetime.strftime('%Y-%m-%d %H:%M:%S %Z')

    return human_readable_datetime

def chatbot_query(request):
    # Parse parameters from request
    node_id = request.GET.get("node_id")
    query = request.GET.get("query")
    
    if not node_id or not query:
        return JsonResponse({"error": "Missing node_id or query"}, status=400)

    # Connect to MongoDB and retrieve data for the specified node_id
    try:
        node_id = int(node_id)
    except ValueError:
        return JsonResponse({"error": "Invalid node_id"}, status=400)

    client = MongoClient(mongo_uri)
    db = client['sensor_data']
    collection = db['readings']
    
    # Fetch all data for the specified node_id
    readings = list(collection.find({"node_id": node_id}))

    data = [{
        'timestamp': convert_ist_to_human_readable(convert_iso_to_ist(reading['timestamp'].isoformat())),
        'battery_voltage': float(reading['battery_voltage']['$numberDouble']) if isinstance(reading['battery_voltage'], dict) else float(reading['battery_voltage']),
        'solar': float(reading['solar']['$numberDouble']) if isinstance(reading['solar'], dict) else float(reading['solar']),
        'pressure': float(reading['pressure']['$numberDouble']) if isinstance(reading['pressure'], dict) else float(reading['pressure']),
    } for reading in readings]

    client.close()
    
    # Sample 20 equally distributed data points
    if len(data) > 20:
        indices = np.linspace(0, len(data) - 1, 20, dtype=int)
        data = [data[i] for i in indices]

    # Prepare messages for LLM API
    context_data = "\n".join([f"Timestamp: {d['timestamp']}, Battery Voltage: {d['battery_voltage']}, Solar: {d['solar']}, Pressure: {d['pressure']}" for d in data])
    messages = [
        {"role": "system", "content": "You are a data assistant analyzing sensor data for various nodes. Please include features such as significant drops or jumps in the data, as well as insights related to the health and functioning of the devices."},
        {"role": "user", "content": f"{query}. Here is the data: {context_data}"}
    ]

    # Hugging Face API client
    client = InferenceClient(api_key="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")
    
    # Get response from the LLM
    try:
        stream = client.chat.completions.create(
            model="HuggingFaceTB/SmolLM2-1.7B-Instruct", 
            messages=messages, 
            max_tokens=500,
            stream=True
        )
        output = "".join(chunk.choices[0].delta.content for chunk in stream)
    except Exception as e:
        return JsonResponse({"error": f"Error generating response: {str(e)}"}, status=500)
    
    return JsonResponse({"response": output})



def download_data(request):
    # Get parameters from request
    node_id = request.GET.get("node_id")
    start_date = request.GET.get("start_date")
    end_date = request.GET.get("end_date")

    if not node_id or not start_date or not end_date:
        return HttpResponse("Missing required parameters", status=400)

    try:
        node_id = int(node_id)  # Convert node_id to int if needed
        start_date = datetime.fromisoformat(start_date)
        end_date = datetime.fromisoformat(end_date)
    except ValueError:
        return HttpResponse("Invalid date format", status=400)

    # Connect to MongoDB
    client = MongoClient(mongo_uri)
    db = client['sensor_data']
    collection = db['readings']

    # Query MongoDB for the specified node and date range
    query = {
        "node_id": node_id,
        "timestamp": {
            "$gte": start_date,
            "$lt": end_date.replace(hour=23, minute=59, second=59, microsecond=999999)  # End of the selected end day
        }
    }
    projection = {"_id": 0, "timestamp": 1, "battery_voltage": 1, "solar": 1, "pressure": 1}
    readings = collection.find(query, projection).sort("timestamp", 1)

    # Format data
    data = [{
        'timestamp': reading['timestamp'].isoformat(),
        'node_id': reading.get('node_id'),
        'battery_voltage': float(reading['battery_voltage']['$numberDouble']) if isinstance(reading['battery_voltage'], dict) else float(reading['battery_voltage']),
        'solar': float(reading['solar']['$numberDouble']) if isinstance(reading['solar'], dict) else float(reading['solar']),
        'pressure': float(reading['pressure']['$numberDouble']) if isinstance(reading['pressure'], dict) else float(reading['pressure']),
    } for reading in readings]

    # Close the MongoDB connection
    client.close()

    # Prepare CSV response
    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = f"attachment; filename=sensor_data_{node_id}_{start_date.strftime('%Y%m%d')}_{end_date.strftime('%Y%m%d')}.csv"

    # Write data to CSV
    writer = csv.writer(response)
    writer.writerow(["Timestamp", "Node ID", "Battery Voltage", "Solar Power", "Pressure"])

    for record in data:
        writer.writerow([
            convert_iso_to_ist(record["timestamp"]),
            node_id,
            record["battery_voltage"],
            record["solar"],
            record["pressure"]
        ])

    return response



def signup(request):
    if request.method == "POST":
        username = request.POST['username']
        fname = request.POST['fname']
        lname = request.POST['lname']
        email = request.POST['email']
        pass1 = request.POST['pass1']
        pass2 = request.POST['pass2']
        
        if len(username) > 20:
            messages.error(request, "Username must be under 20 characters!")
            return redirect('home')
        
        if pass1 != pass2:
            messages.error(request, "Passwords didn't match!")
            return redirect('home')
        
        if not username.isalnum():
            messages.error(request, "Username must be alphanumeric!")
            return redirect('home')
        
        # Check if username already exists
        if User.objects.filter(username=username).exists():
            messages.error(request, "Username already taken! Please choose another.")
            return render(request, "authentication/signup.html") 
        
        # Create the user
        myuser = User.objects.create_user(username, email, pass1)
        myuser.first_name = fname
        myuser.last_name = lname
        myuser.is_active = True  # Set to inactive for email confirmation (if needed)
        myuser.save()

        messages.success(request, "Your account has been created successfully!")
        return redirect('signin')  # Redirect to signin page after successful signup
        
    return render(request, "authentication/signup.html")

# MongoDB connection details
mongo_uri = 'mongodb+srv://suryanshkgp:m3$JviM$d*X32cB@cluster0.lgvfa.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0'

def get_data(request):
    node_id = request.GET.get('node_id')
    
    client = MongoClient(mongo_uri)
    db = client['sensor_data']
    collection = db['readings']
    
    # Fetch data for the specified node
    readings = list(collection.find({'node_id': int(node_id)}))
    
    data = [{
        'node_id': reading.get('node_id'),
        'battery_voltage': float(reading['battery_voltage']['$numberDouble']) if isinstance(reading['battery_voltage'], dict) else float(reading['battery_voltage']),
        'solar': float(reading['solar']['$numberDouble']) if isinstance(reading['solar'], dict) else float(reading['solar']),
        'pressure': float(reading['pressure']['$numberDouble']) if isinstance(reading['pressure'], dict) else float(reading['pressure']),
        'timestamp': convert_iso_to_ist(reading['timestamp'].isoformat())
    } for reading in readings]

    print(data)  # Print the data to the console for debugging

    client.close()  # Close the client after retrieving data
    return JsonResponse(data, safe=False)  # Use safe=False to allow non-dict objects

def get_sensor_data():
    client = MongoClient(mongo_uri)
    db = client['sensor_data']
    collection = db['readings']
    data = list(collection.find())  # Fetch all data
    client.close()
    return data

def signup(request):
    if request.method == "POST":
        username = request.POST['username']
        fname = request.POST['fname']
        lname = request.POST['lname']
        email = request.POST['email']
        pass1 = request.POST['pass1']
        pass2 = request.POST['pass2']
        
        if len(username) > 20:
            messages.error(request, "Username must be under 20 characters!")
            return redirect('home')
        
        if pass1 != pass2:
            messages.error(request, "Passwords didn't match!")
            return redirect('home')
        
        if not username.isalnum():
            messages.error(request, "Username must be alphanumeric!")
            return redirect('home')
        
        # Check if username already exists
        if User.objects.filter(username=username).exists():
            messages.error(request, "Username already taken! Please choose another.")
            return render(request, "authentication/signup.html") 
        
        # Create the user
        myuser = User.objects.create_user(username, email, pass1)
        myuser.first_name = fname
        myuser.last_name = lname
        myuser.is_active = True  # Set to inactive for email confirmation (if needed)
        myuser.save()

        messages.success(request, "Your account has been created successfully!")
        return redirect('signin')  # Redirect to signin page after successful signup
        
    return render(request, "authentication/signup.html")

def dashboard_view(request):
    if request.user.is_authenticated:
        client = MongoClient(mongo_uri)
        db = client['sensor_data']
        collection = db['readings']
        
        # Get distinct nodes
        node_ids = collection.distinct("node_id")

        # Fetch sensor data
        readings = list(collection.find())
        data = [{
            'node_id': reading.get('node_id'),
            'battery_voltage': float(reading['battery_voltage']['$numberDouble']) if isinstance(reading['battery_voltage'], dict) else float(reading['battery_voltage']),
            'solar': float(reading['solar']['$numberDouble']) if isinstance(reading['solar'], dict) else float(reading['solar']),
            'pressure': float(reading['pressure']['$numberDouble']) if isinstance(reading['pressure'], dict) else float(reading['pressure']),
            'timestamp': reading['timestamp'].isoformat() if isinstance(reading['timestamp'], datetime) else reading['timestamp']
        } for reading in readings]
        
        client.close()

        latest_data = data[-1] if data else None
        return render(request, "authentication/dashboard.html", {
            'data': json.dumps(data),  # Ensures data is always a JSON array
            'latest_data': latest_data,
            'node_ids': node_ids
        })

    else:
        return redirect('login')



def download_csv(request):
    node_id = request.GET.get("node_id")
    start_date = request.GET.get("start_date")
    end_date = request.GET.get("end_date")

    # Connect to MongoDB
    client = MongoClient(mongo_uri)
    db = client['sensor_data']
    collection = db['readings']

    # Query the data based on node_id and date range
    query = {"node_id": int(node_id)}
    if start_date and end_date:
        query['timestamp'] = {
            '$gte': datetime.strptime(start_date, "%Y-%m-%d"),
            '$lte': datetime.strptime(end_date, "%Y-%m-%d")
        }

    # Fetch data
    readings = collection.find(query)
    client.close()

    # Create the CSV response
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="node_{node_id}_data.csv"'

    writer = csv.writer(response)
    writer.writerow(['Node ID', 'Battery Voltage', 'Solar Power', 'Pressure', 'Timestamp'])

    for reading in readings:
        writer.writerow([
            reading.get('node_id'),
            reading.get('battery_voltage'),
            reading.get('solar'),
            reading.get('pressure'),
            reading.get('timestamp').isoformat()
        ])

    return response


def signin(request):
    if request.method == 'POST':
        username = request.POST['username']
        pass1 = request.POST['pass1']  # Change this to 'pass1' if you want to keep it consistent with the form

        user = authenticate(username=username, password=pass1)
        
        if user is not None:
            login(request, user)
            return redirect('dashboard')  # Redirect to the dashboard_view instead of rendering it directly
        else:
            messages.error(request, "Bad Credentials!!")
            return redirect('home')
    
    return render(request, "authentication/index.html")

def signout(request):
    logout(request)
    messages.success(request, "Logged Out Successfully!!")
    return redirect('home')

