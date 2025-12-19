from django.db import models
from django.utils import timezone
from django.core.mail import EmailMessage, EmailMultiAlternatives
from django.template.loader import render_to_string
from django.conf import settings
from io import BytesIO
from PIL import Image, ImageDraw, ImageFont
from django.core.mail import get_connection, EmailMultiAlternatives


# Create your models here.
class UserInfo(models.Model):
    username = models.CharField(max_length=150)
    email = models.EmailField(unique=True)
    password = models.CharField(max_length=120)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.username
    
class certifications(models.Model):
    user = models.ForeignKey('UserInfo', on_delete = models.CASCADE)
    recipient_name = models.CharField(max_length=200)
    recipient_email = models.EmailField()
    certificate_name = models.CharField(max_length=200, help_text="e.g Course Completion Certificate")
    course_name = models.CharField(max_length=200, blank=True, null=True)
    completion_date = models.DateTimeField(auto_now_add=True)
    issued_by = models.CharField(max_length=200)
    issued_date = models.DateTimeField(auto_now=True)
    certificate_number = models.CharField(max_length=100, unique=True, editable=False)
    is_sent = models.BooleanField(default=False)
    sent_at = models.DateTimeField(auto_now_add=True, blank=True)

    class Meta:
        ordering = ['-issued_date']

    def __str__(self):
        return f"{self.certificate_name} - {self.recipient_name}"
    
    def save(self, *args, **kwargs):
        if not self.certificate_number:
            # Generate unique certificate number
            import uuid
            self.certificate_number = f"CERT-{uuid.uuid4().hex[:8].upper()}"
        super().save(*args, **kwargs)
 
    def generate_certificate_image(self):
         width, height = 1200, 800
         image = Image.new('RGB', (width, height), color='white')
         draw = ImageDraw.Draw(image)
         try:
             title_font = ImageFont.truetype("arial.ttf", 60)
             name_font = ImageFont.truetype("arial.ttf", 80)
             text_font = ImageFont.truetype("arial.ttf", 30)
             small_font = ImageFont.truetype("arial.ttf", 20)
         except:
             title_font = ImageFont.load_default()
             name_font = ImageFont.load_default()
             text_font = ImageFont.load_default()
             small_font = ImageFont.load_default()
         border_color = (108, 92, 231)
         draw.rectangle([(20, 20), (width-20, height-20)], outline=border_color, width=5)
         draw.rectangle([(30, 30), (width-30, height-30)], outline=border_color, width=2)
         title = "CERTIFICATE OF COMPLETION"
         title_bbox = draw.textbbox((0, 0), title, font=title_font)
         title_width = title_bbox[2] - title_bbox[0]
         draw.text(((width - title_width) / 2, 100), title, fill=border_color, font=title_font)
         subtitle = "This is to certify that"
         subtitle_bbox = draw.textbbox((0, 0), subtitle, font=text_font)
         subtitle_width = subtitle_bbox[2] - subtitle_bbox[0]
         draw.text(((width - subtitle_width) / 2, 200), subtitle, fill='black', font=text_font)
         name_bbox = draw.textbbox((0, 0), self.recipient_name, font=name_font)
         name_width = name_bbox[2] - name_bbox[0]
         draw.text(((width - name_width) / 2, 280), self.recipient_name, fill='black', font=name_font)
         line_y = 380
         draw.line([(300, line_y), (900, line_y)], fill='black', width=2)
         if self.course_name:
             course_text = f"has successfully completed the course"
             course_bbox = draw.textbbox((0, 0), course_text, font=text_font)
             course_width = course_bbox[2] - course_bbox[0]
             draw.text(((width - course_width) / 2, 420), course_text, fill='black', font=text_font)
             course_name_bbox = draw.textbbox((0, 0), self.course_name, font=name_font)
             course_name_width = course_name_bbox[2] - course_name_bbox[0]
             draw.text(((width - course_name_width) / 2, 480), self.course_name, fill=border_color, font=text_font)
         date_text = f"Date: {self.completion_date.strftime('%B %d, %Y')}"
         cert_text = f"Certificate No: {self.certificate_number}"
         draw.text((100, height - 100), date_text, fill='black', font=small_font)
         draw.text((width - 350, height - 100), cert_text, fill='black', font=small_font)
         buffer = BytesIO()
         image.save(buffer, format='PNG')
         buffer.seek(0)
         return buffer
 
    def send_certificate_email(self):
         from django.utils import timezone
         from django.conf import settings
         try:
             certificate_image = self.generate_certificate_image()
             subject = f'Your {self.certificate_name} is Ready!'
             message = f"""
 Dear {self.recipient_name},
 
 Congratulations! Your certificate has been issued.
 
 Certificate Number: {self.certificate_number}
 Completion Date: {self.completion_date.strftime('%B %d, %Y')}
 Recipient: {self.recipient_name}
 """
             if self.course_name:
                 message += f"Course: {self.course_name}\n"
             message += "\nBest regards,\nThe Zenitsu Team"
             if 'console' in settings.EMAIL_BACKEND.lower():
                 print("\n" + "="*50)
                 print("CERTIFICATE EMAIL (Console Mode)")
                 print("="*50)
                 print(f"To: {self.recipient_email}")
                 print(f"From: {settings.DEFAULT_FROM_EMAIL}")
                 print(f"Reply-To: {self.user.email}")
                 print(f"Subject: {subject}")
                 print(f"\n{message}")
                 print(f"\nAttachment: certificate_{self.certificate_number}.png")
                 print("="*50 + "\n")
             else:
                 from django.core.mail import EmailMessage
                 email = EmailMessage(
                     subject=subject,
                     body=message,
                     from_email=settings.DEFAULT_FROM_EMAIL,
                     to=[self.recipient_email],
                     reply_to=[self.user.email],
                 )
                 email.attach(
                     f'certificate_{self.certificate_number}.png',
                     certificate_image.getvalue(),
                     'image/png'
                 )
                 email.send(fail_silently=False)
             self.is_sent = True
             self.sent_at = timezone.now()
             self.save()
             EmailLog.objects.create(
                 certificate=self,
                 recipient_email=self.recipient_email,
                 subject=subject,
                 status='sent'
             )
             print(f"✅ Certificate processed successfully for {self.recipient_email}")
             return True
         except Exception as e:
             EmailLog.objects.create(
                 certificate=self,
                 recipient_email=self.recipient_email,
                 subject=subject if 'subject' in locals() else 'Certificate Sending Failed',
                 status='failed',
                 error_message=str(e)
             )
             print(f"❌ Error: {e}")
             import traceback
             traceback.print_exc()
             return False

class EmailLog(models.Model):
    STATUS_CHOICES = (
        ('sent', 'Sent'),
        ('failed', 'Failed'),
    )

    certificate = models.ForeignKey(certifications, on_delete=models.CASCADE, related_name='email_logs')
    recipient_email = models.EmailField()
    subject = models.CharField(max_length=255)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES)
    error_message = models.TextField(blank=True, null=True)
    sent_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-sent_at']

    def __str__(self):
        return f"{self.status.upper()} - {self.recipient_email} ({self.sent_at.strftime('%Y-%m-%d %H:%M')})"
    
    def generate_certificate_image(self):
        """Generate certificate as PNG image"""
        # Create a new image with white background
        width, height = 1200, 800
        image = Image.new('RGB', (width, height), color='white')
        draw = ImageDraw.Draw(image)
        
        # Try to use custom fonts, fallback to default
        try:
            title_font = ImageFont.truetype("arial.ttf", 60)
            name_font = ImageFont.truetype("arial.ttf", 80)
            text_font = ImageFont.truetype("arial.ttf", 30)
            small_font = ImageFont.truetype("arial.ttf", 20)
        except:
            title_font = ImageFont.load_default()
            name_font = ImageFont.load_default()
            text_font = ImageFont.load_default()
            small_font = ImageFont.load_default()
        
        # Draw border
        border_color = (108, 92, 231)  # Purple accent color
        draw.rectangle([(20, 20), (width-20, height-20)], outline=border_color, width=5)
        draw.rectangle([(30, 30), (width-30, height-30)], outline=border_color, width=2)
        
        # Title
        title = "CERTIFICATE OF COMPLETION"
        title_bbox = draw.textbbox((0, 0), title, font=title_font)
        title_width = title_bbox[2] - title_bbox[0]
        draw.text(((width - title_width) / 2, 100), title, fill=border_color, font=title_font)
        
        # Subtitle
        subtitle = "This is to certify that"
        subtitle_bbox = draw.textbbox((0, 0), subtitle, font=text_font)
        subtitle_width = subtitle_bbox[2] - subtitle_bbox[0]
        draw.text(((width - subtitle_width) / 2, 200), subtitle, fill='black', font=text_font)
        
        # Recipient name (centered)
        name_bbox = draw.textbbox((0, 0), self.recipient_name, font=name_font)
        name_width = name_bbox[2] - name_bbox[0]
        draw.text(((width - name_width) / 2, 280), self.recipient_name, fill='black', font=name_font)
        
        # Draw line under name
        line_y = 380
        draw.line([(300, line_y), (900, line_y)], fill='black', width=2)
        
        # Course completion text
        if self.course_name:
            course_text = f"has successfully completed the course"
            course_bbox = draw.textbbox((0, 0), course_text, font=text_font)
            course_width = course_bbox[2] - course_bbox[0]
            draw.text(((width - course_width) / 2, 420), course_text, fill='black', font=text_font)
            
            course_name_bbox = draw.textbbox((0, 0), self.course_name, font=name_font)
            course_name_width = course_name_bbox[2] - course_name_bbox[0]
            draw.text(((width - course_name_width) / 2, 480), self.course_name, fill=border_color, font=text_font)
        
        # Date and certificate number
        date_text = f"Date: {self.completion_date.strftime('%B %d, %Y')}"
        cert_text = f"Certificate No: {self.certificate_number}"
        
        draw.text((100, height - 100), date_text, fill='black', font=small_font)
        draw.text((width - 350, height - 100), cert_text, fill='black', font=small_font)
        
        # Save to BytesIO
        buffer = BytesIO()
        image.save(buffer, format='PNG')
        buffer.seek(0)
        return buffer
        
    
    def send_certificate_email(self):
        """Generate certificate and send via email"""
        from django.utils import timezone
        from django.conf import settings
        
        try:
            # Generate certificate image
            certificate_image = self.generate_certificate_image()
            
            # Simple email message
            subject = f'Your {self.certificate_name} is Ready!'
            message = f"""
    Dear {self.recipient_name},

    Congratulations! Your certificate has been issued.

    Certificate Number: {self.certificate_number}
    Completion Date: {self.completion_date.strftime('%B %d, %Y')}
    Recipient: {self.recipient_name}
    """
            if self.course_name:
                message += f"Course: {self.course_name}\n"
            
            message += "\nBest regards,\nThe Zenitsu Team"
            
            # Check if we're using console backend
            if 'console' in settings.EMAIL_BACKEND.lower():
                print("\n" + "="*50)
                print("CERTIFICATE EMAIL (Console Mode)")
                print("="*50)
                print(f"To: {self.recipient_email}")
                print(f"From: {settings.DEFAULT_FROM_EMAIL}")
                print(f"Reply-To: {self.user.email}")
                print(f"Subject: {subject}")
                print(f"\n{message}")
                print(f"\nAttachment: certificate_{self.certificate_number}.png")
                print("="*50 + "\n")
            else:
                # Only try to send if not using console backend
                from django.core.mail import EmailMessage
                
                email = EmailMessage(
                    subject=subject,
                    body=message,
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    to=[self.recipient_email],
                    reply_to=[self.user.email],
                )
                
                email.attach(
                    f'certificate_{self.certificate_number}.png',
                    certificate_image.getvalue(),
                    'image/png'
                )
                
                email.send(fail_silently=False)
            
            # Update status
            self.is_sent = True
            self.sent_at = timezone.now()
            self.save()
            
            # Create success log
            EmailLog.objects.create(
                certificate=self,
                recipient_email=self.recipient_email,
                subject=subject,
                status='sent'
            )

            print(f"✅ Certificate processed successfully for {self.recipient_email}")
            return True
            
        except Exception as e:
            # Create error log
            EmailLog.objects.create(
                certificate=self,
                recipient_email=self.recipient_email,
                subject=subject if 'subject' in locals() else 'Certificate Sending Failed',
                status='failed',
                error_message=str(e)
            )

            print(f"❌ Error: {e}")
            import traceback
            traceback.print_exc()
            return False
