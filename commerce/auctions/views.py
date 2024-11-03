from django.contrib.auth import authenticate, login, logout
from django.db import IntegrityError
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render
from django.urls import reverse

from .models import *


def index(request):
    listings = Listing.objects.all()

    return render(request, "auctions/index.html",{
                  "listings": listings
                  })

def listing(request, id):
    listing = Listing.objects.get(id=id)

    return render(request, "auctions/listing.html",{
                  "listing": listing
                  })

def login_view(request):
    if request.method == "POST":

        # Attempt to sign user in
        username = request.POST["username"]
        password = request.POST["password"]
        user = authenticate(request, username=username, password=password)

        # Check if authentication successful
        if user is not None:
            login(request, user)
            return HttpResponseRedirect(reverse("index"))
        else:
            return render(request, "auctions/login.html", {
                "message": "Invalid username and/or password."
            })
    else:
        return render(request, "auctions/login.html")


def logout_view(request):
    logout(request)
    return HttpResponseRedirect(reverse("index"))


def register(request):
    if request.method == "POST":
        username = request.POST["username"]
        email = request.POST["email"]

        # Ensure password matches confirmation
        password = request.POST["password"]
        confirmation = request.POST["confirmation"]
        if password != confirmation:
            return render(request, "auctions/register.html", {
                "message": "Passwords must match."
            })

        # Attempt to create new user
        try:
            user = User.objects.create_user(username, email, password)
            user.save()
        except IntegrityError:
            return render(request, "auctions/register.html", {
                "message": "Username already taken."
            })
        login(request, user)
        return HttpResponseRedirect(reverse("index"))
    else:
        return render(request, "auctions/register.html")


def create_listing(request):
    if request.method == "POST":
        title = request.POST["title"]
        description = request.POST["description"]
        #testing get since POST is a dictionary by default
        start_bid = request.POST.get("starting_bid", "")
        image_url = request.POST["image_url"]
        #error check
        errors = {}

        if title == "":
            errors["title"]="title cannot be blank"
        
        if start_bid == "":
            start_bid = 0.01
        else:
            try:
                start_bid = float(start_bid)
            except ValueError:
                errors["starting_bid"]="an issue with the starting bid format"
        
        if errors:
            return render (request, "auctions/create_listing.html", {
                    "errors": errors
                })
    
        #pass user.id from request
        listing = Listing(user=request.user, title=title, description=description, start_bid=start_bid, current_price=start_bid, image_url=image_url)
        listing.save()
        return HttpResponseRedirect(reverse("index"))
    
    else:
        #return default page if not post form
        return render(request, "auctions/create_listing.html")
