from flask import Flask, render_template, request, redirect, url_for, session,flash 
from flask_sqlalchemy import SQLAlchemy 
from werkzeug.security import generate_password_hash,check_password_hash
from pet_data import PET_CONTENT_DATA

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-super-secret-key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///site.db'
db = SQLAlchemy(app)

# Dictionary to map pet types to background image URLs
BACKGROUND_IMAGES = {
    'lizard': 'https://example.com/images/lizard-bg.jpg',
    'dog': 'https://example.com/images/dog-bg.jpg',
    'cat': 'https://example.com/images/cat-bg.jpg',
    'bird': 'https://example.com/images/bird-bg.jpg',
    'default': 'https://example.com/images/default-bg.jpg'
}


# --- Database Models ---
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128))
    is_admin = db.Column(db.Boolean, default=False)

    def _repr_(self):
        return f'<User {self.username}>'

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


class Pet(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    pet_name = db.Column(db.String(50), nullable=True)
    pet_type = db.Column(db.String(50), nullable=False)
    breed = db.Column(db.String(50), nullable=False)
    gender = db.Column(db.String(10), nullable=False)
    age = db.Column(db.Integer, nullable=False)
    medical_history = db.Column(db.String(255), nullable=True)
    owner_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

    def _repr_(self):
        return f'<Pet {self.pet_type} - {self.breed}>'


# --- Routes ---
@app.route('/')
def home():
    return render_template('home.html')

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/contact')
def contact():
    return render_template('contact.html')

@app.route('/getstarted')
def getstarted():
    return render_template('getstarted.html')


# --- LOGIN ---
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user = User.query.filter_by(username=username).first()

        if user and user.check_password(password):
            session['user_id'] = user.id
            session['username'] = user.username
            flash('Logged in successfully!', 'success')
            pet = Pet.query.filter_by(owner_id=user.id).first()
            if pet:
                return redirect(url_for('mainhome'))
            else:
                return redirect(url_for('dashboard'))
        else:
            flash('Login failed. Check your username and password.', 'danger')
            return redirect(url_for('login'))
    return render_template('login.html')


# --- SIGNUP ---
@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')

        if not (username and email and password and confirm_password):
            flash('All fields are required.', 'danger')
            return redirect(url_for('signup'))
        if password != confirm_password:
            flash('Passwords do not match.', 'danger')
            return redirect(url_for('signup'))
        if User.query.filter_by(username=username).first():
            flash('Username already exists.', 'danger')
            return redirect(url_for('signup'))
        if User.query.filter_by(email=email).first():
            flash('Email already exists.', 'danger')
            return redirect(url_for('signup'))

        new_user = User(username=username, email=email)
        new_user.set_password(password)
        db.session.add(new_user)
        db.session.commit()

        session['user_id'] = new_user.id
        session['username'] = new_user.username
        flash('Account created successfully! Please add your pet details.', 'success')
        return redirect(url_for('dashboard'))
    return render_template('signup.html')


# --- DASHBOARD ---
@app.route('/dashboard', methods=['GET', 'POST'])
def dashboard():
    if 'user_id' not in session:
        flash('Please login to access the dashboard.', 'warning')
        return redirect(url_for('login'))

    username = session.get('username', 'Guest')

    if request.method == 'POST':
        pet_name = request.form.get('pet_name')
        pet_type = request.form.get('pet_type')
        breed = request.form.get('breed')
        gender = request.form.get('gender')
        age = request.form.get('age')
        medical_history = request.form.get('medical_history')

        if not (pet_type and breed and gender and age):
            flash("Please fill in all required fields.", "danger")
            return redirect(url_for('dashboard'))

        existing_pet = Pet.query.filter_by(owner_id=session['user_id']).first()
        if existing_pet:
            existing_pet.pet_name = pet_name
            existing_pet.pet_type = pet_type
            existing_pet.breed = breed
            existing_pet.gender = gender
            existing_pet.age = int(age)
            existing_pet.medical_history = medical_history
            flash("Pet details updated successfully!", "success")
        else:
            new_pet = Pet(
                pet_name=pet_name,
                pet_type=pet_type,
                breed=breed,
                gender=gender,
                age=int(age),
                medical_history=medical_history if medical_history else None,
                owner_id=session['user_id']
            )
            db.session.add(new_pet)
            flash("Pet details saved successfully!", "success")
        
        db.session.commit()
        return redirect(url_for('mainhome'))

    pets = Pet.query.filter_by(owner_id=session['user_id']).all()
    return render_template("dashboard.html", username=username, pets=pets)


# --- MAINHOME ---
@app.route('/mainhome')
def mainhome():
    if 'user_id' not in session:
        flash("Please login first.", "warning")
        return redirect(url_for('login'))
    
    username = session.get('username', 'Guest')
    pet = Pet.query.filter_by(owner_id=session['user_id']).first()
    
    background_url = BACKGROUND_IMAGES.get(pet.pet_type.lower() if pet else 'default')
    
    return render_template("mainhome.html", username=username, pet=pet, background_url=background_url)


# --- Module Routes (Now Correctly Mapped to your HTML files) ---
# --- Module Routes (Now Correctly Mapped to your HTML files) ---
@app.route('/care_tips/<pet_type>/<breed>')
def caretips(pet_type, breed):
    if 'user_id' not in session:
        flash("Please login to view care tips.", "warning")
        return redirect(url_for('login'))
    
    pet_type_lower = pet_type.lower()
    breed_key = f"{pet_type_lower}_{breed.lower()}"
    
    # Correctly access the 'caretips' data
    content_data = PET_CONTENT_DATA.get(pet_type_lower, {}).get(breed_key, {})
    caretips_content = content_data.get('caretips', {})
    
    return render_template('caretips.html', pet_type=pet_type, breed=breed, content=caretips_content)


@app.route('/feeding/<pet_type>/<breed>')
def feeding(pet_type, breed):
    if 'user_id' not in session:
        flash("Please login to view the feeding guide.", "warning")
        return redirect(url_for('login'))
    
    pet_type_lower = pet_type.lower()
    breed_key = f"{pet_type_lower}_{breed.lower()}"
    
    # Correctly access the 'feeding' data
    content_data = PET_CONTENT_DATA.get(pet_type_lower, {}).get(breed_key, {})
    feeding_content = content_data.get('feeding', {})
    
    return render_template('feeding.html', pet_type=pet_type, breed=breed, content=feeding_content)


@app.route('/health/<pet_type>/<breed>')
def health(pet_type, breed):
    if 'user_id' not in session:
        flash("Please login to view health and wellness information.", "warning")
        return redirect(url_for('login'))
    
    pet_type_lower = pet_type.lower()
    breed_key = f"{pet_type_lower}_{breed.lower()}"

    # Correctly access the 'health' data
    content_data = PET_CONTENT_DATA.get(pet_type_lower, {}).get(breed_key, {})
    health_content = content_data.get('health', {})
    
    return render_template('health.html', pet_type=pet_type, breed=breed, content=health_content)


@app.route('/training/<pet_type>/<breed>')
def training(pet_type, breed):
    if 'user_id' not in session:
        flash("Please login to view training activities.", "warning")
        return redirect(url_for('login'))
    
    pet_type_lower = pet_type.lower()
    breed_key = f"{pet_type_lower}_{breed.lower()}"

    # Correctly access the 'training' data
    content_data = PET_CONTENT_DATA.get(pet_type_lower, {}).get(breed_key, {})
    training_content = content_data.get('training', {})
    
    return render_template('training.html', pet_type=pet_type, breed=breed, content=training_content)

# --- LOGOUT ---
@app.route('/logout')
def logout():
    session.pop('user_id', None)
    session.pop('username', None)
    flash('You have been logged out.', 'info')
    return redirect(url_for('home'))


# --- Main Entry ---
if __name__ == '_main_':
    with app.app_context():
        db.create_all()
    app.run(debug=True)