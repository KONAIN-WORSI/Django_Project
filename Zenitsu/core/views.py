from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.hashers import make_password, check_password
from .forms import SignupForm 
from .models import UserInfo, certifications
from django.contrib import messages


# Create your views here.
def sign_up(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        email = request.POST.get('email')
        password1 = request.POST.get('password1')
        password2 = request.POST.get('password2')
        
        # Validate passwords match
        if password1 != password2:
            return render(request, 'sign_up.html', {
                'error': 'Passwords do not match'
            })
        
        # Check if user exists
        if UserInfo.objects.filter(email=email).exists():
            return render(request, 'sign_up.html', {
                'error': 'Email already registered'
            })
        
        # Create user
        user = UserInfo.objects.create(
            username=username,
            email=email,
            password=make_password(password1)
        )
          
        user.save()
        
        return redirect('login')
    
    return render(request, 'sign_up.html')


def login(request):
    error = ''
    if request.method == 'POST':
        email = request.POST.get('email', '').strip()  # Strip whitespace
        password = request.POST.get('password', '')
        
        # Generic error message for security
        if not email or not password:
            error = 'Please provide both email and password'
        else:
            try:
                user = UserInfo.objects.get(email=email)
                if check_password(password, user.password):
                    request.session['user_id'] = user.id
                    request.session['user_email'] = user.email  # Optional: store email too
                    print(f'User {user.email} logged in successfully')
                    return redirect('landing')
                else:
                    error = 'Invalid email or password'  # Generic message
            except UserInfo.DoesNotExist:
                # Use the same error message to prevent email enumeration
                error = 'Invalid email or password'  # Same as above

    return render(request, 'login.html', {'error': error})

def landing(request):
    user = None
    user_id = request.session.get('user_id')
    if user_id:
        try:
            user = UserInfo.objects.get(id=user_id)
        except UserInfo.DoesNotExist:
            user = None
    else:
        user = None
    
    return render(request, 'landing.html', {'user': user})

def certifications_view(request):
    if request.method == 'POST':
        recipient_name = request.POST.get('recipient_name')
        recipient_email = request.POST.get('recipient_email')
        certificate_name = request.POST.get('certificate_name')
        course_name = request.POST.get('course_name')
        
        user_id = request.session.get('user_id')

        if not user_id:
            messages.error(request, 'Please log in to create a certifications.')
            return redirect('login')
        
        try:
            user = UserInfo.objects.get(id = user_id)

            certification = certifications.objects.create(
                user = user,
                recipient_name = recipient_name,
                recipient_email = recipient_email,
                certificate_name = certificate_name,
                course_name = course_name
            )
        except UserInfo.DoesNotExist:
            messages.error(request, 'User not found. Please log in again.')
            return redirect('login')
        
        # send certification to recipient email
        try:
            sent = certification.send_certificate_email()
        except Exception:
            sent = False

        if sent:
            messages.success(request, f"Certification sent successfully to {recipient_email}!")
        else:
            messages.error(request, 'Certification created but failed to send certification. Please try again later.')
        return redirect('certificate_list')
    
    return render(request, 'certificates/certifications_view.html')


def certificate_list(request):
    user_id = request.session.get('user_id')

    if not user_id:
        messages.error(request, 'Please log in to view your Certifications.')
        return redirect('login')

    try:
        user = UserInfo.objects.get(id = user_id)
        certificates = certifications.objects.filter(user = user)
    except UserInfo.DoesNotExist:
        messages.error(request, 'User not found. Please log in again.')
        return redirect('login')

    return render(request, 'certificates/certificate_list.html', {
        'certificates' : certificates,
        'user' : user
    })


def resend_certificate(request, certificate_id):
    user_id = request.session.get('user_id')

    if not user_id:
        messages.error(request, 'Please log in to resend Certifications.')
        return redirect('login')

    certificate = get_object_or_404(certifications, id = certificate_id, user_id = user_id)

    if certificate.send_certificate_email():
        messages.success(request, f'Certification resent successfully to {certificate.recipient_email}')
    else:
        messages.error(request, 'Failed to resend certification.Please try again later.')

    return redirect('certificate_list')


# # views.py - Add this temporary test function
# from django.http import HttpResponse
# from django.core.mail import send_mail
# from django.conf import settings

# def test_email(request):
#     """Test basic email sending"""
#     try:
#         send_mail(
#             'Test Email from Django',
#             'This is a test message.',
#             settings.EMAIL_HOST_USER,
#             ['recipient@example.com'],  # Change to your test email
#             fail_silently=False,
#         )
#         return HttpResponse("Email sent successfully! Check your inbox.")
#     except Exception as e:
#         return HttpResponse(f"Error: {str(e)}")

# # Add to urls.py temporarily
# # path('test-email/', views.test_email, name='test_email'),