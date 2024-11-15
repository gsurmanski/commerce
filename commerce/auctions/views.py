from django.contrib.auth import authenticate, login, logout
from django.db import IntegrityError
from django.db.models import Max
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render, redirect
from django.urls import reverse
from django.contrib import messages
#import decimal for precision of numbers and compatibility with decimal field in Bid model
from decimal import Decimal, InvalidOperation

from .models import *


def index(request):
    listings = Listing.objects.all()

    return render(request, "auctions/index.html",{
                  "listings": listings
                  })

def listing(request, id):
    listing = Listing.objects.get(id=id)
    error = {}

    #check if already added to watchlist to render correct button
    is_in_watchlist = Watchlist.objects.filter(listing=listing, user=request.user).exists()
    
    #if any button is pressed
    if request.method == "POST":
        action = request.POST["action"]

        #if add watchlists form
        if action == "add_watchlist":
            #check database for other watchlist entries
            if Watchlist.objects.filter(user=request.user, listing=listing).exists():
                error["database"] = "entry exists"
            else:
                watchlist = Watchlist(user=request.user, listing=listing)
                watchlist.save()
                messages.success(request, "watchlist saved")

        elif action =="remove_watchlist":
            Watchlist.objects.filter(user=request.user, listing=listing).delete()
            messages.success(request, "watchlist entry deleted")
        #if bid placed
        elif action == "place_bid":
            try:
                bid = Decimal(request.POST["bid"])
                # Retrieve the highest bid amount using aggregate(Max)
                # Get the Bid object with the highest bid for the listing. -amount is sort by descending
                highest_bid = Bid.objects.filter(listing=listing).order_by('-amount').first()
                same_bid = Bid.objects.filter(listing=listing, user=request.user, amount=bid).exists()
                #check if bid not empty
                if not bid:
                    messages.error(request, "Enter a valid bid.")
                #check if bid higher than min bid set
                elif bid < listing.start_bid:
                    messages.error(request, "your bid isn't higher than the minimum bid")
                #check if bid is higher than highest bid
                elif highest_bid and bid <= highest_bid.amount:
                    messages.error(request, "your bid must be higher than the highest bid")
                #check if you are trying to enter the same bid as you already did
                elif same_bid:
                    messages.error(request, "you can't enter the same bid twice")
                else:
                    new_bid = Bid(amount=bid, listing=listing, user=request.user)
                    new_bid.save()
                    messages.success(request, "Your bid has been placed successfully.")

            except (InvalidOperation, ValueError):
                messages.error(request, "invalid bid")

         # After handling POST, redirect to avoid resubmission on refresh
        return redirect('listing', id=id)
    
    #default rendering        
    return render(request, "auctions/listing.html",{
                  "listing": listing,
                  "error": error,
                  'is_in_watchlist': is_in_watchlist
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
