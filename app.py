from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
import requests
import os
from dotenv import load_dotenv
from data import waste_data, synonym_map
import re
from models import db, UserQuery, Donation, WasteItem
import json
import time

# Load environment variables
load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', 'eco-bin-secret-key')

# MySQL Database Configuration
app.config['SQLALCHEMY_DATABASE_URI'] = (
    f"mysql://{os.getenv('MYSQL_USER')}:{os.getenv('MYSQL_PASSWORD')}"
    f"@{os.getenv('MYSQL_HOST')}:{os.getenv('MYSQL_PORT', 3306)}"
    f"/{os.getenv('MYSQL_DB')}"
)
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize database
db.init_app(app)

# Paystack API credentials
PAYSTACK_PUBLIC_KEY = os.getenv('PAYSTACK_PUBLIC_KEY')
PAYSTACK_SECRET_KEY = os.getenv('PAYSTACK_SECRET_KEY')
TEST_MODE = os.getenv('TEST_MODE', 'False').lower() == 'true'

# Create tables and populate data on startup
with app.app_context():
    db.create_all()
    # Populate waste items from data.py if empty
    if WasteItem.query.count() == 0:
        print("Populating waste items from data.py...")
        for name, data in waste_data.items():
            item = WasteItem(
                name=name,
                category=data['category'],
                tip=data['tip'],
                synonyms=','.join(data.get('synonyms', []))
            )
            db.session.add(item)
        db.session.commit()
        print(f"✅ Added {len(waste_data)} waste items to database")
    else:
        print("✅ Waste items already populated")

def find_best_match(item_name):
    """
    Find the best matching item in the waste database
    Handles plurals, variations, and synonyms
    """
    item_name = item_name.lower().strip()
    
    # First check exact match
    if item_name in waste_data:
        return waste_data[item_name], item_name
    
    # Check synonyms
    if item_name in synonym_map:
        main_item = synonym_map[item_name]
        return waste_data[main_item], main_item
    
    # Check for plural/singular variations
    if item_name.endswith('s') and item_name[:-1] in waste_data:
        return waste_data[item_name[:-1]], item_name[:-1]
    elif not item_name.endswith('s') and item_name + 's' in waste_data:
        return waste_data[item_name + 's'], item_name + 's'
    
    # Check for partial matches and common variations
    for waste_item, data in waste_data.items():
        # Check if the search term is contained in the waste item or vice versa
        if (item_name in waste_item or waste_item in item_name) and len(item_name) > 2:
            return data, waste_item
        
        # Check for common word variations
        variations = [
            item_name.replace(' ', ''),
            item_name.replace(' ', '-'),
            item_name + 's',
            item_name[:-1] if item_name.endswith('s') else None
        ]
        
        for variation in variations:
            if variation and variation in waste_data:
                return waste_data[variation], variation
    
    return None, item_name

@app.route('/')
def index():
    # Get statistics from database
    total_items = WasteItem.query.filter_by(is_active=True).count()
    total_queries = UserQuery.query.count()
    total_donations = Donation.query.filter_by(payment_status='completed').count()
    
    return render_template('index.html', 
                         waste_data=waste_data,
                         total_items=total_items,
                         total_queries=total_queries,
                         total_donations=total_donations)

@app.route('/classify', methods=['POST'])
def classify_waste():
    item = request.form.get('item', '').strip().lower()
    
    if not item:
        flash('Please enter an item to classify.', 'error')
        return redirect(url_for('index'))
    
    # Clean up the input
    item = re.sub(r'[^\w\s]', '', item)
    item = ' '.join(item.split())
    
    # Find the best matching item
    result, matched_item = find_best_match(item)
    
    if result:
        category = result['category']
        tip = result['tip']
    else:
        category = 'Unknown'
        tip = 'Please check local waste disposal guidelines or contact your waste management provider.'
        matched_item = item
    
    # Log the query to database
    try:
        user_query = UserQuery(
            item_name=item,
            matched_item=matched_item,
            category=category,
            tip=tip,
            ip_address=request.remote_addr,
            user_agent=request.headers.get('User-Agent')
        )
        db.session.add(user_query)
        db.session.commit()
    except Exception as e:
        print(f"Error logging query: {e}")
    
    return render_template('result.html', 
                         item=item, 
                         matched_item=matched_item,
                         category=category, 
                         tip=tip)

@app.route('/donate', methods=['GET', 'POST'])
def donate():
    if request.method == 'POST':
        email = request.form.get('email')
        payment_method = request.form.get('payment_method', 'mpesa')
        amount = request.form.get('amount')
        
        # Validate common fields
        if not all([email, amount]):
            flash('Please fill all required fields.', 'error')
            return render_template('donate.html')
        
        try:
            amount = float(amount)
            if amount <= 0:
                flash('Amount must be greater than 0.', 'error')
                return render_template('donate.html')
            if amount < 10:
                flash('Minimum donation is KES 10.', 'error')
                return render_template('donate.html')
        except ValueError:
            flash('Please enter a valid amount.', 'error')
            return render_template('donate.html')
        
        # Create donation record
        donation = Donation(
            email=email,
            amount=amount,
            payment_method=payment_method,
            payment_status='pending'
        )
        
        # Handle M-Pesa payments
        if payment_method == 'mpesa':
            phone = request.form.get('phone')
            
            if not phone:
                flash('Please enter your M-Pesa phone number.', 'error')
                return render_template('donate.html')
                
            if not (phone.startswith('07') and len(phone) == 10 and phone.isdigit()):
                flash('Please enter a valid Kenyan phone number (07XX XXX XXX).', 'error')
                return render_template('donate.html')
            
            donation.phone = phone
            db.session.add(donation)
            db.session.commit()
            
            return process_paystack_transaction(donation)
        
        # Handle Card payments
        elif payment_method == 'card':
            db.session.add(donation)
            db.session.commit()
            
            # For card payments, we'll use Paystack's inline payment
            return render_template('card_payment.html', 
                                 donation=donation,
                                 paystack_public_key=PAYSTACK_PUBLIC_KEY,
                                 email=email,
                                 amount=amount)
        
        else:
            flash('Please select a payment method.', 'error')
            return render_template('donate.html')
    
    return render_template('donate.html')

def process_paystack_transaction(donation):
    """Use Paystack transaction initialization API (More Reliable)"""
    if TEST_MODE:
        donation.payment_status = 'completed'
        donation.transaction_id = f'TEST_{donation.id}'
        db.session.commit()
        flash(f'TEST MODE: Payment of KES {donation.amount} would be processed.', 'success')
        return render_template('donate.html')
    
    headers = {
        'Authorization': f'Bearer {PAYSTACK_SECRET_KEY}',
        'Content-Type': 'application/json'
    }
    
    # Convert phone to international format
    phone = donation.phone
    if phone.startswith('0'):
        phone = '254' + phone[1:]  # 254 format for Paystack
    
    payload = {
        'email': donation.email,
        'amount': int(donation.amount * 100),  # Convert to kobo
        'currency': 'KES',
        'channels': ['mobile_money', 'card'],
        'mobile_money': {
            'phone': phone,
            'provider': 'mpesa'
        },
        'metadata': {
            'donation_id': donation.id,
            'custom_fields': [
                {
                    'display_name': "Purpose",
                    'variable_name': "purpose",
                    'value': "EcoBin Donation"
                }
            ]
        },
        'callback_url': 'http://localhost:5000/payment-callback'
    }
    
    try:
        response = requests.post(
            'https://api.paystack.co/transaction/initialize',
            headers=headers,
            json=payload,
            timeout=30
        )
        
        print(f"Paystack Initialize Response: {response.json()}")  # Debug
        
        if response.status_code == 200:
            data = response.json()
            if data['status']:
                donation.transaction_id = data['data']['reference']
                donation.payment_status = 'processing'
                db.session.commit()
                
                # Redirect user to Paystack payment page
                return redirect(data['data']['authorization_url'])
            else:
                flash('❌ Failed to initialize payment', 'error')
        else:
            flash(f'❌ Payment service error: {response.status_code}', 'error')
            
    except requests.exceptions.RequestException as e:
        flash(f'❌ Network error: {str(e)}', 'error')
    
    return render_template('donate.html')

@app.route('/payment-callback')
def payment_callback():
    """Handle payment callback from Paystack"""
    reference = request.args.get('reference')
    trxref = request.args.get('trxref')
    
    # Use reference or trxref
    transaction_ref = reference or trxref
    
    if transaction_ref:
        # Verify the payment
        headers = {
            'Authorization': f'Bearer {PAYSTACK_SECRET_KEY}'
        }
        
        try:
            response = requests.get(
                f'https://api.paystack.co/transaction/verify/{transaction_ref}',
                headers=headers
            )
            
            print(f"Payment Verification Response: {response.json()}")  # Debug
            
            if response.status_code == 200:
                data = response.json()
                if data['status'] and data['data']['status'] == 'success':
                    donation = Donation.query.filter_by(transaction_id=transaction_ref).first()
                    if donation:
                        donation.payment_status = 'completed'
                        db.session.commit()
                        flash('✅ Payment completed successfully! Thank you for your donation.', 'success')
                    else:
                        flash('✅ Payment verified successfully! Thank you for your support.', 'success')
                else:
                    flash('❌ Payment verification failed or payment not completed', 'error')
            else:
                flash('❌ Could not verify payment', 'error')
            
        except requests.exceptions.RequestException as e:
            flash(f'❌ Network error during verification: {str(e)}', 'error')
    
    return redirect(url_for('donate'))

@app.route('/verify-otp', methods=['POST'])
def verify_otp():
    """Verify OTP for Paystack mobile money payments"""
    otp = request.form.get('otp')
    reference = request.form.get('reference')
    donation_id = request.form.get('donation_id')
    
    if not all([otp, reference, donation_id]):
        flash('Please enter the OTP sent to your phone.', 'error')
        return redirect(url_for('donate'))
    
    headers = {
        'Authorization': f'Bearer {PAYSTACK_SECRET_KEY}',
        'Content-Type': 'application/json'
    }
    
    payload = {
        'otp': otp,
        'reference': reference
    }
    
    try:
        response = requests.post(
            'https://api.paystack.co/charge/submit_otp',
            headers=headers,
            json=payload,
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            if data.get('status') == True:
                donation = Donation.query.get(donation_id)
                if donation:
                    donation.payment_status = 'completed'
                    donation.transaction_id = reference
                    db.session.commit()
                    flash('✅ Payment completed successfully! Thank you for your donation.', 'success')
                else:
                    flash('✅ Payment verified successfully!', 'success')
            else:
                flash('❌ Invalid OTP. Please try again.', 'error')
        else:
            flash('❌ OTP verification failed.', 'error')
            
    except requests.exceptions.RequestException:
        flash('❌ Network error during OTP verification.', 'error')
    
    return redirect(url_for('donate'))

@app.route('/paystack-webhook', methods=['POST'])
def paystack_webhook():
    """Handle Paystack webhook for payment notifications"""
    try:
        # Verify it's from Paystack
        if request.headers.get('x-paystack-signature'):
            data = request.get_json()
            
            if data['event'] == 'charge.success':
                reference = data['data']['reference']
                donation = Donation.query.filter_by(transaction_id=reference).first()
                
                if donation and donation.payment_status != 'completed':
                    donation.payment_status = 'completed'
                    db.session.commit()
                    print(f"✅ Webhook: Donation {donation.id} completed via {data['data']['channel']}")
            
            return jsonify({'status': 'success'}), 200
        
    except Exception as e:
        print(f"Webhook error: {e}")
    
    return jsonify({'status': 'error'}), 400

# Debugging routes
@app.route('/debug-paystack')
def debug_paystack():
    """Debug Paystack connection"""
    headers = {
        'Authorization': f'Bearer {PAYSTACK_SECRET_KEY}'
    }
    
    try:
        response = requests.get(
            'https://api.paystack.co/transaction',
            headers=headers,
            timeout=10
        )
        
        return jsonify({
            'status': response.status_code,
            'message': 'Paystack connection successful' if response.status_code == 200 else 'Paystack connection failed',
            'response': response.json() if response.status_code == 200 else str(response.text)
        })
        
    except Exception as e:
        return jsonify({'error': str(e)})

@app.route('/test-mpesa')
def test_mpesa():
    """Test M-Pesa payment with dummy data"""
    headers = {
        'Authorization': f'Bearer {PAYSTACK_SECRET_KEY}',
        'Content-Type': 'application/json'
    }
    
    payload = {
        'email': 'test@example.com',
        'amount': 1000,  # 10 KES in kobo
        'currency': 'KES',
        'mobile_money': {
            'phone': '+254700000000',
            'provider': 'mpesa'
        }
    }
    
    try:
        response = requests.post(
            'https://api.paystack.co/charge',
            headers=headers,
            json=payload,
            timeout=30
        )
        
        return jsonify(response.json())
        
    except Exception as e:
        return jsonify({'error': str(e)})

# Admin routes for viewing data
@app.route('/admin/queries')
def admin_queries():
    queries = UserQuery.query.order_by(UserQuery.created_at.desc()).limit(50).all()
    return render_template('admin_queries.html', queries=queries)

@app.route('/admin/donations')
def admin_donations():
    donations = Donation.query.order_by(Donation.created_at.desc()).limit(50).all()
    return render_template('admin_donations.html', donations=donations)

# Test database connection
@app.route('/test-db')
def test_db():
    try:
        # Test connection
        db.engine.connect()
        
        # Get counts
        items_count = WasteItem.query.count()
        queries_count = UserQuery.query.count()
        donations_count = Donation.query.count()
        
        return f"""
        <h2>✅ Database Connection Successful!</h2>
        <p>MySQL connection established successfully.</p>
        <p>Database statistics:</p>
        <ul>
            <li>Waste Items: {items_count}</li>
            <li>User Queries: {queries_count}</li>
            <li>Donations: {donations_count}</li>
        </ul>
        """
        
    except Exception as e:
        return f"""
        <h2>❌ Database Connection Failed</h2>
        <p>Error: {str(e)}</p>
        <p>Check your MySQL configuration in .env file</p>
        """

if __name__ == '__main__':
    print("Starting EcoBin application with Paystack integration...")
    print("✅ Database initialized")
    print("🌱 Waste items populated")
    print("💳 Paystack payment integration ready")
    print(f"🔑 Test Mode: {TEST_MODE}")
    app.run(debug=True, host='0.0.0.0', port=5000)