from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from .models import Service, Appointment, BookingSlot, GalleryImage
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.conf import settings
from django.shortcuts import render, redirect
from django.core.mail import send_mail

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


def book_appointment(request):
    if request.method == 'POST':
        full_name = request.POST.get('full_name')
        phone_number = request.POST.get('phone_number')
        service = request.POST.get('service')
        time_slot = request.POST.get('time_slot')
        preferred_date = request.POST.get('preferred_date')
        special_requests = request.POST.get('special_requests', '')
        inspiration_image = request.FILES.get('inspiration_image')

        is_already_booked = Appointment.objects.filter(
            preferred_date=preferred_date,
            time_slot=time_slot
        ).exclude(status='Cancelled').exists()

        if is_already_booked:
            messages.error(request, f"Sorry, the slot '{time_slot}' on {preferred_date} is no longer available.")
            return redirect('home')

        # Save to database
        appointment = Appointment.objects.create(
            full_name=full_name,
            phone_number=phone_number,
            service=service,
            time_slot=time_slot,
            preferred_date=preferred_date,
            special_requests=special_requests,
            inspiration_image=inspiration_image
        )

        # Send alert email to Salon Owner
        try:
            subject = f"NEW BOOKING: {full_name} - {preferred_date} ({time_slot})"
            message = (
                f"You have a new appointment booking!\n\n"
                f"Client Name: {full_name}\n"
                f"Phone Number: {phone_number}\n"
                f"Service: {service}\n"
                f"Date: {preferred_date}\n"
                f"Time Slot: {time_slot}\n"
                f"Special Requests: {special_requests if special_requests else 'None'}\n\n"
                f"Check your Admin Dashboard to manage this booking."
            )
            send_mail(
                subject=subject,
                message=message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[settings.SALON_ADMIN_EMAIL],
                fail_silently=True,
            )
        except Exception:
            pass  # Fail silently so booking completes smoothly even if email sending has an issue

        messages.success(request, "Your appointment request has been submitted successfully!")
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