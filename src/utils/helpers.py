"""
Helper Functions Module
Common utility functions for the PDV system
"""
import os
import re
import hashlib
import json
from datetime import datetime, timedelta
from decimal import Decimal, ROUND_HALF_UP
from typing import Any, Dict, List, Optional, Union
import unicodedata

def format_currency(value: Union[int, float, Decimal], symbol: str = 'R$') -> str:
    """
    Format number as currency
    
    Args:
        value: Numeric value to format
        symbol: Currency symbol
    
    Returns:
        Formatted currency string
    """
    if value is None:
        return f"{symbol} 0,00"
    
    try:
        # Convert to Decimal for precise calculation
        decimal_value = Decimal(str(value))
        # Round to 2 decimal places
        rounded_value = decimal_value.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
        
        # Format with thousands separator
        formatted = f"{rounded_value:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')
        
        return f"{symbol} {formatted}"
    
    except (ValueError, TypeError):
        return f"{symbol} 0,00"

def parse_currency(currency_str: str) -> Decimal:
    """
    Parse currency string to decimal
    
    Args:
        currency_str: Currency string like "R$ 1.234,56"
    
    Returns:
        Decimal value
    """
    if not currency_str:
        return Decimal('0')
    
    try:
        # Remove currency symbol and spaces
        clean_str = re.sub(r'[^\d.,]', '', currency_str)
        
        # Handle Brazilian format (1.234,56 -> 1234.56)
        if ',' in clean_str and '.' in clean_str:
            # Both separators present
            clean_str = clean_str.replace('.', '').replace(',', '.')
        elif ',' in clean_str:
            # Only comma (decimal separator in Brazilian format)
            clean_str = clean_str.replace(',', '.')
        
        return Decimal(clean_str)
    
    except (ValueError, TypeError):
        return Decimal('0')

def format_cpf_cnpj(document: str) -> str:
    """
    Format CPF or CNPJ document
    
    Args:
        document: Document number string
    
    Returns:
        Formatted document string
    """
    if not document:
        return ''
    
    # Remove non-numeric characters
    clean_doc = re.sub(r'\D', '', document)
    
    if len(clean_doc) == 11:
        # CPF format: 123.456.789-01
        return f"{clean_doc[:3]}.{clean_doc[3:6]}.{clean_doc[6:9]}-{clean_doc[9:]}"
    elif len(clean_doc) == 14:
        # CNPJ format: 12.345.678/0001-90
        return f"{clean_doc[:2]}.{clean_doc[2:5]}.{clean_doc[5:8]}/{clean_doc[8:12]}-{clean_doc[12:]}"
    
    return document

def validate_cpf(cpf: str) -> bool:
    """
    Validate CPF document
    
    Args:
        cpf: CPF string
    
    Returns:
        True if valid, False otherwise
    """
    # Remove non-numeric characters
    cpf = re.sub(r'\D', '', cpf)
    
    # Check length
    if len(cpf) != 11:
        return False
    
    # Check for known invalid CPFs
    if cpf in ['00000000000', '11111111111', '22222222222', '33333333333',
               '44444444444', '55555555555', '66666666666', '77777777777',
               '88888888888', '99999999999']:
        return False
    
    # Validate check digits
    def calculate_digit(cpf_digits, weights):
        total = sum(int(digit) * weight for digit, weight in zip(cpf_digits, weights))
        remainder = total % 11
        return 0 if remainder < 2 else 11 - remainder
    
    # First check digit
    first_digit = calculate_digit(cpf[:9], range(10, 1, -1))
    if first_digit != int(cpf[9]):
        return False
    
    # Second check digit
    second_digit = calculate_digit(cpf[:10], range(11, 1, -1))
    if second_digit != int(cpf[10]):
        return False
    
    return True

def validate_cnpj(cnpj: str) -> bool:
    """
    Validate CNPJ document
    
    Args:
        cnpj: CNPJ string
    
    Returns:
        True if valid, False otherwise
    """
    # Remove non-numeric characters
    cnpj = re.sub(r'\D', '', cnpj)
    
    # Check length
    if len(cnpj) != 14:
        return False
    
    # Check for known invalid CNPJs
    if cnpj in ['00000000000000', '11111111111111', '22222222222222']:
        return False
    
    # Validate check digits
    def calculate_digit(cnpj_digits, weights):
        total = sum(int(digit) * weight for digit, weight in zip(cnpj_digits, weights))
        remainder = total % 11
        return 0 if remainder < 2 else 11 - remainder
    
    # First check digit
    first_weights = [5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
    first_digit = calculate_digit(cnpj[:12], first_weights)
    if first_digit != int(cnpj[12]):
        return False
    
    # Second check digit
    second_weights = [6, 5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
    second_digit = calculate_digit(cnpj[:13], second_weights)
    if second_digit != int(cnpj[13]):
        return False
    
    return True

def sanitize_filename(filename: str) -> str:
    """
    Sanitize filename for safe file operations
    
    Args:
        filename: Original filename
    
    Returns:
        Sanitized filename
    """
    # Remove or replace invalid characters
    filename = re.sub(r'[<>:"/\\|?*]', '_', filename)
    
    # Remove control characters
    filename = re.sub(r'[\x00-\x1f\x7f-\x9f]', '', filename)
    
    # Normalize unicode characters
    filename = unicodedata.normalize('NFKD', filename)
    
    # Limit length
    if len(filename) > 255:
        name, ext = os.path.splitext(filename)
        filename = name[:255-len(ext)] + ext
    
    return filename.strip()

def generate_hash(data: str, algorithm: str = 'md5') -> str:
    """
    Generate hash from string data
    
    Args:
        data: Data to hash
        algorithm: Hash algorithm (md5, sha1, sha256)
    
    Returns:
        Hash string
    """
    try:
        hash_obj = hashlib.new(algorithm)
        hash_obj.update(data.encode('utf-8'))
        return hash_obj.hexdigest()
    except ValueError:
        # Fallback to md5 if algorithm not available
        return hashlib.md5(data.encode('utf-8')).hexdigest()

def safe_divide(numerator: Union[int, float, Decimal], 
                denominator: Union[int, float, Decimal], 
                default: Union[int, float, Decimal] = 0) -> Decimal:
    """
    Safe division that handles division by zero
    
    Args:
        numerator: Numerator value
        denominator: Denominator value
        default: Default value if division by zero
    
    Returns:
        Division result or default value
    """
    try:
        num = Decimal(str(numerator))
        den = Decimal(str(denominator))
        
        if den == 0:
            return Decimal(str(default))
        
        return num / den
    
    except (ValueError, TypeError):
        return Decimal(str(default))

def truncate_text(text: str, max_length: int, suffix: str = '...') -> str:
    """
    Truncate text to maximum length
    
    Args:
        text: Text to truncate
        max_length: Maximum length
        suffix: Suffix to add if truncated
    
    Returns:
        Truncated text
    """
    if not text or len(text) <= max_length:
        return text
    
    return text[:max_length - len(suffix)] + suffix

def parse_date(date_str: str, formats: List[str] = None) -> Optional[datetime]:
    """
    Parse date string using multiple formats
    
    Args:
        date_str: Date string to parse
        formats: List of date formats to try
    
    Returns:
        Parsed datetime or None
    """
    if not date_str:
        return None
    
    if formats is None:
        formats = [
            '%d/%m/%Y',
            '%d/%m/%Y %H:%M',
            '%d/%m/%Y %H:%M:%S',
            '%Y-%m-%d',
            '%Y-%m-%d %H:%M',
            '%Y-%m-%d %H:%M:%S',
            '%d-%m-%Y',
            '%d-%m-%Y %H:%M',
            '%d-%m-%Y %H:%M:%S'
        ]
    
    for fmt in formats:
        try:
            return datetime.strptime(date_str.strip(), fmt)
        except ValueError:
            continue
    
    return None

def format_date(date_obj: datetime, format_str: str = '%d/%m/%Y') -> str:
    """
    Format datetime object to string
    
    Args:
        date_obj: Datetime object
        format_str: Format string
    
    Returns:
        Formatted date string
    """
    if not date_obj:
        return ''
    
    try:
        return date_obj.strftime(format_str)
    except (ValueError, TypeError):
        return ''

def get_file_size(file_path: str) -> int:
    """
    Get file size in bytes
    
    Args:
        file_path: Path to file
    
    Returns:
        File size in bytes, 0 if file doesn't exist
    """
    try:
        return os.path.getsize(file_path)
    except (OSError, FileNotFoundError):
        return 0

def format_file_size(size_bytes: int) -> str:
    """
    Format file size in human readable format
    
    Args:
        size_bytes: Size in bytes
    
    Returns:
        Formatted size string
    """
    if size_bytes == 0:
        return '0 B'
    
    size_names = ['B', 'KB', 'MB', 'GB', 'TB']
    i = 0
    size = float(size_bytes)
    
    while size >= 1024.0 and i < len(size_names) - 1:
        size /= 1024.0
        i += 1
    
    return f'{size:.1f} {size_names[i]}'

def create_backup_filename(original_filename: str, suffix: str = None) -> str:
    """
    Create backup filename with timestamp
    
    Args:
        original_filename: Original filename
        suffix: Optional suffix
    
    Returns:
        Backup filename
    """
    name, ext = os.path.splitext(original_filename)
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    
    if suffix:
        return f"{name}_{suffix}_{timestamp}{ext}"
    else:
        return f"{name}_backup_{timestamp}{ext}"

def deep_merge_dicts(dict1: Dict[str, Any], dict2: Dict[str, Any]) -> Dict[str, Any]:
    """
    Deep merge two dictionaries
    
    Args:
        dict1: First dictionary
        dict2: Second dictionary (takes precedence)
    
    Returns:
        Merged dictionary
    """
    result = dict1.copy()
    
    for key, value in dict2.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = deep_merge_dicts(result[key], value)
        else:
            result[key] = value
    
    return result

def flatten_dict(d: Dict[str, Any], parent_key: str = '', sep: str = '.') -> Dict[str, Any]:
    """
    Flatten nested dictionary
    
    Args:
        d: Dictionary to flatten
        parent_key: Parent key prefix
        sep: Separator for nested keys
    
    Returns:
        Flattened dictionary
    """
    items = []
    
    for k, v in d.items():
        new_key = f"{parent_key}{sep}{k}" if parent_key else k
        
        if isinstance(v, dict):
            items.extend(flatten_dict(v, new_key, sep=sep).items())
        else:
            items.append((new_key, v))
    
    return dict(items)

def retry_operation(operation, max_attempts: int = 3, delay: float = 1.0, 
                   exceptions: tuple = (Exception,)) -> Any:
    """
    Retry operation with exponential backoff
    
    Args:
        operation: Function to retry
        max_attempts: Maximum number of attempts
        delay: Initial delay between attempts
        exceptions: Exceptions to catch and retry
    
    Returns:
        Operation result
    
    Raises:
        Last exception if all attempts fail
    """
    import time
    
    last_exception = None
    
    for attempt in range(max_attempts):
        try:
            return operation()
        except exceptions as e:
            last_exception = e
            if attempt < max_attempts - 1:
                time.sleep(delay * (2 ** attempt))  # Exponential backoff
            continue
    
    raise last_exception

def is_valid_email(email: str) -> bool:
    """
    Validate email address format
    
    Args:
        email: Email address to validate
    
    Returns:
        True if valid email format
    """
    if not email:
        return False
    
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))

def normalize_phone(phone: str) -> str:
    """
    Normalize phone number format
    
    Args:
        phone: Phone number string
    
    Returns:
        Normalized phone number
    """
    if not phone:
        return ''
    
    # Remove non-numeric characters
    clean_phone = re.sub(r'\D', '', phone)
    
    # Format based on length
    if len(clean_phone) == 11:
        # Mobile: (XX) 9XXXX-XXXX
        return f"({clean_phone[:2]}) {clean_phone[2:7]}-{clean_phone[7:]}"
    elif len(clean_phone) == 10:
        # Landline: (XX) XXXX-XXXX
        return f"({clean_phone[:2]}) {clean_phone[2:6]}-{clean_phone[6:]}"
    
    return phone