

"""
Payment Helper Functions
Handles QR code generation, payment validation, and payment method processing
"""

import qrcode
import base64
import io
from django.http import JsonResponse


def generate_upi_qr_code(amount, merchant_id="store@exampleupi"):
    """
    Generate dynamic QR code for UPI payments
    
    Args:
        amount: Order amount in rupees
        merchant_id: UPI ID of merchant
    
    Returns:
        Base64 encoded QR code image data
    """
    try:
        # Create UPI payment URL
        upi_url = f"upi://pay?pa={merchant_id}&pn=KostaaStore&am={amount}&cu=INR"
        
        # Generate QR code
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(upi_url)
        qr.make(fit=True)
        
        # Create image
        img = qr.make_image(fill_color="black", back_color="white")
        
        # Convert to base64
        buffer = io.BytesIO()
        img.save(buffer, format='PNG')
        img_str = base64.b64encode(buffer.getvalue()).decode()
        
        return f"data:image/png;base64,{img_str}"
    except Exception as e:
        print(f"Error generating UPI QR code: {str(e)}")
        # Fallback to static QR code
        return "/static/images/qrcode.jpeg"


def generate_paytm_qr_code(amount, paytm_id="9876543210@paytm"):
    """
    Generate dynamic QR code for Paytm payments
    
    Args:
        amount: Order amount in rupees
        paytm_id: Paytm phone number or ID
    
    Returns:
        Base64 encoded QR code image data
    """
    try:
        # Create Paytm UPI payment URL
        paytm_url = f"upi://pay?pa={paytm_id}&pn=KostaaStore&am={amount}&cu=INR&mode=00"
        
        # Generate QR code
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(paytm_url)
        qr.make(fit=True)
        
        # Create image
        img = qr.make_image(fill_color="black", back_color="white")
        
        # Convert to base64
        buffer = io.BytesIO()
        img.save(buffer, format='PNG')
        img_str = base64.b64encode(buffer.getvalue()).decode()
        
        return f"data:image/png;base64,{img_str}"
    except Exception as e:
        print(f"Error generating Paytm QR code: {str(e)}")
        # Fallback to static QR code
        return "/static/images/qrcode.jpeg"


def validate_card(card_number, expiry, cvv):
    """
    Validate card details (basic validation)
    
    Args:
        card_number: Card number (16 digits)
        expiry: Expiry date (MM/YY format)
        cvv: CVV (3-4 digits)
    
    Returns:
        Tuple (is_valid, error_message)
    """
    # Remove spaces from card number
    card_number = card_number.replace(" ", "")
    
    # Validate card number length
    if len(card_number) not in [13, 14, 15, 16]:
        return False, "Card number must be 13-16 digits"
    
    # Check if all are digits
    if not card_number.isdigit():
        return False, "Card number must contain only digits"
    
    # Validate expiry format (MM/YY)
    if "/" not in expiry:
        return False, "Expiry date format should be MM/YY"
    
    try:
        month, year = expiry.split("/")
        month = int(month)
        year = int(year)
        
        if month < 1 or month > 12:
            return False, "Invalid month in expiry date"
        
        if year < 20:  # Assuming YY format (20-99)
            return False, "Invalid year in expiry date"
    except:
        return False, "Invalid expiry date format"
    
    # Validate CVV
    if len(cvv) not in [3, 4]:
        return False, "CVV must be 3 or 4 digits"
    
    if not cvv.isdigit():
        return False, "CVV must contain only digits"
    
    return True, "Card details are valid"


def validate_upi_id(upi_id):
    """
    Validate UPI ID format
    
    Args:
        upi_id: UPI ID (e.g., user@bank)
    
    Returns:
        Tuple (is_valid, error_message)
    """
    if not upi_id or len(upi_id) < 3:
        return False, "UPI ID is required"
    
    if "@" not in upi_id:
        return False, "Invalid UPI ID format"
    
    parts = upi_id.split("@")
    if len(parts) != 2:
        return False, "Invalid UPI ID format"
    
    if len(parts[0]) < 3 or len(parts[1]) < 2:
        return False, "Invalid UPI ID format"
    
    return True, "UPI ID is valid"
