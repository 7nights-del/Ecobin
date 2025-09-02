👥 Contributors

1. Traicy Akinyi -akinyitraicy@gmail.com ; Git account: 7nights-del
2. Paula Aketch-aketchpaula915@gmail.com ; Git account: PPaula123
3. Brian Mwaghogho-brianmwaghogho33@gmail.com ; Git account: brianmwaghogho
4. Hafsa Hajir-hafsahajir87@gmail.com ; Git account: xafsithoo-sys
5. Samuel Mburu -mburusam885@gmail.com ; Git account: Mburu-Sam
Access our PITCH DECK https://docs.google.com/presentation/d/1FkO2cbdeeqH3tUYCTb9LEJG2_bdr0QhC/edit?slide=I'd.p13#slide=I'd.p13

# EcoBin - Smart Waste Classification System

EcoBin is a Flask-based web application that helps users classify waste items and make informed recycling decisions. The application uses AI-powered matching to identify waste categories and provides disposal tips.

## Features

- 🗂️ **Waste Classification**: Intelligent matching of waste items to categories
- 💳 **Payment Integration**: M-Pesa and card payments via IntaSend
- 📊 **Admin Dashboard**: View user queries and donation statistics
- 🗄️ **Database Integration**: MySQL database with SQLAlchemy ORM
- 🔧 **Test Mode**: Safe testing without real payments

## Quick Start

### 1. Clone and Setup

```bash
git clone <repository-url>
cd ecobin
pip install -r requirements.txt
```

### 2. Database Setup

Create a MySQL database named `ecobin_db` and configure your credentials.

### 3. Environment Configuration

Copy the example environment file:

```bash
cp .env.example .env
```

Edit `.env` with your actual configuration:

```env
# Flask Configuration
SECRET_KEY=your-secret-key-here

# MySQL Database Configuration
MYSQL_USER=your_mysql_username
MYSQL_PASSWORD=your_mysql_password
MYSQL_HOST=localhost
MYSQL_PORT=3306
MYSQL_DB=ecobin_db

# IntaSend Payment Configuration
INTASEND_PUBLIC_KEY=your_intasend_public_key_here
INTASEND_SECRET_KEY=your_intasend_secret_key_here

# Test Mode (True for testing, False for live)
TEST_MODE=True
```

### 4. IntaSend Setup

#### For Testing (Recommended)
- Set `TEST_MODE=True` in your `.env` file
- The application will use mock payments for safe testing

#### For Live Payments
1. Sign up at [IntaSend](https://intasend.com/)
2. Get your API keys from the dashboard
3. Set `TEST_MODE=False` in your `.env` file
4. Verify your account for live payments

### 5. Run the Application

```bash
python app.py
```

Visit `http://localhost:5000` to use the application.

## Configuration Status

Check your configuration at: `http://localhost:5000/config-status`

This page shows:
- ✅ Configuration validation
- 🔧 Test mode status
- 📖 Setup instructions
- 🧪 Testing links

## API Endpoints

- `/` - Home page with waste classification
- `/donate` - Donation page with payment options
- `/classify` - POST endpoint for waste classification
- `/admin/queries` - View user queries (admin)
- `/admin/donations` - View donations (admin)
- `/test-db` - Database connection test
- `/config-status` - Configuration status

## Database Models

- **WasteItem**: Waste items with categories and tips
- **UserQuery**: Logged user classification requests
- **Donation**: Payment records and status

## Payment Integration

### Test Mode
- Uses mock payments for safe testing
- No real money transactions
- Perfect for development and testing

### Test Credentials to Use:
Test Cards:

Card: 4123450131001381

CVV: 123

Expiry: 12/30

PIN: 1234 (if required)

## Troubleshooting

### Common Issues

1. **Database Connection Failed**
   - Check MySQL credentials in `.env`
   - Ensure MySQL service is running
   - Verify database exists

2. **Payment Configuration Issues**
   - Visit `/config-status` for detailed diagnostics
   - Check Paystack API keys
   - Ensure proper account verification for live mode

3. **Missing Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

## Development

### Project Structure
```
ecobin/
├── app.py              # Main Flask application
├── models.py           # Database models
├── data.py             # Waste data and mappings
├── requirements.txt    # Python dependencies
├── .env.example        # Environment template
├── templates/          # HTML templates
├── static/             # CSS and assets
└── README.md          # This file
```

### Adding New Waste Items

Edit `data.py` to add new waste classifications:

```python
waste_data = {
    "new_item": {
        "category": "Recyclable",
        "tip": "Clean before recycling",
        "synonyms": ["alternative_name"]
    }
}
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## License

This project is licensed under the MIT License.

## Support

For issues and questions:
- Check `/config-status` for configuration help
- Review the troubleshooting section
- Visit Paystack documentation for payment issues
