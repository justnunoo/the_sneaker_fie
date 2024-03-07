from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from .models import Product, Cart,  ShoeColor, ShoeSize, UserProfile, Favorite, Order, OrderItem
import random, time, os
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth.models import User, auth 
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Sum
from django.http import JsonResponse
from django.template.loader import render_to_string
from django.utils import timezone


# Create your views here.
def home(request):

    products = Product.objects.all()
    products = list(products)
    random.seed(time.time())
    random.shuffle(products)
    
    # Calculate discounted prices for each product
    for product in products:
        if product.discount:
            discount_percent = product.discount_percent
            discounted_price = product.price * (100 - discount_percent) / 100
            product.discounted_price = discounted_price
        else:
            product.discounted_price = product.price

    context = {'products' : products}
    return render(request, 'mains/home.html', context)

# def get_filtered_boxes(brand):
#     source = f"static\\{brand.lower()}"
#     boxee = Product.objects.all()
#     boxed = list(boxee)
#     random.seed(time.time())
#     random.shuffle(boxed)

#     boxes = [i for i in boxed if os.path.dirname(os.path.join("static", i.image_path)) == source]

#     return boxes

# def display_brand(request, brand):
#     boxes = get_filtered_boxes(brand)

#     # Calculate discounted prices for each product
#     for box in boxes:
#         if box.discount:
#             discount_percent = box.discount_percent
#             discounted_price = box.price * (100 - discount_percent) / 100
#             box.discounted_price = discounted_price
#         else:
#             box.discounted_price = box.price

#     brand_name = brand.upper()
    
#     context = {'boxes': boxes, 'brand_name' : brand_name}

#     return render(request, f'brands/{brand}.html', context)

def display_by_brand(request, brand):
    products = Product.objects.filter(brands = brand)

    discounted_products = []
    for product in products:
        #check if product is discounted
        if product.discount:
            discount_percent = product.discount_percent

            #calculate the discount price
            discounted_price = product.price * (100 - discount_percent) / 100
            product.discounted_price = discounted_price
        else:
            #if not discounted, use regular price
            product.discounted_price = product.price

        discounted_products.append(product)

    brand_name = brand.upper()
    context = {'products' : discounted_products,
               'brand_name' : brand_name}
    return render(request, f'brands/{brand}.html', context)

def adidas(request):
    return display_by_brand(request, 'adidas')

def nike(request):
    return display_by_brand(request, 'nike')

def jordan(request):
    return display_by_brand(request, 'jordan')

def puma(request):
    return display_by_brand(request, 'puma')

def new_balance(request):
    return display_by_brand(request, 'new_balance')

def vans(request):
    return display_by_brand(request, 'vans')

def reebok(request):
    return display_by_brand(request, 'reebok')

def balenciaga(request):
    return display_by_brand(request, 'balenciaga')


#login and register
LOGIN_OR_REGISTER = 'authentication/login_or_register.html'

def login(request):
    if request.method == 'POST' and 'login' in request.POST:
        username = request.POST['username']
        password = request.POST['password']

        # Authenticate user credentials
        user = auth.authenticate(request, username=username, password=password)

        if user is not None:
            auth.login(request, user)

            # Retrieve product_id from session and redirect accordingly
            selected_product_id = request.session.pop('selected_product_id', None)
            if selected_product_id is not None:
                redirect_url = reverse('product_detail', args=[selected_product_id])
            else:
                redirect_url = reverse('home')  # Set your default redirect URL

            return redirect(redirect_url)
        else:
            messages.error(request, 'Invalid credentials')

    return render(request, LOGIN_OR_REGISTER)

def register(request):
    if request.method == 'POST' and 'signup' in request.POST:
        username = request.POST['username']
        number = request.POST.get('user_number')
        email = request.POST['email']
        password1 = request.POST['password1']
        password2 = request.POST['password2']

        # Check if passwords match
        if password1 != password2:
            messages.error(request, 'Passwords do not match. Please try again.')
        else:
            # Check if username already exists
            if User.objects.filter(username=username).exists():
                messages.error(request, 'Username already exists')
            # Check if email already exists
            elif User.objects.filter(email=email).exists():
                messages.error(request, 'Email already exists')
            else:
                # Create a new user
                user = User.objects.create_user(username=username, email=email, password=password1)
                user_profile, created = UserProfile.objects.get_or_create(user=user)
                user_profile.number = number
                user_profile.save()

                # Authenticate and login the user
                user = auth.authenticate(request, username=username, password=password1)
                if user is not None:
                    auth.login(request, user)

                    # Retrieve product_id from session and redirect accordingly
                    selected_product_id = request.session.pop('selected_product_id', None)
                    redirect_url = reverse('product_detail', args=[selected_product_id]) if selected_product_id else reverse('home')
                    messages.error(request, 'Account successfully created.')
                    return redirect(redirect_url)

                # Handle unexpected cases
                else:
                    messages.error(request, 'Unexpected error during authentication. Please try again.')

    return render(request, 'authentication/login_or_register.html')



#this function handles the search request
def logout(request):
    auth.logout(request)
     # Retrieve product_id from session and redirect accordingly
    selected_product_id = request.session.pop('selected_product_id', None)
    redirect_url = reverse('product_detail', args=[selected_product_id]) if selected_product_id else reverse('home')
    return redirect(redirect_url)

#this function is used to search for items on the web application
def search(request):
    query = request.GET.get('query')
    if query:
        products = Product.objects.filter(name__icontains=query) | Product.objects.filter(price__icontains=query)
    else:
        products = Product.objects.all()
    
    # Calculate discounted prices for each product
    for product in products:
        if product.discount:
            discount_percent = product.discount_percent
            discounted_price = product.price * (100 - discount_percent) / 100
            product.discounted_price = discounted_price
        else:
            product.discounted_price = product.price
    
    #this is to display some shoes in the case the queried shoe is not found
    shoes = list(Product.objects.all())
    random.shuffle(shoes)
    images_to_display = shoes[:6]
    
    context = {
        'images_to_display' : images_to_display,
        'products': products,
        'query': query
    }
    return render(request, 'mains/search.html', context)


def product_detail(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    shoes = list(Product.objects.all())
    random.shuffle(shoes)
    images_to_display = shoes[:3]

    # Save the product ID in the session
    request.session['selected_product_id'] = product_id

    # Check if the product is in the user's favorites
    is_favorite = request.user.is_authenticated and request.user.favorite_set.filter(product=product).exists()

    #checking if a product is discounted or not
    if product.discount:
        discount_percent = product.discount_percent

        # Calculate the discounted price
        discounted_price = product.price * (100 - discount_percent) / 100
    else:
        discounted_price = product.price

    context = {'product': product, 
               'is_favorite': is_favorite,
                'shoes' : shoes,
                'images_to_display' : images_to_display ,
                'discounted_price' : discounted_price}

    return render(request, 'mains/product_detail.html', context)

#this handles the cart page
def cart(request):
    user = request.user
    items = Cart.objects.filter(user=user)
    cart_count = items.count()
    context = {'items': items}
    return render(request, 'mains/cart.html', context)


# this function adds a product to the cart
# def add_to_cart(request, product_id):
#     user = request.user
#     product = get_object_or_404(Product, id=product_id)
    

#     item_name = str(product.name)

#     # Store the product_id in the session
#     request.session['selected_product_id'] = product_id

#     if request.method == 'POST':
#         quantity = int(request.POST.get('quantity', 1))

#         # Check if 'size' and 'color' are in POST data
#         if 'size' in request.POST and 'color' in request.POST:
#             size_id = int(request.POST['size'])
#             size = get_object_or_404(ShoeSize, id=size_id)
#             color_id = int(request.POST['color'])
#             color = get_object_or_404(ShoeColor, id=color_id)

#             item = Cart.objects.filter(product=product, user=user, size=size, color=color)
#             if item.exists():
#                 item = item.first()
#                 item.quantity += quantity
#                 item.save()
#             else:
#                 new_item = Cart.objects.create(product=product, user=user, quantity=quantity, size=size, color=color)
#                 new_item.save()

#             # Update UserProfile cart count
#             user_profile = UserProfile.objects.get_or_create(user=request.user)[0]
#             user_profile.update_cart_count()

#             # Adding message to be displayed when a new item is added to the cart
#             messages.info(request, f'{item_name} added to Cart')
#             return redirect('product_detail', product_id=product_id)
#         else:
#             # Handle the case when 'size' or 'color' is missing in POST data
#             messages.error(request, 'Invalid request. Please select size and color.')
#             return redirect('product_detail', product_id=product_id)

#     # Handle GET requests separately, if needed
#     return redirect('mains/product_detail.html', product_id=product_id)


def add_to_cart(request, product_id):
    user = request.user
    product = get_object_or_404(Product, id=product_id)

    item_name = str(product.name)

    # Store the product_id in the session
    request.session['selected_product_id'] = product_id

    if request.method == 'POST':
        quantity = int(request.POST.get('quantity', 1))

        # Check if 'size' and 'color' are in POST data
        if 'size' in request.POST and 'color' in request.POST:
            size_id = int(request.POST['size'])
            size = get_object_or_404(ShoeSize, id=size_id)
            color_id = int(request.POST['color'])
            color = get_object_or_404(ShoeColor, id=color_id)

            # Determine the price based on discount
            price = product.price
            if product.discount:
                price = product.price * (100 - product.discount_percent) / 100

            # Check if the item already exists in the cart
            item = Cart.objects.filter(product=product, user=user, size=size, color=color).first()
            if item:
                item.quantity += quantity
                item.save()
            else:
                Cart.objects.create(product=product, user=user, quantity=quantity, size=size, color=color, price=price)

            # Update UserProfile cart count
            user_profile = UserProfile.objects.get_or_create(user=request.user)[0]
            user_profile.update_cart_count()

            # Adding message to be displayed when a new item is added to the cart
            messages.info(request, f'{item_name} added to Cart')
            return redirect('product_detail', product_id=product_id)
        else:
            # Handle the case when 'size' or 'color' is missing in POST data
            messages.error(request, 'Invalid request. Please select size and color.')
            return redirect('product_detail', product_id=product_id)

    # Handle GET requests separately, if needed
    return redirect('product_detail', product_id=product_id)

@login_required
def remove_from_cart(request, product_id):
    cart_item = get_object_or_404(Cart, id=product_id)
    removed_item_name = str(cart_item.product)

    cart_item.delete()
    
    # Update UserProfile cart count
    user_profile = UserProfile.objects.get_or_create(user=request.user)[0]
    user_profile.update_cart_count()

    messages.success(request, f"{removed_item_name} removed from cart.")
    return redirect('cart')

@login_required
#this handles the removal of all products from cart 
def empty_cart(request):
    item = Cart.objects.all()
    item.delete()

    # Update UserProfile cart count
    user_profile = UserProfile.objects.get_or_create(user=request.user)[0]
    user_profile.update_cart_count()

    messages.success(request, "All items removed from Cart.")
    return redirect('cart')

#this function updates the cart
# def update_cart(request, product_id):
#     cart = Cart(request)
#     product = Product.objects.get(id=product_id)
#     quantity = int(request.POST.get('quantity'))
#     cart.update(product=product, quantity=quantity)
#     messages.success(request, f"{product.name} has been updated in your cart.")
#     return redirect('cart')

def update_cart_item(request, item_id):
    if request.method == 'POST':
        item = get_object_or_404(Cart, pk=item_id)
        name = item.product.name
        quantity = int(request.POST.get('quantity', 1))
        size_id = int(request.POST.get('size'))
        size = get_object_or_404(ShoeSize, id=size_id)
        color_id = int(request.POST.get('color'))
        color = get_object_or_404(ShoeColor, id=color_id)

        # Update the cart item with new data
        item.quantity = quantity
        item.size_id = size
        item.color_id = color
        item.updated_at = timezone.now()
        item.save()

        messages.success(request, f"{name} updated successfully in cart.")
        return redirect('cart')
    else:
        messages.error(request, "Invalid request method.")
        return redirect('cart')

def checkout(request):
    return render(request, 'checkout.html')

#this adds a product to the user's favorites
def add_to_favorite(request, product_id):
    product = get_object_or_404(Product, id=product_id)

    # Check if the product is already in favorites
    existing_favorite = Favorite.objects.filter(user=request.user, product=product).first()

    if existing_favorite:
        # Remove the product from favorites
        existing_favorite.delete()
        messages.success(request, f'{product.name} removed from Favorites.')
    else:
        # Create a new Favorite instance
        favorite = Favorite(user=request.user, product=product)
        favorite.save()
        messages.success(request, f'{product.name} added to Favorites.')

    return redirect('product_detail', product_id=product_id)

# this displays the user's favorite items
def favorite(request):
    user = request.user
    
    # Retrieve user's favorite products
    favorites = Favorite.objects.filter(user=user)
    
    # Calculate discounted prices for each favorite product
    for favorite in favorites:
        product = favorite.product
        if product.discount:
            discount_percent = product.discount_percent
            discounted_price = product.price * (100 - discount_percent) / 100
            product.discounted_price = discounted_price
        else:
            product.discounted_price = product.price
    
    context = {'favorites': favorites}
    return render(request, 'mains/favorite.html', context)


# this removes an item from the user's favorites
def remove_from_favorite(request, product_id):
    product = get_object_or_404(Product, id=product_id)

    # Check if the product is in favorites
    favorite = Favorite.objects.filter(user=request.user, product=product).first()

    if favorite:
        # Remove the product from favorites
        favorite.delete()
        messages.success(request, f'{product.name} removed from Favorites.')
    else:
        messages.error(request, f'{product.name} is not in your Favorites.')

    return redirect('favorite')

#function to display discounted products
def discounted_products(request):
    products = Product.objects.filter(discount=True)
    
    discounted_products = []
    for product in products:
        # Check if each product is discounted
        if product.discount:
            discount_percent = product.discount_percent

            # Calculate the discounted price
            discounted_price = product.price * (100 - discount_percent) / 100
            product.discounted_price = discounted_price  # Add discounted price to product instance
        else:
            # If not discounted, use regular price
            product.discounted_price = product.price
        
        discounted_products.append(product)
    
    context = {'products': discounted_products}
    return render(request, 'categories/discounted_products.html', context)

def display_category(request, category):
    products = Product.objects.filter(categories = category)

    discounted_products = []
    for product in products:
        #check if product is discounted
        if product.discount:
            discount_percent = product.discount_percent

            #calculate the discount price
            discounted_price = product.price * (100 - discount_percent) / 100
            product.discounted_price = discounted_price
        else:
            #if not discounted, use regular price
            product.discounted_price = product.price

        discounted_products.append(product)

    category_name = category.upper()
    context = {'products' : discounted_products,
               'category_name' : category_name}
    return render(request, f'categories/{category}.html', context)

def trending(request):
    return display_category(request, 'trending')
def outdoor(request):
    return display_category(request, 'outdoor')
def new(request):
    return display_category(request, 'new')


#this function allows the user to create an order from the products added to their Cart.
def create_order(request):
    if request.method == 'POST':
        # Retrieve the current user
        user = request.user
        
        # Create a new order for the user
        order = Order.objects.create(user=user, total_price=0)
        
        # Retrieve items from the cart for the current user
        cart_items = Cart.objects.filter(user=user)
        
        # Initialize the total price of the order
        total_price = 0
        
        # Create OrderItem instances for each cart item and associate them with the order
        for cart_item in cart_items:
            product = cart_item.product
            
            # Check if the product has a discount applied
            if product.discount:
                # Calculate the discounted price
                discounted_price = product.price * (100 - product.discount_percent) / 100
                # Update the total price with the discounted price
                total_price += discounted_price * cart_item.quantity
            else:
                # If no discount, use the regular price
                total_price += product.price * cart_item.quantity
            
            # Create OrderItem instance and associate it with the order
            order_item = OrderItem.objects.create(
                order=order,
                product=product,
                quantity=cart_item.quantity,
                size=cart_item.size,
                color=cart_item.color
            )
            
            # Remove the cart item after adding it to the order
            cart_item.delete()
        
        # Update the total price of the order
        order.total_price = total_price
        order.save()
        
            # Update UserProfile cart count
        user_profile = UserProfile.objects.get_or_create(user=request.user)[0]
        user_profile.update_cart_count()

        messages.success(request, 'Order has been successfully placed')

        # Redirect to a page indicating the order has been successfully created
        return render(request, 'mains/cart.html', {'order': order})
    else:
        messages.error(request, 'Order not placing unsuccessful')

        # If the request method is not POST, redirect the user to another page or display an error message
        return redirect('cart')  # Redirect to home page or any other page

# @login_required
# def create_order(request):
#     if request.method == 'POST':
#         # Retrieve the current user
#         user = request.user
        
#         # Create a new order for the user
#         order = Order.objects.create(user=user, total_price=0)
        
#         # Retrieve items from the cart for the current user
#         cart_items = Cart.objects.filter(user=user)
        
#         # Initialize the total price of the order
#         total_price = 0
        
#         # Create OrderItem instances for each cart item and associate them with the order
#         for cart_item in cart_items:
#             product = cart_item.product
            
#             # Check if the product has a discount applied
#             if product.discount:
#                 # Calculate the discounted price
#                 discounted_price = product.price * (100 - product.discount_percent) / 100
#                 # Update the total price with the discounted price
#                 total_price += discounted_price * cart_item.quantity
#             else:
#                 # If no discount, use the regular price
#                 total_price += product.price * cart_item.quantity
            
#             # Create OrderItem instance and associate it with the order
#             order_item = OrderItem.objects.create(
#                 order=order,
#                 product=product,
#                 quantity=cart_item.quantity,
#                 size=cart_item.size,
#                 color=cart_item.color
#             )
            
#             # Remove the cart item after adding it to the order
#             cart_item.delete()
        
#         # Update the total price of the order
#         order.total_price = total_price
#         order.save()
        
#         # Update UserProfile cart count
#         user_profile = UserProfile.objects.get_or_create(user=user)[0]
#         user_profile.update_cart_count()

#         # Return JSON response indicating order placement success and order details URL
#         data = {
#             'success': True,
#             'order_details_url': reverse('order_details', kwargs={'order_id': order.id})
#         }
#         return JsonResponse(data)
#     else:
#         # If the request method is not POST, return an error response
#         return JsonResponse({'success': False})


def order_details(request, order_id):
    order = Order.objects.get(pk=order_id)
    print(order.id)  # Check if order.id is printed correctly
    total_price = sum(order_item.subtotal for order_item in order.orderitem_set.all())
    return render(request, 'mains/order_details.html', {'order': order, 'total_price': total_price})
    
    
def orders(request):
    user = request.user
    orders = Order.objects.filter(user=user)
    context ={"orders" : orders}
    return render(request, "orders.html", context)