"""
Session 4: Normalization Rules
Clean the data before it hits the database

Learning points:
- Date parsing and timezone handling
- Unit standardization
- Status enum mapping
- Handling missing data
- Validation rules
"""
from datetime import datetime, date
from typing import Optional, Any
from decimal import Decimal, InvalidOperation


def normalize_date(value: Any, date_format: Optional[str] = None) -> Optional[date]:
    """
    Normalize date values to standard date object

    Learning points:
    - CSV dates can be in many formats
    - Empty/null handling
    - Invalid date handling

    Common formats:
    - YYYY-MM-DD
    - MM/DD/YYYY
    - DD-MM-YYYY
    """
    if not value or value == '':
        return None

    if isinstance(value, date):
        return value

    if isinstance(value, datetime):
        return value.date()

    if isinstance(value, str):
        value = value.strip()

        # Try specific format if provided
        if date_format:
            try:
                return datetime.strptime(value, date_format).date()
            except ValueError:
                pass

        # Try common formats
        formats = [
            '%Y-%m-%d',
            '%m/%d/%Y',
            '%d-%m-%Y',
            '%Y/%m/%d',
            '%d/%m/%Y',
            '%Y-%m-%d %H:%M:%S',  # With time
        ]

        for fmt in formats:
            try:
                return datetime.strptime(value, fmt).date()
            except ValueError:
                continue

    raise ValueError(f"Unable to parse date: {value}")


def normalize_datetime(value: Any, datetime_format: Optional[str] = None) -> Optional[datetime]:
    """
    Normalize datetime values to standard datetime object

    Learning point: Timezone handling policy
    For this workshop: assume all times are UTC or local factory time
    """
    if not value or value == '':
        return None

    if isinstance(value, datetime):
        return value

    if isinstance(value, str):
        value = value.strip()

        # Try specific format if provided
        if datetime_format:
            try:
                return datetime.strptime(value, datetime_format)
            except ValueError:
                pass

        # Try common formats
        formats = [
            '%Y-%m-%d %H:%M:%S',
            '%Y-%m-%dT%H:%M:%S',
            '%Y-%m-%d %H:%M:%S.%f',
            '%m/%d/%Y %H:%M:%S',
            '%Y-%m-%d',  # Date only - assume midnight
        ]

        for fmt in formats:
            try:
                return datetime.strptime(value, fmt)
            except ValueError:
                continue

    raise ValueError(f"Unable to parse datetime: {value}")


def normalize_decimal(value: Any, precision: int = 4) -> Optional[Decimal]:
    """
    Normalize numeric values to Decimal

    Learning points:
    - Floating point precision issues
    - Using Decimal for measurements
    - Handling various numeric formats
    """
    if not value or value == '':
        return None

    if isinstance(value, Decimal):
        return value

    if isinstance(value, (int, float)):
        return Decimal(str(value))

    if isinstance(value, str):
        # Remove whitespace and common formatting
        value = value.strip().replace(',', '')

        try:
            return Decimal(value)
        except (InvalidOperation, ValueError):
            raise ValueError(f"Unable to parse decimal: {value}")

    raise ValueError(f"Unable to parse decimal: {value}")


def normalize_unit(value: str, unit: str) -> tuple[Optional[Decimal], str]:
    """
    Normalize measurement units

    Learning point: Unit standardization
    Different sources might use different units

    Examples:
    - mm vs cm vs m
    - % vs decimal (0.995 vs 99.5%)
    - N vs kN
    """
    if not value:
        return None, unit

    numeric_value = normalize_decimal(value)

    if not numeric_value:
        return None, unit

    # Standardize unit naming
    unit = unit.strip().lower()

    # Percentage handling
    if unit in ['%', 'percent', 'pct']:
        unit = '%'
        # If value is > 1, assume it's already a percentage
        # If value is <= 1, assume it's a decimal ratio
        if numeric_value <= 1:
            numeric_value = numeric_value * 100

    # Length conversions - standardize to mm
    elif unit in ['cm', 'centimeter', 'centimeters']:
        numeric_value = numeric_value * 10
        unit = 'mm'
    elif unit in ['m', 'meter', 'meters']:
        numeric_value = numeric_value * 1000
        unit = 'mm'
    elif unit in ['mm', 'millimeter', 'millimeters']:
        unit = 'mm'

    # Force conversions - standardize to N
    elif unit in ['kn', 'kilonewton', 'kilonewtons']:
        numeric_value = numeric_value * 1000
        unit = 'N'
    elif unit in ['n', 'newton', 'newtons']:
        unit = 'N'

    return numeric_value, unit


def normalize_status(value: str, status_type: str) -> str:
    """
    Normalize status values to database enums

    Learning point: String normalization and enum mapping

    Status types:
    - inspection_result: PASS, FAIL, CONDITIONAL
    - ncr_status: OPEN, IN_REVIEW, CLOSED, CANCELLED
    - ncr_severity: LOW, MEDIUM, HIGH, CRITICAL
    """
    if not value:
        return None

    value = value.strip().upper().replace('-', '_').replace(' ', '_')

    if status_type == 'inspection_result':
        # Map variations to standard enum
        mapping = {
            'PASS': 'PASS',
            'PASSED': 'PASS',
            'OK': 'PASS',
            'GOOD': 'PASS',
            'FAIL': 'FAIL',
            'FAILED': 'FAIL',
            'REJECT': 'FAIL',
            'REJECTED': 'FAIL',
            'CONDITIONAL': 'CONDITIONAL',
            'COND': 'CONDITIONAL',
            'PARTIAL': 'CONDITIONAL',
        }
        result = mapping.get(value)
        if not result:
            raise ValueError(f"Unknown inspection result: {value}")
        return result

    elif status_type == 'ncr_status':
        mapping = {
            'OPEN': 'OPEN',
            'OPENED': 'OPEN',
            'NEW': 'OPEN',
            'IN_REVIEW': 'IN_REVIEW',
            'REVIEW': 'IN_REVIEW',
            'REVIEWING': 'IN_REVIEW',
            'CLOSED': 'CLOSED',
            'CLOSE': 'CLOSED',
            'RESOLVED': 'CLOSED',
            'CANCELLED': 'CANCELLED',
            'CANCELED': 'CANCELLED',
            'CANCEL': 'CANCELLED',
        }
        result = mapping.get(value)
        if not result:
            raise ValueError(f"Unknown NCR status: {value}")
        return result

    elif status_type == 'ncr_severity':
        mapping = {
            'LOW': 'LOW',
            'L': 'LOW',
            'MINOR': 'LOW',
            'MEDIUM': 'MEDIUM',
            'MED': 'MEDIUM',
            'M': 'MEDIUM',
            'MODERATE': 'MEDIUM',
            'HIGH': 'HIGH',
            'H': 'HIGH',
            'MAJOR': 'HIGH',
            'CRITICAL': 'CRITICAL',
            'CRIT': 'CRITICAL',
            'C': 'CRITICAL',
            'SEVERE': 'CRITICAL',
        }
        result = mapping.get(value)
        if not result:
            raise ValueError(f"Unknown NCR severity: {value}")
        return result

    raise ValueError(f"Unknown status type: {status_type}")


def validate_row(row: dict, required_fields: list, row_num: int = 0) -> list[str]:
    """
    Validate that required fields are present

    Learning point: Validation vs rejection
    - Some missing data is OK (nullable fields)
    - Some missing data breaks the record (required fields)

    Returns list of validation errors (empty if valid)
    """
    errors = []

    for field in required_fields:
        value = row.get(field)
        if value is None or (isinstance(value, str) and value.strip() == ''):
            errors.append(f"Row {row_num}: Missing required field '{field}'")

    return errors


def clean_string(value: Any, max_length: Optional[int] = None) -> Optional[str]:
    """
    Clean string values

    Learning points:
    - Whitespace handling
    - Null/empty handling
    - Length constraints
    """
    if value is None:
        return None

    if not isinstance(value, str):
        value = str(value)

    # Strip whitespace
    value = value.strip()

    # Empty string to None
    if value == '':
        return None

    # Truncate if needed
    if max_length and len(value) > max_length:
        value = value[:max_length]

    return value


# Example normalization pipeline for inspection row
def normalize_inspection_row(row: dict) -> dict:
    """
    Example: Normalize a full inspection row

    This shows how all the normalization functions work together
    Participants will implement this in Session 4
    """
    try:
        normalized = {
            'inspection_id': clean_string(row.get('inspection_id'), 100),
            'site': clean_string(row.get('site'), 100),
            'production_line': clean_string(row.get('production_line'), 100),
            'supplier': clean_string(row.get('supplier'), 200),
            'part_number': clean_string(row.get('part_number'), 100),
            'part_description': clean_string(row.get('part_description')),
            'inspection_date': normalize_date(row.get('inspection_date')),
            'inspector': clean_string(row.get('inspector'), 200),
            'result': normalize_status(row.get('result'), 'inspection_result'),
            'notes': clean_string(row.get('notes')),
        }

        # Handle measurements with units
        measurement_value = row.get('measurement_value')
        measurement_unit = row.get('measurement_unit')

        if measurement_value:
            value, unit = normalize_unit(measurement_value, measurement_unit or '')
            normalized['measurement_value'] = value
            normalized['measurement_unit'] = unit
        else:
            normalized['measurement_value'] = None
            normalized['measurement_unit'] = None

        # Specs
        normalized['spec_min'] = normalize_decimal(row.get('spec_min'))
        normalized['spec_max'] = normalize_decimal(row.get('spec_max'))

        return normalized

    except Exception as e:
        raise ValueError(f"Normalization failed: {str(e)}")
