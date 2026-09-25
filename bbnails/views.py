from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from .models import Service, Appointment, BookingSlot, GalleryImage
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.conf import settings
import logging
import urllib.parse

# --- Client Public Views ---

def home(request):
    services = Service.objects.filter(is_active=True)
    all_slots = BookingSlot.objects.filter(is_available=True)
    gallery_images = GalleryImage.objects.all().order_by('-created_at')

    # Get selected date from query params or form reset
    selected_date = request.GET.get('date')

    # Find slots that are ALREADY booked on this specific date
    booked_slots = []
    if selected_date:
        booked_slots = Appointment.objects.filter(
            preferred_date=selected_date
        ).exclude(status='Cancelled').values_list('time_slot', flat=True)

    # Filter out already booked slots
    available_slots = [slot for slot in all_slots if slot.time_slot not in booked_slots]

    return render(request, 'bbnails/home.html', {
        'services': services,
        'slots': available_slots,
        'selected_date': selected_date,
        'gallery_images': gallery_images,
    })


logger = logging.getLogger(__name__)

def book_appointment(request):
    if request.method == 'POST':
        try:
            full_name = request.POST.get('full_name')
            phone_number = request.POST.get('phone_number')
            service = request.POST.get('service')
            time_slot = request.POST.get('time_slot')
            preferred_date = request.POST.get('preferred_date')
            special_requests = request.POST.get('special_requests', '')
            inspiration_image = request.FILES.get('inspiration_image')

            # 1. Check if the slot is already booked
            is_already_booked = Appointment.objects.filter(
                preferred_date=preferred_date,
                time_slot=time_slot
            ).exclude(status='Cancelled').exists()

            if is_already_booked:
                messages.error(request, f"Sorry, the slot '{time_slot}' on {preferred_date} is no longer available.")
                return redirect('home')

            # 2. Save appointment to database
            Appointment.objects.create(
                full_name=full_name,
                phone_number=phone_number,
                service=service,
                time_slot=time_slot,
                preferred_date=preferred_date,
                special_requests=special_requests,
                inspiration_image=inspiration_image
            )

            # 3. Construct WhatsApp Message and Redirect Link
            whatsapp_number = getattr(settings, 'SALON_WHATSAPP_NUMBER', '')
            
            raw_message = (
                f"Hello BB Nails Salon! 👋\n\n"
                f"I just placed an appointment booking on your website:\n\n"
                f"👤 Name: {full_name}\n"
                f"📞 Phone: {phone_number}\n"
                f"💅 Service: {service}\n"
                f"📅 Date: {preferred_date}\n"
                f"⏰ Time: {time_slot}\n"
                f"📝 Notes: {special_requests if special_requests else 'None'}\n\n"
                f"Please confirm my booking!"
            )

            # Encode message for URL
            encoded_message = urllib.parse.quote(raw_message)
            whatsapp_url = f"https://wa.me/{whatsapp_number}?text={encoded_message}"

            # Optional success message
            messages.success(request, "Your booking request was saved! Opening WhatsApp to send your confirmation...")
            
            # Redirect user directly to WhatsApp
            return redirect(whatsapp_url)

        except Exception as e:
            messages.error(request, f"Booking Error: {str(e)}")
            return redirect('home')

    return redirect('home')


# Dynamic API endpoint for AJAX slot fetching based on selected date
def get_available_slots(request):
    selected_date = request.GET.get('date')
    
    # If no date was selected or empty value passed
    if not selected_date:
        return JsonResponse({'slots': []})

    try:
        # Fetch active template slots
        all_slots = BookingSlot.objects.filter(is_available=True)

        # Get slots already booked for this specific date
        booked_slots = Appointment.objects.filter(
            preferred_date=selected_date
        ).exclude(status='Cancelled').values_list('time_slot', flat=True)

        # Build clean slot list
        available_slots = [
            {'id': slot.id, 'time_slot': slot.time_slot}
            for slot in all_slots if slot.time_slot not in list(booked_slots)
        ]

        return JsonResponse({'slots': available_slots})
    except Exception as e:
        print("Error in get_available_slots:", str(e))
        return JsonResponse({'error': str(e)}, status=400)


# --- Staff Admin Dashboard ---

@login_required(login_url='/admin/login/')
def admin_dashboard(request):
    appointments = Appointment.objects.all().order_by('-created_at')
    slots = BookingSlot.objects.all()
    services = Service.objects.all()

    context = {
        'total_bookings': appointments.count(),
        'pending_count': appointments.filter(status='Pending').count(),
        'confirmed_count': appointments.filter(status='Confirmed').count(),
        'appointments': appointments,
        'slots': slots,
        'services': services,
    }
    return render(request, 'bbnails/admin_dashboard.html', context)


# Service Actions
def add_service(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        price = request.POST.get('price')
        description = request.POST.get('description', '')

        if name and price:
            Service.objects.create(name=name, price=price, description=description)
            messages.success(request, f"Service '{name}' added successfully.")
    return redirect('admin_dashboard')


def toggle_service(request, pk):
    service = get_object_or_404(Service, pk=pk)
    service.is_active = not service.is_active
    service.save()
    messages.success(request, f"Service status updated for '{service.name}'.")
    return redirect('admin_dashboard')


def delete_service(request, pk):
    service = get_object_or_404(Service, pk=pk)
    service.delete()
    messages.success(request, "Service deleted successfully.")
    return redirect('admin_dashboard')


# Slot Actions
def add_slot(request):
    if request.method == 'POST':
        time_slot = request.POST.get('time_slot')
        if time_slot:
            BookingSlot.objects.create(time_slot=time_slot)
            messages.success(request, f"Slot '{time_slot}' added successfully.")
    return redirect('admin_dashboard')


def toggle_slot(request, pk):
    slot = get_object_or_404(BookingSlot, pk=pk)
    slot.is_available = not slot.is_available
    slot.save()
    messages.success(request, f"Availability toggled for '{slot.time_slot}'.")
    return redirect('admin_dashboard')


def delete_slot(request, pk):
    slot = get_object_or_404(BookingSlot, pk=pk)
    slot.delete()
    messages.success(request, "Slot deleted successfully.")
    return redirect('admin_dashboard')


# Appointment Status Actions
def update_status(request, pk, status):
    appointment = get_object_or_404(Appointment, pk=pk)
    appointment.status = status
    appointment.save()
    messages.success(request, f"Appointment status updated to '{status}'.")
    return redirect('admin_dashboard')