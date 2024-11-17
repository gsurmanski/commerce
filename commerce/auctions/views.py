from django.contrib.auth import authenticate, login, logout
from django.db import IntegrityError
from django.db.models import Max
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render, redirect
from django.urls import reverse
from django.contrib import messages
#import decimal for precision of numbers and compatibility with decimal field in Bid model
from decimal import Decimal, InvalidOperation
#login auth decorator
from django.contrib.auth.decorators import login_required

from django.shortcuts import get_object_or_404

from .models import *


def index(request):
    listings = Listing.objects.all()

    return render(request, "auctions/index.html",{
                  "listings": listings
                  })

def listing(request, id):
    listing = get_object_or_404(Listing, id=id)
    # Initialize is_in_watchlist to False in case user is not logged in
    is_in_watchlist = False
    # Get the Bid object with the highest bid for the listing. -amount is sort by descending
    highest_bid = Bid.objects.filter(listing=listing).order_by('-amount').first()

    # If no bids exist, create a "default" Bid object
    if highest_bid is None:
        # Create a fake Bid object (this will not save to the database, just a temporary placeholder)
        highest_bid = Bid(amount=listing.current_price, user=listing.user, listing=listing)

    #check if listing is closed
    closed = Closed.objects.filter(listing=listing).exists()

    #get any comments
    comments = Comment.objects.filter(listing=listing)

    # Check if the user is authenticated before querying for the watchlist
    if request.user.is_authenticated:
        is_in_watchlist = Watchlist.objects.filter(listing=listing, user=request.user).exists()

    #if any button is pressed
    if request.method == "POST":
        action = request.POST.get("action")
        
        #if add watchlists form
        if action == "add_watchlist":
            if request.user.is_authenticated:
                #check database for other watchlist entries
                if Watchlist.objects.filter(user=request.user, listing=listing).exists():
                    messages.error(request, "entry exists")
                else:
                    watchlist = Watchlist(user=request.user, listing=listing)
                    watchlist.save()
                    messages.success(request, "watchlist saved")
            else:
                messages.error(request, "you aren't logged in")

        elif action == "remove_watchlist":
            Watchlist.objects.filter(user=request.user, listing=listing).delete()
            messages.success(request, "watchlist entry deleted")
        #if bid placed

        elif action == "place_bid":
            try:
                bid = Decimal(request.POST["bid"])
                # Retrieve the highest bid amount using aggregate(Max)
                same_bid = Bid.objects.filter(listing=listing, user=request.user, amount=bid).exists()
                #check if bid not empty
                if bid <= 0:
                    messages.error(request, "Enter a valid bid greater than zero.")
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

                    #update listing with new price
                    listing.current_price = bid
                    listing.save()

            except (InvalidOperation, ValueError):
                messages.error(request, "invalid bid")

        elif action == "close_auction":
            if request.user.is_authenticated and request.user == listing.user:
                if Closed.objects.filter(listing=listing).exists():
                    messages.error(request, "this is already closed")
                else:
                    messages.success(request, f'sure we\'ll close it. {highest_bid.user} won')
                    Closed(listing=listing).save()

        elif action == "comment":
            comment = request.POST.get("comment")
            if request.user.is_authenticated and comment != "":
                Comment(text=comment, listing=listing, user= request.user).save()
                messages.success(request, "comment added")
            else:
                messages.error(request, "type something")

         # After handling POST, redirect to avoid resubmission on refresh
        return redirect('listing', id=id)
    
    #default rendering        
    return render(request, "auctions/listing.html",{
                  "listing": listing,
                  'is_in_watchlist': is_in_watchlist,
                  'closed': closed,
                  'highest_bid': highest_bid,
                  'comments': comments
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

@login_required
def create_listing(request):
    if request.method == "POST":
        title = request.POST["title"]
        description = request.POST["description"]
        #testing get since POST is a dictionary by default
        start_bid = request.POST.get("starting_bid", "")
        image_url = request.POST["image_url"]
        category = request.POST["category"]

        if title.strip() == "":
           messages.error(request, "title cannot be blank")
           return redirect('create_listing')
        elif category.strip() == "":
           messages.error(request, "category cannot be blank")
           return redirect('create_listing')
        
        if start_bid.strip() == "":
            start_bid = 0.01
        else:
            try:
                start_bid = Decimal(start_bid)
            except ValueError:
                messages.error(request, "an issue with the starting bid format")
                return redirect('create_listing')
            
        #pass user.id from request
        listing = Listing(user=request.user, title=title, description=description, start_bid=start_bid, current_price=start_bid, image_url=image_url, category=category)
        listing.save()
        return redirect('index')
    
    else:
        #return default page if not post form
        return render(request, "auctions/create_listing.html")

def watchlist(request):
    # Get all listing IDs associated with the user's watchlist
    listing_ids = Watchlist.objects.filter(user=request.user).values_list('listing', flat=True)

    # Get all Listings that match these IDs
    listings = Listing.objects.filter(id__in=listing_ids)

    return render(request, "auctions/watchlist.html",{
                  "listings": listings
                  })

def categories(request):
    # Get all listing IDs associated with the user's watchlist
    categories = Listing.objects.values('category').distinct()
    
    return render(request, "auctions/categories.html",{
                  "categories": categories
                  })

def category(request, category):
    # Get all listing IDs associated with the user's watchlist
    listings = Listing.objects.filter(category=category)

    return render(request, "auctions/category.html",{
                  "listings": listings
                  })