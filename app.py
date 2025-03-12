from flask import Flask, render_template, request, redirect, url_for, session
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
import os
import pandas as pd  # For reading Excel and CSV files

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('FLASK_SECRET_KEY', 'default_fallback_key')

# Default DB for users
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///default.db'

# Additional DB binds
app.config['SQLALCHEMY_BINDS'] = {
    'blood_donations': 'sqlite:///blood_donations.db',
    'blood_requests': 'sqlite:///blood_requests.db'
}
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

### MODELS ###

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)

class BloodRequest(db.Model):
    __bind_key__ = 'blood_requests'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    gender = db.Column(db.String(10), nullable=False)
    email = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(20), nullable=False)
    blood_type = db.Column(db.String(10), nullable=False)
    address = db.Column(db.Text, nullable=False)
    id_proof = db.Column(db.String(200), nullable=False)  # File path for uploaded ID proof

class BloodDonation(db.Model):
    __bind_key__ = 'blood_donations'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    gender = db.Column(db.String(10), nullable=False)
    email = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(20), nullable=False)
    blood_type = db.Column(db.String(10), nullable=False)
    age = db.Column(db.Integer, nullable=False)
    weight = db.Column(db.Integer, nullable=False)
    medical_conditions = db.Column(db.Text, nullable=True)

### ROUTES ###

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = generate_password_hash(request.form.get('password'))
        new_user = User(username=username, email=email, password=password)
        db.session.add(new_user)
        db.session.commit()
        return redirect(url_for('login'))
    return render_template('signup.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        user = User.query.filter_by(email=email).first()
        if user and check_password_hash(user.password, password):
            session['user_id'] = user.id
            return redirect(url_for('index'))
        else:
            error = "Invalid email or password"
    return render_template('login.html', error=error)

@app.route('/logout')
def logout():
    session.pop('user_id', None)
    return redirect(url_for('index'))

@app.route('/link')
def link():
    return render_template('link.html')

@app.route('/map')
def map():
    return render_template('map.html')

# Route for Receiving Blood Requests (Contact Page)
@app.route('/contact', methods=['GET', 'POST'])
def contact():
    if request.method == 'POST':
        # Get form data from the contact form
        name = request.form.get('fname')
        gender = request.form.get('gender')
        email = request.form.get('femail')
        phone = request.form.get('fphone')
        blood_type = request.form.get('ftype')
        address = request.form.get('fdetails')
        
        # Handle file upload for ID proof
        upload_folder = os.path.join(app.root_path, 'uploads')
        os.makedirs(upload_folder, exist_ok=True)
        
        file = request.files.get('id_proof')
        file_path = os.path.join('uploads', file.filename) if file else ''
        if file:
            file.save(os.path.join(app.root_path, file_path))
        
        # Save recipient request into the database
        new_request = BloodRequest(
            name=name,
            gender=gender,
            email=email,
            phone=phone,
            blood_type=blood_type,
            address=address,
            id_proof=file_path
        )
        db.session.add(new_request)
        db.session.commit()
        
        # Define blood type compatibility mapping
        compatibility = {
            "A+": ["A+", "A-", "O+", "O-"],
            "A-": ["A-", "O-"],
            "B+": ["B+", "B-", "O+", "O-"],
            "B-": ["B-", "O-"],
            "A1B+": ["AB+"],
            "AB+": ["A+", "A-", "B+", "B-", "AB+", "AB-", "O+", "O-"],
            "AB-": ["A-", "B-", "AB-", "O-"],
            "O+": ["O+", "O-"],
            "O-": ["O-"]
        }
        donor_types = compatibility.get(blood_type.upper(), [])
        
        # Read donors.xlsx from the "donor" folder
        donors_file = os.path.join(app.root_path, 'donor', 'donors.xlsx')
        
        try:
            if not os.path.exists(donors_file):
                raise FileNotFoundError(f"File not found: {donors_file}")
            
            df = pd.read_excel(donors_file)
            
            # Standardize column names to lowercase
            df.columns = df.columns.str.strip().str.lower()
            
            # Check for required columns (all in lowercase)
            required_cols = {"blood group", "name", "phone number"}
            if not required_cols.issubset(set(df.columns)):
                missing = required_cols - set(df.columns)
                raise KeyError(f"Missing required columns in donors.xlsx: {missing}")
            
            # Filter donors whose blood group (converted to uppercase) is in the compatible list
            matching_donors_df = df[df['blood group'].str.upper().isin(donor_types)]
            
            # Convert to list of dictionaries for rendering
            matching_donors = matching_donors_df[['name', 'phone number', 'blood group']].to_dict(orient='records')
        except Exception as e:
            print(f"Error reading donors file: {e}")
            matching_donors = []
        
        # Render matching donors page with the results
        return render_template("matching.html", donors=matching_donors, recipient=blood_type.upper())
    
    return render_template('contact.html')

# Route for Donating Blood (Donate Page) with Location Tracking
@app.route('/donate', methods=['GET', 'POST'])
def donate():
    if request.method == 'POST':
        name = request.form.get('fname')
        gender = request.form.get('gender')
        age = request.form.get('fage')
        weight = request.form.get('fweight')
        email = request.form.get('femail')
        phone = request.form.get('fphone')
        blood_type = request.form.get('ftype')
        medical_conditions = request.form.get('fdetails')
        
        # Save donation record
        new_donation = BloodDonation(
            name=name,
            gender=gender,
            email=email,
            phone=phone,
            blood_type=blood_type,
            age=int(age),
            weight=int(weight),
            medical_conditions=medical_conditions
        )
        db.session.add(new_donation)
        db.session.commit()
        
        # After donation, load donor tracking dataset (CSV file)
        tracking_file = os.path.join(app.root_path, 'donor', 'donor_tracking.csv')
        try:
            if not os.path.exists(tracking_file):
                raise FileNotFoundError(f"Tracking file not found: {tracking_file}")
            
            df = pd.read_csv(tracking_file)
            df.columns = df.columns.str.strip().str.lower()
            # Filter donors whose blood group matches (case-insensitive)
            matching_df = df[df['blood_group'].str.upper() == blood_type.upper()]
            
            if not matching_df.empty:
                donor_info = matching_df.iloc[0]  # choose the first matching donor
                donor_lat = donor_info['latitude']
                donor_lng = donor_info['longitude']
                donor_name = donor_info['name']
            else:
                donor_lat = None
                donor_lng = None
                donor_name = None
        except Exception as e:
            print(f"Error reading donor tracking file: {e}")
            donor_lat = None
            donor_lng = None
            donor_name = None

        if donor_lat and donor_lng:
            # Render the tracking page with the donor's location data
            return render_template('tracking.html', donor_lat=donor_lat, donor_lng=donor_lng, donor_name=donor_name)
        else:
            # If no matching donor is found, you may choose to redirect or show a message.
            return redirect(url_for('index'))
    
    return render_template('donate.html')

@app.route('/blood_donations')
def view_donations():
    donations = BloodDonation.query.all()
    return render_template('blood_donations.html', donations=donations)

@app.route('/blood_requests')
def view_requests():
    requests_rec = BloodRequest.query.all()
    return render_template('blood_requests.html', requests=requests_rec)

if __name__ == '__main__':
    # Create tables in all binds plus the default database
    with app.app_context():
        db.create_all()
    app.run(debug=True)
