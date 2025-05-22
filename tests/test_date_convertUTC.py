from datetime import datetime, timezone, timedelta
from app.utils.date_convertUTC import ensure_utc

def test_ensure_utc_with_naive_datetime():
    """Test avec une date sans fuseau horaire"""
    # Arrange
    naive_date = datetime(2024, 3, 15, 14, 0)  # 14h00 sans fuseau horaire
    
    # Act
    utc_date = ensure_utc(naive_date)
    
    # Assert
    assert utc_date.tzinfo == timezone.utc, "La date devrait avoir le fuseau horaire UTC"
    assert utc_date.hour == 14, "L'heure devrait rester à 14h"
    assert utc_date.minute == 0, "Les minutes devraient rester à 0"

def test_ensure_utc_with_utc_datetime():
    """Test avec une date déjà en UTC"""
    # Arrange
    utc_date = datetime(2024, 3, 15, 14, 0, tzinfo=timezone.utc)
    
    # Act
    result = ensure_utc(utc_date)
    
    # Assert
    assert result.tzinfo == timezone.utc, "La date devrait rester en UTC"
    assert result == utc_date, "La date ne devrait pas être modifiée"

def test_ensure_utc_with_other_timezone():
    """Test avec une date dans un autre fuseau horaire (Paris, UTC+1)"""
    # Arrange
    paris_tz = timezone(timedelta(hours=1))
    paris_date = datetime(2024, 3, 15, 14, 0, tzinfo=paris_tz)
    
    # Act
    utc_date = ensure_utc(paris_date)
    
    # Assert
    assert utc_date.tzinfo == timezone.utc, "La date devrait être convertie en UTC"
    assert utc_date.hour == 13, "L'heure devrait être 13h en UTC (14h - 1h)"
    assert utc_date.minute == 0, "Les minutes devraient rester à 0"

def test_ensure_utc_with_midnight():
    """Test avec une date à minuit sans heure"""
    # Arrange
    midnight_date = datetime(2024, 3, 15, 0, 0, 0, 0)  # minuit sans fuseau horaire
    
    # Act
    utc_date = ensure_utc(midnight_date)
    
    # Assert
    assert utc_date.tzinfo == timezone.utc, "La date devrait avoir le fuseau horaire UTC"
    assert utc_date.hour == 0, "L'heure devrait rester à 0h"
    assert utc_date.minute == 0, "Les minutes devraient rester à 0"
    assert utc_date.second == 0, "Les secondes devraient rester à 0"
    assert utc_date.microsecond == 0, "Les microsecondes devraient rester à 0"

def test_ensure_utc_with_different_timezones():
    """Test avec différents fuseaux horaires"""
    # Arrange
    test_cases = [
        (timezone(timedelta(hours=2)), 14, 12),  # UTC+2
        (timezone(timedelta(hours=-5)), 14, 19),  # UTC-5
        (timezone(timedelta(hours=8)), 14, 6),   # UTC+8
    ]
    
    for tz, input_hour, expected_hour in test_cases:
        # Arrange
        date_with_tz = datetime(2024, 3, 15, input_hour, 0, tzinfo=tz)
        
        # Act
        utc_date = ensure_utc(date_with_tz)
        
        # Assert
        assert utc_date.tzinfo == timezone.utc, f"La date avec {tz} devrait être convertie en UTC"
        assert utc_date.hour == expected_hour, f"Pour {tz}, {input_hour}h devrait devenir {expected_hour}h en UTC"
        assert utc_date.minute == 0, "Les minutes devraient rester à 0" 