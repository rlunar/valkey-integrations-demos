# tasks.py
from celery_config import celery_app
from models import Flight, Passenger, FlightNotification, NotificationType, FlightStatus
from datetime import datetime
from typing import Dict
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Task retry settings
TASK_RETRY_KWARGS = {
    'max_retries': 3,
    'countdown': 5,  # Wait 5 seconds before retry
    'autoretry_for': (Exception,),
}

@celery_app.task(bind=True, **TASK_RETRY_KWARGS)
def send_email_notification(self, notification_data: Dict) -> Dict:
    """
    Send email notification to passenger about flight status
    
    Args:
        notification_data: Dictionary containing notification information
        
    Returns:
        Dict with status and details
    """
    try:
        # Validate data using Pydantic
        notification = FlightNotification(**notification_data)
        
        logger.info(f"Sending email to {notification.passenger.email}")
        logger.info(f"Subject: Flight {notification.flight.flight_number} Update")
        logger.info(f"Message: {notification.message}")
        
        # In production, integrate with services like:
        # - Amazon SES
        # - SendGrid
        # - Mailgun
        
        # Simulated email sending
        email_content = {
            'to': notification.passenger.email,
            'subject': f'Flight {notification.flight.flight_number} - {notification.flight.status.value.title()}',
            'body': format_email_body(notification),
            'sent_at': datetime.utcnow().isoformat()
        }
        
        logger.info(f"✓ Email sent successfully to {notification.passenger.email}")
        return {
            'status': 'success',
            'notification_type': 'email',
            'passenger_id': notification.passenger.passenger_id,
            'details': email_content
        }
        
    except Exception as exc:
        logger.error(f"✗ Error sending email: {exc}")
        raise self.retry(exc=exc)

@celery_app.task(bind=True, **TASK_RETRY_KWARGS)
def send_sms_notification(self, notification_data: Dict) -> Dict:
    """
    Send SMS notification to passenger about flight status
    
    Args:
        notification_data: Dictionary containing notification information
        
    Returns:
        Dict with status and details
    """
    try:
        notification = FlightNotification(**notification_data)
        
        logger.info(f"Sending SMS to {notification.passenger.phone_number}")
        logger.info(f"Message: {notification.message}")
        
        # In production, integrate with services like:
        # - Amazon SNS
        # - Twilio
        # - Vonage
        
        # Simulated SMS sending
        sms_content = {
            'to': notification.passenger.phone_number,
            'message': format_sms_message(notification),
            'sent_at': datetime.utcnow().isoformat()
        }
        
        logger.info(f"✓ SMS sent successfully to {notification.passenger.phone_number}")
        return {
            'status': 'success',
            'notification_type': 'sms',
            'passenger_id': notification.passenger.passenger_id,
            'details': sms_content
        }
        
    except Exception as exc:
        logger.error(f"✗ Error sending SMS: {exc}")
        raise self.retry(exc=exc)

@celery_app.task(bind=True, **TASK_RETRY_KWARGS)
def send_push_notification(self, notification_data: Dict) -> Dict:
    """
    Send push notification to passenger's mobile device
    
    Args:
        notification_data: Dictionary containing notification information
        
    Returns:
        Dict with status and details
    """
    try:
        notification = FlightNotification(**notification_data)
        
        if not notification.passenger.push_token:
            logger.warning(f"⚠ No push token for passenger {notification.passenger.passenger_id}")
            return {
                'status': 'skipped',
                'reason': 'no_push_token',
                'passenger_id': notification.passenger.passenger_id
            }
        
        logger.info(f"Sending push notification to device {notification.passenger.push_token[:10]}...")
        
        # In production, integrate with services like:
        # - Firebase Cloud Messaging (FCM)
        # - Apple Push Notification Service (APNS)
        # - Expo Push Notifications
        
        # Simulated push notification
        push_content = {
            'token': notification.passenger.push_token,
            'title': f'Flight {notification.flight.flight_number} Update',
            'body': notification.message,
            'data': {
                'flight_number': notification.flight.flight_number,
                'status': notification.flight.status.value,
                'gate': notification.flight.gate
            },
            'sent_at': datetime.utcnow().isoformat()
        }
        
        logger.info(f"✓ Push notification sent successfully")
        return {
            'status': 'success',
            'notification_type': 'push',
            'passenger_id': notification.passenger.passenger_id,
            'details': push_content
        }
        
    except Exception as exc:
        logger.error(f"✗ Error sending push notification: {exc}")
        raise self.retry(exc=exc)

@celery_app.task
def notify_passengers(flight_data: Dict, new_status: str) -> Dict:
    """
    Coordinate sending notifications to all passengers on a flight
    
    Args:
        flight_data: Dictionary containing flight information
        new_status: New flight status
        
    Returns:
        Dict with summary of notifications sent
    """
    try:
        flight = Flight(**flight_data)
        flight.status = FlightStatus(new_status)
        
        # Generate appropriate message based on status
        message = generate_status_message(flight)
        
        results = {
            'flight_number': flight.flight_number,
            'status': new_status,
            'passengers_notified': 0,
            'notifications_sent': []
        }
        
        # Send notifications to all passengers based on their preferences
        for passenger in flight.passengers:
            notification_data = {
                'flight': flight.dict(),
                'passenger': passenger.dict(),
                'message': message,
                'timestamp': datetime.utcnow().isoformat()
            }
            
            # Send notifications based on passenger preferences
            for notif_type in passenger.preferred_notifications:
                if notif_type == NotificationType.EMAIL:
                    task = send_email_notification.delay(
                        {**notification_data, 'notification_type': 'email'}
                    )
                elif notif_type == NotificationType.SMS:
                    task = send_sms_notification.delay(
                        {**notification_data, 'notification_type': 'sms'}
                    )
                elif notif_type == NotificationType.PUSH:
                    task = send_push_notification.delay(
                        {**notification_data, 'notification_type': 'push'}
                    )
                
                results['notifications_sent'].append({
                    'passenger_id': passenger.passenger_id,
                    'type': notif_type.value,
                    'task_id': task.id
                })
            
            results['passengers_notified'] += 1
        
        logger.info(f"✓ Initiated notifications for {results['passengers_notified']} passengers on flight {flight.flight_number}")
        return results
        
    except Exception as exc:
        logger.error(f"✗ Error coordinating passenger notifications: {exc}")
        raise

# Helper functions for message formatting

def format_email_body(notification: FlightNotification) -> str:
    """Format email body with HTML"""
    return f"""
    <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                <h2 style="color: #0066cc;">Flight Update for {notification.flight.flight_number}</h2>
                <p>Dear {notification.passenger.first_name} {notification.passenger.last_name},</p>
                
                <p style="font-size: 16px; background-color: #f0f8ff; padding: 15px; border-left: 4px solid #0066cc;">
                    {notification.message}
                </p>
                
                <h3 style="color: #0066cc;">Flight Details:</h3>
                <ul style="list-style-type: none; padding-left: 0;">
                    <li style="padding: 5px 0;"><strong>Flight:</strong> {notification.flight.airline} {notification.flight.flight_number}</li>
                    <li style="padding: 5px 0;"><strong>Route:</strong> {notification.flight.origin} → {notification.flight.destination}</li>
                    <li style="padding: 5px 0;"><strong>Status:</strong> <span style="color: #ff6600; font-weight: bold;">{notification.flight.status.value.title()}</span></li>
                    <li style="padding: 5px 0;"><strong>Scheduled Departure:</strong> {notification.flight.scheduled_departure.strftime("%B %d, %Y at %I:%M %p UTC")}</li>
                    {f'<li style="padding: 5px 0;"><strong>Gate:</strong> {notification.flight.gate}</li>' if notification.flight.gate else ''}
                </ul>
                
                <p style="margin-top: 30px; color: #666;">Thank you for choosing {notification.flight.airline}.</p>
                <hr style="border: none; border-top: 1px solid #ddd; margin: 20px 0;">
                <p style="font-size: 12px; color: #999;">This is an automated notification. Please do not reply to this email.</p>
            </div>
        </body>
    </html>
    """

def format_sms_message(notification: FlightNotification) -> str:
    """Format concise SMS message"""
    gate_info = f" Gate {notification.flight.gate}." if notification.flight.gate else ""
    return f"{notification.flight.airline} {notification.flight.flight_number}: {notification.message}{gate_info}"

def generate_status_message(flight: Flight) -> str:
    """Generate appropriate message based on flight status"""
    messages = {
        FlightStatus.DELAYED: f"Your flight has been delayed. New departure time will be announced shortly.",
        FlightStatus.BOARDING: f"Your flight is now boarding at gate {flight.gate}. Please proceed to the gate.",
        FlightStatus.CANCELLED: f"We regret to inform you that your flight has been cancelled. Please contact customer service for rebooking.",
        FlightStatus.DEPARTED: f"Your flight has departed and is en route to {flight.destination}.",
        FlightStatus.ARRIVED: f"Your flight has arrived at {flight.destination}. Welcome!"
    }
    return messages.get(flight.status, f"Flight status updated to {flight.status.value}")
