from flask import Flask, render_template, request, redirect, url_for, flash
from flask import request
import os
from dotenv import load_dotenv
from data import waste_data

# Load environment variables
load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', 'eco-bin-secret-key')

# IntaSend API credentials
PUBLIC_KEY = os.getenv('INTASEND_PUBLIC_KEY')
SECRET_KEY = os.getenv('INTASEND_SECRET_KEY')

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/classify', methods=['POST'])
def classify_waste():
    item = request.form.get('item', '').strip().lower()
    
    if not item:
        flash('Please enter an item to classify.', 'error')
        return redirect(url_for('index'))
    
    # Check if item exists in our database
    result = waste_data.get(item, None)
    
    if result:
        category = result['category']
        tip = result['tip']
    else:
        category = 'Unknown'
        tip = 'Please check local waste disposal guidelines or contact your waste management provider.'
    
    return render_template('result.html', item=item, category=category, tip=tip)

@app.route('/donate', methods=['GET', 'POST'])
def donate():
    if request.method == 'POST':
        email = request.form.get('email')
        phone = request.form.get('phone')
        amount = request.form.get('amount')
        
        if not all([email, phone, amount]):
            flash('Please fill all fields.', 'error')
            return render_template('donate.html')
        
        try:
            amount = float(amount)
            if amount <= 0:
                flash('Amount must be greater than 0.', 'error')
                return render_template('donate.html')
        except ValueError:
            flash('Please enter a valid amount.', 'error')
            return render_template('donate.html')
        
        # Prepare IntaSend API request
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {PUBLIC_KEY}:{SECRET_KEY}'
        }
        
        payload = {
            'public_key': PUBLIC_KEY,
            'amount': amount,
            'phone_number': phone,
            'email': email,
            'currency': 'KES',
            'api_version': '1.0.0'
        }
        
        try:
            response = requests.post(
                'https://api.intasend.com/api/v1/payment/mpesa/checkout/',
                json=payload,
                headers=headers
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get('success', False):
                    flash('Payment initiated successfully! Check your phone for M-Pesa prompt.', 'success')
                else:
                    flash('Payment failed. Please try again.', 'error')
            else:
                flash('Payment service temporarily unavailable. Please try again later.', 'error')
                
        except requests.exceptions.RequestException:
            flash('Network error. Please check your connection and try again.', 'error')
        
        return render_template('donate.html')
    
    return render_template('donate.html')

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)