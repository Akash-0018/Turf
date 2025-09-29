import json
import requests
from django.conf import settings
from facilities.models import Facility, TimeSlot
from django.urls import reverse
from django.contrib.sites.shortcuts import get_current_site
from django.template.loader import render_to_string

ADMIN_WHATSAPP = "+918074101457"

def get_whatsapp_message_template(match_request, message_type='new_request'):
    """
    Generate WhatsApp message template based on the type of message
    """
    if message_type == 'new_request':
        return f"""*New Match Request*
🏃‍♂️ Challenger Team: {match_request.challenger.name}
🎯 Opponent Team: {match_request.opponent.name}
📅 Preferred Date: {match_request.preferred_date.strftime('%d-%m-%Y')}
⏰ Time: {match_request.preferred_time.get_slot_time_display() if match_request.preferred_time else 'Not specified'}
🏟️ Facility: {match_request.preferred_facility.name if match_request.preferred_facility else 'Not specified'}
📝 Message: {match_request.message if match_request.message else 'No message'}

Please forward this to the opponent team captain."""

    elif message_type == 'accepted':
        return f"""*Match Request Accepted*
✅ The match request between {match_request.challenger.name} and {match_request.opponent.name} has been accepted!

Details:
📅 Date: {match_request.preferred_date.strftime('%d-%m-%Y')}
⏰ Time: {match_request.preferred_time.get_slot_time_display() if match_request.preferred_time else 'Not specified'}
🏟️ Facility: {match_request.preferred_facility.name if match_request.preferred_facility else 'Not specified'}"""

    elif message_type == 'rejected':
        return f"""*Match Request Rejected*
❌ The match request between {match_request.challenger.name} and {match_request.opponent.name} has been rejected.

Reason: {match_request.response_message if match_request.response_message else 'No reason provided'}"""

    elif message_type == 'rescheduled':
        return f"""*Match Rescheduling Request*
🔄 Match request has been rescheduled

Details:
🏃‍♂️ Teams: {match_request.challenger.name} vs {match_request.opponent.name}
📅 New Date: {match_request.preferred_date.strftime('%d-%m-%Y')}
⏰ New Time: {match_request.preferred_time.get_slot_time_display() if match_request.preferred_time else 'Not specified'}
📝 Reason: {match_request.message}

The match request needs to be approved again."""

def send_whatsapp_message(phone_number, message):
    """
    Send WhatsApp message using WhatsApp Business API
    """
    try:
        # Format the phone number (remove '+' and any spaces)
        formatted_phone = phone_number.replace('+', '').replace(' ', '')
        
        # Set up the API request
        url = f'https://graph.facebook.com/{settings.WHATSAPP_API_VERSION}/{settings.WHATSAPP_PHONE_NUMBER_ID}/messages'
        
        headers = {
            'Authorization': f'Bearer {settings.WHATSAPP_ACCESS_TOKEN}',
            'Content-Type': 'application/json',
        }
        
        payload = {
            'messaging_product': 'whatsapp',
            'recipient_type': 'individual',
            'to': formatted_phone,
            'type': 'text',
            'text': {
                'preview_url': False,
                'body': message
            }
        }
        
        # Make the API request
        response = requests.post(url, headers=headers, json=payload)
        response_data = response.json()
        
        # Log the response for debugging
        print(f'WhatsApp API Response: {response_data}')
        
        if response.status_code == 200:
            messages_sent = response_data.get('messages', [])
            if messages_sent:
                print(f'Message sent successfully. Message ID: {messages_sent[0].get("id")}')
                return True
        
        print(f'Failed to send message. Status code: {response.status_code}')
        print(f'Error details: {response_data}')
        return False
        
    except Exception as e:
        print(f'Error sending WhatsApp message: {str(e)}')
        return False

def notify_match_request(match_request, notification_type='new_request'):
    """
    Handle match request notifications via WhatsApp
    """
    message = get_whatsapp_message_template(match_request, notification_type)
    sent_to = []
    success = True
    
    # Get captain's phone numbers
    opponent_captain_phone = match_request.opponent.captain.phone_number if match_request.opponent.captain else None
    challenger_captain_phone = match_request.challenger.captain.phone_number if match_request.challenger.captain else None
    
    # Always notify admin first
    if send_whatsapp_message(ADMIN_WHATSAPP, message):
        sent_to.append('admin')
    else:
        success = False
        print(f'Failed to send WhatsApp message to admin: {ADMIN_WHATSAPP}')
    
    # For new requests and rescheduling, notify the opponent's captain
    if notification_type in ['new_request', 'rescheduled']:
        if opponent_captain_phone:
            if send_whatsapp_message(opponent_captain_phone, message):
                sent_to.append('opponent captain')
            else:
                success = False
                print(f'Failed to send WhatsApp message to opponent captain: {opponent_captain_phone}')
    
    # For accept/reject notifications, always notify the challenger's captain
    if notification_type in ['accepted', 'rejected']:
        if challenger_captain_phone:
            if send_whatsapp_message(challenger_captain_phone, message):
                sent_to.append('challenger captain')
            else:
                success = False
                print(f'Failed to send WhatsApp message to challenger captain: {challenger_captain_phone}')
    
    # Log the notification results
    print(f'Match request notification ({notification_type}) sent to: {", ".join(sent_to)}')
    if not success:
        print('Some notifications failed to send. Check the logs above for details.')
    
    return success