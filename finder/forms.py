import os
from PIL import Image as PILImage
from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from .models import CATEGORIES


class StudentRegistrationForm(UserCreationForm):
    """
    Registration form for campus students and faculty.
    Uses Django's built-in User model and password validators,
    and adds a required email address for student communication.
    """
    email = forms.EmailField(
        required=True,
        help_text="Required for students to contact you when your item is found.",
        widget=forms.EmailInput(attrs={
            'class': 'w-full px-4 py-3 rounded-xl border border-gray-200 text-sm focus:outline-none focus:ring-2 focus:ring-brand-500 focus:border-brand-500',
            'placeholder': 'student@campus.edu',
        })
    )

    class Meta:
        model = User
        fields = ('username', 'email')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['username'].widget.attrs.update({
            'class': 'w-full px-4 py-3 rounded-xl border border-gray-200 text-sm focus:outline-none focus:ring-2 focus:ring-brand-500 focus:border-brand-500',
            'placeholder': 'Choose a unique username',
        })
        self.fields['password1'].widget.attrs.update({
            'class': 'w-full px-4 py-3 rounded-xl border border-gray-200 text-sm focus:outline-none focus:ring-2 focus:ring-brand-500 focus:border-brand-500',
            'placeholder': 'Enter a secure password',
        })
        self.fields['password2'].widget.attrs.update({
            'class': 'w-full px-4 py-3 rounded-xl border border-gray-200 text-sm focus:outline-none focus:ring-2 focus:ring-brand-500 focus:border-brand-500',
            'placeholder': 'Confirm your password',
        })

    def clean_email(self):
        email = self.cleaned_data.get('email').strip().lower()
        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError("An account with this email address already exists.")
        return email


class StudentLoginForm(AuthenticationForm):
    """
    Login form styled with Tailwind CSS utility classes.
    """
    username = forms.CharField(
        widget=forms.TextInput(attrs={
            'class': 'w-full px-4 py-3 rounded-xl border border-gray-200 text-sm focus:outline-none focus:ring-2 focus:ring-brand-500 focus:border-brand-500',
            'placeholder': 'Enter your username',
        })
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'w-full px-4 py-3 rounded-xl border border-gray-200 text-sm focus:outline-none focus:ring-2 focus:ring-brand-500 focus:border-brand-500',
            'placeholder': 'Enter your password',
        })
    )


class ItemReportForm(forms.Form):
    """
    Reusable form for reporting or editing lost & found items.
    Note: Uses standard django.forms.Form because documents are stored in MongoDB via PyMongo.
    """
    REPORT_TYPE_CHOICES = [
        ('lost', 'Lost Item (I misplaced something)'),
        ('found', 'Found Item (I found someone\'s item)'),
    ]

    CATEGORY_CHOICES = [(cat, cat) for cat in CATEGORIES]

    report_type = forms.ChoiceField(
        choices=REPORT_TYPE_CHOICES,
        widget=forms.Select(attrs={
            'class': 'w-full px-4 py-3 rounded-xl border border-gray-200 text-sm bg-white focus:outline-none focus:ring-2 focus:ring-brand-500 focus:border-brand-500',
        })
    )

    title = forms.CharField(
        max_length=150,
        widget=forms.TextInput(attrs={
            'class': 'w-full px-4 py-3 rounded-xl border border-gray-200 text-sm focus:outline-none focus:ring-2 focus:ring-brand-500 focus:border-brand-500',
            'placeholder': 'e.g. Dell XPS 15 Laptop, Blue Water Bottle, Black Leather Wallet',
        })
    )

    category = forms.ChoiceField(
        choices=CATEGORY_CHOICES,
        widget=forms.Select(attrs={
            'class': 'w-full px-4 py-3 rounded-xl border border-gray-200 text-sm bg-white focus:outline-none focus:ring-2 focus:ring-brand-500 focus:border-brand-500',
        })
    )

    description = forms.CharField(
        widget=forms.Textarea(attrs={
            'rows': 4,
            'class': 'w-full px-4 py-3 rounded-xl border border-gray-200 text-sm focus:outline-none focus:ring-2 focus:ring-brand-500 focus:border-brand-500',
            'placeholder': 'Provide identifying details such as color, brand, stickers, unique scratches, or where inside the room it was left...',
        })
    )

    location = forms.CharField(
        max_length=150,
        widget=forms.TextInput(attrs={
            'class': 'w-full px-4 py-3 rounded-xl border border-gray-200 text-sm focus:outline-none focus:ring-2 focus:ring-brand-500 focus:border-brand-500',
            'placeholder': 'e.g. Main Library 2nd Floor, Science Hall Room 304, Basketball Court',
        })
    )

    date_lost_found = forms.DateField(
        widget=forms.DateInput(attrs={
            'type': 'date',
            'class': 'w-full px-4 py-3 rounded-xl border border-gray-200 text-sm bg-white focus:outline-none focus:ring-2 focus:ring-brand-500 focus:border-brand-500',
        })
    )

    image = forms.ImageField(
        required=False,
        widget=forms.FileInput(attrs={
            'class': 'block w-full text-sm text-gray-500 file:mr-4 file:py-2.5 file:px-4 file:rounded-xl file:border-0 file:text-xs file:font-semibold file:bg-brand-50 file:text-brand-700 hover:file:bg-brand-100 cursor-pointer',
            'accept': 'image/*',
        }),
        help_text="Optional. Max size 5MB. Formats: JPG, PNG, WEBP."
    )

    def clean_image(self):
        """
        Validates uploaded image file size and verifies image integrity using Pillow.
        """
        image = self.cleaned_data.get('image')
        if not image:
            return None

        # 1. Check file size limit (5 MB)
        max_size_bytes = 5 * 1024 * 1024
        if image.size > max_size_bytes:
            raise forms.ValidationError("Image file size cannot exceed 5MB.")

        # 2. Validate file extension
        ext = os.path.splitext(image.name)[1].lower()
        if ext not in ['.jpg', '.jpeg', '.png', '.webp']:
            raise forms.ValidationError("Unsupported image format. Please upload JPG, PNG, or WEBP.")

        # 3. Verify image integrity with Pillow
        try:
            img = PILImage.open(image)
            img.verify()  # Verifies that it is actually a valid image file
            # Rewind file pointer after verify() so it can be saved to disk
            image.seek(0)
        except Exception:
            raise forms.ValidationError("Uploaded file is corrupted or not a valid image.")

        return image
