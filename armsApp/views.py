import datetime
from django.shortcuts import redirect, render
from django.shortcuts import render, redirect, get_object_or_404
import json
from django.contrib import messages
from django.contrib.auth.models import User
from django.http import HttpResponse
import face_recognition
from armsApp import models, forms
from django.db.models import Q
from django.contrib.auth import authenticate, login, logout, update_session_auth_hash
from django.contrib.auth.decorators import login_required
import numpy as np
from PIL import Image
import base64
from io import BytesIO







@login_required(login_url='login-page')
def reserve_form(request, pk=None):
    if pk is None:
        messages.error(request, "Invalid Flight ID")
        return redirect('public-page')
    flight = get_object_or_404(models.Flights, id=pk)
    context = {
        'flight': flight,
        'page': 'Reservation',
        # other context data...
    }
    return render(request, 'reservation.html', context)


def context_data():
    context = {
        'page_name' : '',
        'page_title' : '',
        'system_name' : 'Airlines Reservation Managament System',
        'topbar' : True,
        'footer' : True,
    }

    return context
    
def userregister(request):
    context = context_data()
    context['topbar'] = False
    context['footer'] = False
    context['page_title'] = "User Registration"
    if request.user.is_authenticated:
        return redirect("home-page")
    return render(request, 'register.html', context)

@login_required
def upload_modal(request):
    context = context_data()
    return render(request, 'upload.html', context)

def save_register(request):
    resp = {'status': 'failed', 'msg': ''}
    if request.method != 'POST':
        resp['msg'] = "No data has been sent on this request"
    else:
        # Debug: print incoming POST and FILES data to the console
        print("POST data:", request.POST)
        print("FILES data:", request.FILES)
        
        # Include request.FILES when creating the form instance
        form = forms.SaveUser(request.POST, request.FILES)
        if form.is_valid():
            user = form.save()
            messages.success(request, "Your Account has been created successfully")
            resp['status'] = 'success'
        else:
            for field in form:
                for error in field.errors:
                    if resp['msg']:
                        resp['msg'] += '<br />'
                    resp['msg'] += f"[{field.name}] {error}."
            # Debug: print form errors to the console
            print("Form errors:", resp['msg'])
    return HttpResponse(json.dumps(resp), content_type="application/json")


@login_required
def update_profile(request):
    context = context_data()
    context['page_title'] = 'Update Profile'
    user = User.objects.get(id = request.user.id)
    if not request.method == 'POST':
        form = forms.UpdateProfile(instance=user)
        context['form'] = form
        print(form)
    else:
        form = forms.UpdateProfile(request.POST, instance=user)
        if form.is_valid():
            form.save()
            messages.success(request, "Profile has been updated")
            return redirect("profile-page")
        else:
            context['form'] = form
            
    return render(request, 'manage_profile.html',context)

@login_required
def update_password(request):
    context =context_data()
    context['page_title'] = "Update Password"
    if request.method == 'POST':
        form = forms.UpdatePasswords(user = request.user, data= request.POST)
        if form.is_valid():
            form.save()
            messages.success(request,"Your Account Password has been updated successfully")
            update_session_auth_hash(request, form.user)
            return redirect("profile-page")
        else:
            context['form'] = form
    else:
        form = forms.UpdatePasswords(request.POST)
        context['form'] = form
    return render(request,'update_password.html',context)

# Create your views here.
def login_page(request):
    context = context_data()
    context['topbar'] = False
    context['footer'] = False
    context['page_name'] = 'login'
    context['page_title'] = 'Login'
    return render(request, 'login.html', context)

from django.contrib.auth import authenticate, login, logout
from django.shortcuts import render, redirect
from django.contrib import messages

def login_user(request):
    # Optionally log out any current session
    logout(request)
    
    if request.method == "POST":
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        user = authenticate(username=username, password=password)
        if user is not None:
            if user.is_active:
                login(request, user)
                if user.is_staff or user.is_superuser:
                    return redirect('/admin/')
                else:
                    return redirect('home-page')
            else:
                messages.error(request, "Account disabled.")
        else:
            messages.error(request, "Incorrect username or password.")
    
    return render(request, 'login.html')

import jwt
from django.conf import settings
from django.contrib.auth import login
from django.contrib.auth.models import User
from django.http import JsonResponse
from rest_framework_simplejwt.tokens import UntypedToken
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError

def jwt_session_login(request):
    """
    Accepts a POST with a JWT access token, validates it, and logs the user in
    by creating a Django session.
    """
    token = request.POST.get('token')
    try:
        # Validate token (raises error if invalid)
        UntypedToken(token)
        # Decode token to get the user ID (the payload key may differ based on your settings)
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
        user_id = payload.get('user_id')
        user = CustomUser.objects.get(id=user_id)
        login(request, user)
        return JsonResponse({'status': 'success'})
    except (InvalidToken, TokenError, CustomUser.DoesNotExist) as e:
        return JsonResponse({'status': 'failed', 'msg': 'Token invalid or user not found.'})


def search_flight(request):
    context = context_data()
    context['page'] = 'Search Available Flight'
    airlines = models.Airlines.objects.filter(delete_flag = 0, status = 1).all()
    airports = models.Airport.objects.filter(delete_flag = 0, status = 1).all()
    context['airlines'] = airlines
    context['airports'] = airports
    
    return render(request,'search_flight.html', context)

def search_result(request, fromA=None, toA=None, departure = None):
    context = context_data()
    context['page'] = 'Search Result'
    if fromA is None and toA is None and departure is None:
        messages.error(request, "Invalid Search Inputs")
        return redirect('public-page')
    else:
        departure = datetime.datetime.strptime(departure, "%Y-%m-%d")
        year = departure.strftime("%Y")
        month = departure.strftime("%m")
        day = departure.strftime("%d")
        context['flights'] = models.Flights.objects.filter(delete_flag=0,
                        departure__year = year,
                        departure__month = month,
                        departure__day = day,
                        ).order_by('departure').all()
        return render(request, 'search_result.html', context)

def save_reservation(request):
    resp = { 'status': 'failed', 'msg':'' }
    if not request.method == 'POST':
       resp['msg'] = "No data has been sent."
    else:
        form = forms.SaveReservation(request.POST)
        if form.is_valid():
            form.save()
            resp['status'] = 'success'
            resp['msg'] = "Your Reservation has been sent. Our staff will reach as soon we sees your reservation. Thank you!"
            messages.success(request,f"{resp['msg']}")
        else:
            for field in form:
                for error in field.errors:
                    if not resp['msg'] == '':
                        resp['msg'] += str("<br />")

                    resp['msg'] += str(f"[{field.name}] {error}")
    return HttpResponse(json.dumps(resp), content_type="application/json")

# def reserve_form(request, pk=None):
#     context = context_data()
#     context['page'] = 'Search Result'
#     if pk is None:
#         messages.error(request, "Invalid Flight ID")
#         return redirect('public-page')
#     else:
#         context['flight'] = models.Flights.objects.get(id=pk)
#         return render(request, 'reservation.html', context)


@login_required
def home(request):
    context = context_data()
    context['page'] = 'home'
    context['page_title'] = 'Home'
    context['airlines'] = models.Airlines.objects.filter(delete_flag=0, status = 1).count()
    context['airport'] = models.Airport.objects.filter(delete_flag=0, status = 1).count()
    now = datetime.datetime.now()
    year = now.strftime("%Y")
    month = now.strftime("%m")
    day = now.strftime("%d")
    hour = now.strftime("%H")
    context['flight'] = models.Flights.objects.filter(delete_flag=0,
                            departure__year__gte = year,
                            departure__month__gte = month,
                            departure__day__gte = day,
                            departure__hour__gte = hour,
                            ).count()
    return render(request, 'home.html', context)

def logout_user(request):
    logout(request)
    return redirect('login-page')
    
@login_required
def profile(request):
    context = context_data()
    context['page'] = 'profile'
    context['page_title'] = "Profile"
    return render(request,'profile.html', context)

#Airline
@login_required
def list_airline(request):
    context = context_data()
    context['page_title'] ="Airlines"
    context['airlines'] = models.Airlines.objects.filter(delete_flag = 0).all()
    return render(request, 'airlines.html', context) 

@login_required
def manage_airline(request, pk = None):
    if pk is None:
        airline = {}
    else:
        airline = models.Airlines.objects.get(id = pk)
    context = context_data()
    context['page_title'] ="Manage Airline"
    context['airline'] = airline
    return render(request, 'manage_airline.html', context) 

@login_required
def save_airline(request):
    resp = { 'status': 'failed', 'msg':'' }
    if not request.method == 'POST':
       resp['msg'] = "No data has been sent."
    else:
        post = request.POST
        if not post['id'] == '':
            airline = models.Airlines.objects.get(id = post['id'])
            form = forms.SaveAirlines(request.POST, request.FILES, instance = airline)
        else:
            form = forms.SaveAirlines(request.POST, request.FILES)

        if form.is_valid():
            form.save()
            resp['status'] = 'success'
            if post['id'] == '':
                resp['msg'] = "New Airline has been added successfully."
            else:
                resp['msg'] = "Airline Details has been updated successfully."
            messages.success(request,f"{resp['msg']}")
        else:
            for field in form:
                for error in field.errors:
                    if not resp['msg'] == '':
                        resp['msg'] += str("<br />")

                    resp['msg'] += str(f"[{field.name}] {error}")
    return HttpResponse(json.dumps(resp), content_type="application/json")

@login_required
def delete_airline(request, pk=None):
    resp = { 'status' : 'failed', 'msg' : '' }
    if pk is None:
        resp['msg'] = 'No ID has been sent'
    else:
        try:
            models.Airlines.objects.filter(id = pk).update(delete_flag = 1)
            resp['status'] = 'success'
            messages.success(request, "Airline has been deleted successfully")
        except:
            resp['msg'] = 'Airline has failed to delete'
    return HttpResponse(json.dumps(resp), content_type="application/json")

    
#Airport
@login_required
def list_airport(request):
    context = context_data()
    context['page_title'] ="Airports"
    context['airports'] = models.Airport.objects.filter(delete_flag = 0).all()
    return render(request, 'airports.html', context) 

@login_required
def manage_airport(request, pk = None):
    if pk is None:
        airport = {}
    else:
        airport = models.Airport.objects.get(id = pk)
    context = context_data()
    context['page_title'] ="Manage Airport"
    context['airport'] = airport
    return render(request, 'manage_airport.html', context) 

@login_required
def save_airport(request):
    resp = { 'status': 'failed', 'msg':'' }
    if not request.method == 'POST':
       resp['msg'] = "No data has been sent."
    else:
        post = request.POST
        if not post['id'] == '':
            airport = models.Airport.objects.get(id = post['id'])
            form = forms.SaveAirports(request.POST, instance = airport)
        else:
            form = forms.SaveAirports(request.POST)

        if form.is_valid():
            form.save()
            resp['status'] = 'success'
            if post['id'] == '':
                resp['msg'] = "New Airport has been added successfully."
            else:
                resp['msg'] = "Airport Details has been updated successfully."
            messages.success(request,f"{resp['msg']}")
        else:
            for field in form:
                for error in field.errors:
                    if not resp['msg'] == '':
                        resp['msg'] += str("<br />")

                    resp['msg'] += str(f"[{field.name}] {error}")
    return HttpResponse(json.dumps(resp), content_type="application/json")

@login_required
def delete_airport(request, pk=None):
    resp = { 'status' : 'failed', 'msg' : '' }
    if pk is None:
        resp['msg'] = 'No ID has been sent'
    else:
        try:
            models.Airport.objects.filter(id = pk).update(delete_flag = 1)
            resp['status'] = 'success'
            messages.success(request, "Airport has been deleted successfully")
        except:
            resp['msg'] = 'airport has failed to delete'
    return HttpResponse(json.dumps(resp), content_type="application/json")

#Flight
@login_required
def list_flight(request):
    context = context_data()
    context['page_title'] ="Flights"
    context['flights'] = models.Flights.objects.filter(delete_flag = 0).all()
    return render(request, 'flights.html', context) 

@login_required
def manage_flight(request, pk = None):
    if pk is None:
        flight = {}
    else:
        flight = models.Flights.objects.get(id = pk)
    airlines = models.Airlines.objects.filter(delete_flag = 0, status = 1).all()
    airports = models.Airport.objects.filter(delete_flag = 0, status = 1).all()
    context = context_data()
    context['page_title'] ="Manage Flight"
    context['flight'] = flight
    context['airlines'] = airlines
    context['airports'] = airports
    return render(request, 'manage_flight.html', context) 

@login_required
def save_flight(request):
    resp = { 'status': 'failed', 'msg':'' }
    if not request.method == 'POST':
       resp['msg'] = "No data has been sent."
    else:
        post = request.POST
        if not post['id'] == '':
            Flight = models.Flights.objects.get(id = post['id'])
            form = forms.SaveFlights(request.POST, instance = Flight)
        else:
            form = forms.SaveFlights(request.POST)

        if form.is_valid():
            form.save()
            resp['status'] = 'success'
            if post['id'] == '':
                resp['msg'] = "New Flight has been added successfully."
            else:
                resp['msg'] = "Flight Details has been updated successfully."
            messages.success(request,f"{resp['msg']}")
        else:
            for field in form:
                for error in field.errors:
                    if not resp['msg'] == '':
                        resp['msg'] += str("<br />")

                    resp['msg'] += str(f"[{field.name}] {error}")
    return HttpResponse(json.dumps(resp), content_type="application/json")

@login_required
def view_flight(request, pk = None):
    if pk is None:
        flight = {}
    else:
        flight = models.Flights.objects.get(id = pk)
    context = context_data()
    context['page_title'] ="Flight Details"
    context['flight'] = flight
    return render(request, 'view_flight_details.html', context) 

@login_required
def delete_flight(request, pk=None):
    resp = { 'status' : 'failed', 'msg' : '' }
    if pk is None:
        resp['msg'] = 'No ID has been sent'
    else:
        try:
            models.Flights.objects.filter(id = pk).update(delete_flag = 1)
            resp['status'] = 'success'
            messages.success(request, "Flight has been deleted successfully")
        except:
            resp['msg'] = 'Flight has failed to delete'
    return HttpResponse(json.dumps(resp), content_type="application/json")

#Reservation
@login_required
def list_reservation(request):
    context = context_data()
    context['page_title'] ="Reservations"
    context['reservations'] = models.Reservation.objects.all()
    return render(request, 'reservation_list.html', context) 

@login_required
def view_reservation(request, pk = None):
    if pk is None:
        reservation = {}
    else:
        reservation = models.Reservation.objects.get(id = pk)
    context = context_data()
    context['page_title'] ="Reservation Details"
    context['reservation'] = reservation
    return render(request, 'view_reservation_details.html', context) 

@login_required
def delete_reservation(request, pk=None):
    resp = { 'status' : 'failed', 'msg' : '' }
    if pk is None:
        resp['msg'] = 'No ID has been sent'
    else:
        try:
            models.Reservation.objects.filter(id = pk).delete()
            resp['status'] = 'success'
            messages.success(request, "Reservation has been deleted successfully")
        except:
            resp['msg'] = 'Reservation has failed to delete'
    return HttpResponse(json.dumps(resp), content_type="application/json")

@login_required
def update_reservation(request):
    resp = { 'status' : 'failed', 'msg' : '' }
    if not request.method == 'POST':
        resp['msg'] = 'No ID has been sent'
    else:
        try:
            models.Reservation.objects.filter(id = request.POST['id']).update(status=request.POST['status'])
            resp['status'] = 'success'
            messages.success(request, "Reservation Status has been updated successfully")
        except:
            resp['msg'] = 'Reservation Status has failed to update'
    return HttpResponse(json.dumps(resp), content_type="application/json")

def confirmed_reservations(request):
    # Here, we assume the Reservation.email field matches the logged-in user's email.
    reservations = models.Reservation.objects.filter(email=request.user.email, status='1')
    return render(request, 'confirmed_reservations.html', {'reservations': reservations})

# views.py
import paypalrestsdk
from django.conf import settings
from django.shortcuts import redirect, render, get_object_or_404
from .models import Reservation

def create_payment(request, reservation_id):
    # Configure the PayPal SDK with credentials from settings
    paypalrestsdk.configure({
        "mode": "sandbox",  # or "live" when in production
        "client_id": settings.PAYPAL_CLIENT_ID,
        "client_secret": settings.PAYPAL_CLIENT_SECRET,
    })

    # Optionally, retrieve the reservation from the database.
    reservation = get_object_or_404(Reservation, pk=reservation_id, status='1')

    # Use a fixed price for demonstration; adjust as needed.
    price = "10.00"
    
    payment = paypalrestsdk.Payment({
        "intent": "sale",
        "payer": {
            "payment_method": "paypal"
        },
        "redirect_urls": {
            "return_url": "http://127.0.0.1:8000/payment/execute/",
            "cancel_url": "http://127.0.0.1:8000/payment/cancel/"
        },
        "transactions": [{
            "item_list": {
                "items": [{
                    "name": "Reservation Payment",
                    "sku": "001",
                    "price": price,
                    "currency": "USD",
                    "quantity": 1
                }]
            },
            "amount": {
                "total": price,
                "currency": "USD"
            },
            "description": f"Payment for confirmed reservation #{reservation.pk}."
        }]
    })

    if payment.create():
        # Extract approval URL to redirect the user
        for link in payment.links:
            if link.rel == "approval_url":
                approval_url = str(link.href)
                return redirect(approval_url)
    else:
        # Log error or display a message
        return render(request, "error.html", {"error": payment.error})
    

from django.shortcuts import render, redirect
import paypalrestsdk
from django.conf import settings


def execute_payment(request):
    paypalrestsdk.configure({
        "mode": "sandbox",  # or "live"
        "client_id": settings.PAYPAL_CLIENT_ID,
        "client_secret": settings.PAYPAL_CLIENT_SECRET,
    })

    payment_id = request.GET.get("paymentId")
    payer_id = request.GET.get("PayerID")

    if not payment_id or not payer_id:
        return render(request, "payment/error.html", {"error": "Missing payment information"})

    payment = paypalrestsdk.Payment.find(payment_id)

    if payment.execute({"payer_id": payer_id}):
        # You can extract payment details and pass them to the template
        return render(request, "success.html", {
            "payment_id": payment.id,
            "payer_id": payer_id,
            "amount": payment.transactions[0].amount.total,
            "currency": payment.transactions[0].amount.currency,
            "status": payment.state,
        })
    else:
        return render(request, "error.html", {"error": payment.error})


def get_face_encoding(uploaded_file):
    image = face_recognition.load_image_file(uploaded_file)
    encodings = face_recognition.face_encodings(image)
    return encodings[0] if encodings else None


from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.core.files.base import ContentFile
from django.contrib.auth import login
from django.contrib.auth.models import User


import base64
import face_recognition
import numpy as np





from django.shortcuts import render, redirect
from django.contrib.auth import login
from django.contrib import messages
from . import forms
from .models import CustomUser  # Assuming you have a custom user model with a photo field.

def register_user(request):
    if request.user.is_authenticated:
        print("User is already authenticated. Redirecting to home.")
        return redirect("home-page")

    if request.method == "POST":
        form = forms.SaveUser(request.POST, request.FILES)
        if form.is_valid():
            # Save the user with the form data
            user = form.save()
            print(f"User created: {user.username}")

            # Get the face image from the request
            face_image = request.FILES.get("face_image")
            if not face_image:
                messages.error(request, "Please upload a face image.")
                print("Face image not provided.")
                return render(request, "register.html", {"form": form})

            # Save the face image directly to the user model (assuming you added 'photo' field to user)
            user.photo = face_image
            user.save()  # Don't forget to save the user after updating the photo field.
            print(f"Face image uploaded for user: {user.username}")

            messages.success(request, "Your account has been created successfully!")

            # Optionally log the user in immediately
            login(request, user)
            print(f"User {user.username} logged in.")
            return redirect("home-page")
        else:
            print("Form is invalid.")
            messages.error(request, "There was an error with your registration. Please check the form.")
    else:
        print("GET request received, showing registration form.")
        form = forms.SaveUser()

    return render(request, "register.html", {"form": form})




import base64
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from django.core.files.base import ContentFile

import face_recognition

import base64
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from django.core.files.base import ContentFile
from django.contrib.auth.decorators import login_required

import face_recognition
import tempfile
import os
from django.core.files.storage import default_storage

@login_required
def face_verification(request):
    return render(request, "face_verification.html")

@login_required
def verify_face(request):
    if request.method == 'POST':
        try:
            body = json.loads(request.body)
            image_data = body.get("image")

            if not image_data:
                return JsonResponse({'status': 'error', 'message': 'No image provided'}, status=400)

            if not request.user.photo:
                return JsonResponse({'status': 'error', 'message': 'User does not have a profile photo'}, status=400)

            # Decode base64 image
            image_str = image_data.split(',')[1]
            img_data = base64.b64decode(image_str)

            # Ensure 'user_photos' directory exists inside MEDIA_ROOT
            upload_dir = os.path.join(settings.MEDIA_ROOT, 'user_photos')
            os.makedirs(upload_dir, exist_ok=True)

            # Define path relative to MEDIA_ROOT for default_storage
            temp_image_name = f"{request.user.username}_webcam.jpg"
            temp_image_rel_path = os.path.join('user_photos', temp_image_name)

            # Save using Django's storage system
            temp_image_full_path = default_storage.save(temp_image_rel_path, ContentFile(img_data))

            # Get full filesystem path to saved webcam image
            webcam_image_path = os.path.join(settings.MEDIA_ROOT, temp_image_rel_path)

            # Load images
            stored_image = face_recognition.load_image_file(request.user.photo.path)
            webcam_image = face_recognition.load_image_file(webcam_image_path)

            # Get encodings
            stored_face_encoding = face_recognition.face_encodings(stored_image)
            webcam_face_encoding = face_recognition.face_encodings(webcam_image)

            # Check for detected faces
            if len(stored_face_encoding) == 0 or len(webcam_face_encoding) == 0:
                return JsonResponse({'status': 'error', 'message': 'No faces detected in one or both images'}, status=400)

            # Compare faces
            match_result = face_recognition.compare_faces([stored_face_encoding[0]], webcam_face_encoding[0])

            # Clean up temp image
            if os.path.exists(webcam_image_path):
                os.remove(webcam_image_path)

            if match_result[0]:
                return JsonResponse({'status': 'success'})
            else:
                return JsonResponse({'status': 'fail', 'message': 'Face mismatch'})

        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=500)

    return JsonResponse({'status': 'error', 'message': 'Invalid request'}, status=400)
