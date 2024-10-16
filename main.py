from flask import Flask, render_template, redirect, url_for, flash, request
from forms import RegisterForm
from flask_sqlalchemy import SQLAlchemy 
from sqlalchemy.orm import relationship, mapped_column, Mapped
from sqlalchemy import Integer, String, Text, DateTime
from datetime import datetime
import datetime 
from flask_login import UserMixin, login_user, current_user, LoginManager, logout_user
from werkzeug.security import check_password_hash, generate_password_hash
import os
from werkzeug.utils import secure_filename

app =  Flask(__name__)



app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///news.db'

app.config['SECRET_KEY'] = 'Brahim@1982Xyza'


# Configure the folder where images will be saved
UPLOAD_FOLDER = os.path.join(app.root_path, 'static/uploads')
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # Maximum file size (16 MB)

# Set allowed extensions for the uploaded files
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS



db = SQLAlchemy()
db.init_app(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


class News(db.Model):
    __tablename__ = "News"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    title: Mapped[str] = mapped_column(String(250), unique=True, nullable=False)
    date: Mapped[DateTime] = mapped_column(DateTime, default=datetime.datetime.now(), nullable=False)
    article: Mapped[str] = mapped_column(Text, nullable=False)
    img_url: Mapped[str] = mapped_column(String(250), nullable=False)


class User(UserMixin, db.Model):
    __tablename__ = "Users"
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(100), nullable=False)
    # Parent relationship: "comment_author" refers to the comment_author property in the Comment class.
    # comments = relationship("Comment", back_populates="comment_author")


with app.app_context():
    db.create_all()



@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegisterForm()
    if form.validate_on_submit():
        # Check if email already exists
        existing_user = User.query.filter_by(email=form.email.data).first()
        if existing_user:
            flash("You've already signed up with that email, log in instead!", "warning")
            return redirect(url_for('login'))

        # Hash the password and create a new user
        hashed_password = generate_password_hash(form.password.data, method='pbkdf2:sha256', salt_length=8)
        new_user = User(
            username=form.username.data,
            email=form.email.data,
            password=hashed_password
        )

        try:
            db.session.add(new_user)
            db.session.commit()
            flash("You've been successfully registered. Please log in.", "success")
            return redirect(url_for('home'))
        except Exception as e:
            flash("An error occurred while creating your account. Please try again.", "danger")
            db.session.rollback()  # Roll back the session on error

    return render_template('register.html', form=form)



@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "GET":
        return render_template('login.html')
    
    if current_user.is_authenticated:
        return redirect(url_for('home'))

    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")
        
        # Query the user by email (you'll need a User model for this)
        user = User.query.filter_by(email=email).first()

        if user and check_password_hash(user.password, password):
            login_user(user)
            flash("تم تسجيل الدخول بنجاح", "success")
            return redirect(url_for('home'))
        else:
            flash("فشل تسجيل الدخول. تأكد من البريد الإلكتروني أو كلمة المرور", "danger")

    return render_template("login.html")



@app.route('/')
def home():
    all_news = News.query.all()
    # result = db.session.execute(db.select(News))
    # all_news = result.scalars().all()
    return render_template('home.html',all_news=all_news) 





# @app.route('/show_news')
# def show_news():
#     # Fetch all news from the News table
#     all_news = News.query.all()
    
#     # Render the 'show_news.html' template and pass the news data
#     return render_template('show_news.html', all_news=all_news)


@app.route('/add_new', methods=['GET', 'POST'])
def add_new():
    if request.method == 'POST':
        # Get form data
        title = request.form.get('title')
        article = request.form.get('article')
        file = request.files.get('file')  # File input
        
        # Check if all fields are filled
        if not title or not article or not file:
            flash('All fields are required!', 'danger')
            return redirect(url_for('add_new'))
        
        # Check if the file has a valid extension
        if file and allowed_file(file.filename):
            # Secure the filename and save the file
            filename = secure_filename(file.filename)
            file_path = os.path.join('static', 'uploads', filename) 
            # Save the file to the uploads folder
            file.save(os.path.join(app.root_path, file_path))
            
            img_url = os.path.join('/uploads', filename)

            # Normalize the path to avoid issues with backslashes
            img_url = os.path.normpath(img_url).replace('\\', '/')
            print(img_url)
        

            # Add new news to the database
            new_news = News(
                title=title,
                article=article,
                img_url=img_url,
                date=datetime.datetime.now()
            )
            db.session.add(new_news)
            db.session.commit()

            flash('News added successfully!', 'success')

            return redirect(url_for('home'))  # Redirect to the list of news after submission
        else:
            flash('Invalid image file!', 'danger')
            return redirect(url_for('add_new'))
    

    return render_template('add_new.html')




@app.route('/news/<int:news_id>')
def read_news(news_id):
    # Fetch the specific news article by ID
    news = News.query.get_or_404(news_id)
    
    # Render a template to display the news article
    # No changes needed here, unless you want to process something before rendering
    return render_template('read_news.html', news=news)


@app.route('/edit_news/<int:news_id>', methods=['GET', 'POST'])
def edit_news(news_id):
    # Fetch the news article by ID
    news = News.query.get_or_404(news_id)
    
    if request.method == 'POST':
        # Update news data based on form input
        news.title = request.form['title']
        news.article = request.form['article']
        news.img_url = request.form['img_url']
        
        db.session.commit()  # Save the changes to the database
        
        flash('News updated successfully!', 'success')
        return redirect(url_for('home'))  # Redirect to the homepage
    
    # Render the edit form with current news data
    return render_template('edit_news.html', news=news)


@app.route("/delete_news/<int:news_id>", methods=["POST"])
def delete_news(news_id):
    news_item = News.query.get_or_404(news_id)  # Get the news by ID, 404 if not found
    try:
        db.session.delete(news_item)
        db.session.commit()
        flash("خبر تم حذفه بنجاح", "success")  # Flash message for successful deletion
    except Exception as e:
        db.session.rollback()  # Rollback in case of error
        flash("حدث خطأ أثناء حذف الخبر", "danger")
    return redirect(url_for('home')) 

@app.route('/logout')
#@login_required   Ensure the user is logged in before allowing logout
def logout():
    if current_user.is_authenticated:
        logout_user()
        flash('تم تسجيل الخروج بنجاح', 'success')
    else:
        flash('أنت بالفعل خارج النظام', 'warning')
    return redirect(url_for('home'))




if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
