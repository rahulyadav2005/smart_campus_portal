from urllib.parse import quote_plus
from flask import (
    Flask,
    render_template,
    request,
    redirect,
    url_for,
    flash,
    session
)

from flask_sqlalchemy import SQLAlchemy

from werkzeug.security import (
    generate_password_hash,
    check_password_hash
)

from werkzeug.utils import secure_filename
import os


# ==================================================
# APP SETUP
# ==================================================

app = Flask(__name__)

UPLOAD_FOLDER = os.path.join(app.root_path, "static", "uploads")

app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)

ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gif"}

app.secret_key = "smart_campus_secret_key"


# ==================================================
# DATABASE CONNECTION
# ==================================================

from urllib.parse import quote_plus

mysql_password = quote_plus("Rahul2005@#")

app.config["SQLALCHEMY_DATABASE_URI"] = (
    f"mysql+pymysql://root:{mysql_password}@localhost/smart_campus_db"
)



app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)




def allowed_file(filename):
    return (
        "." in filename
        and filename.rsplit(".", 1)[1].lower()
        in ALLOWED_EXTENSIONS
    )




# ==================================================
# USER MODEL
# ==================================================

class User(db.Model):

    __tablename__ = "users"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    name = db.Column(
        db.String(100),
        nullable=False
    )

    email = db.Column(
        db.String(120),
        unique=True,
        nullable=False
    )

    password = db.Column(
        db.String(255),
        nullable=False
    )

    role = db.Column(
        db.String(50),
        nullable=False,
        default="student"
    )


# ==================================================
# COMPLAINT MODEL
# ==================================================

class Complaint(db.Model):

    __tablename__ = "complaints"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id"),
        nullable=False
    )

    category = db.Column(
        db.String(100),
        nullable=False
    )

    location = db.Column(
        db.String(200),
        nullable=False
    )

    description = db.Column(
        db.Text,
        nullable=False
    )

    priority = db.Column(
        db.String(20),
        default="Medium"
    )

    image = db.Column(
        db.String(255),
        nullable=True
    )

    status = db.Column(
        db.String(50),
        default="Pending"
    )

    created_at = db.Column(
        db.DateTime,
        server_default=db.func.now()
    )


# ==================================================
# HOME
# ==================================================

@app.route("/")
def home():

    return render_template("index.html")


# ==================================================
# REGISTER
# ==================================================

@app.route("/register", methods=["GET", "POST"])
def register():

    if request.method == "POST":

        name = request.form["name"]
        email = request.form["email"]
        password = request.form["password"]
        role = request.form["role"]

        # Check if email already exists
        existing_user = User.query.filter_by(
            email=email
        ).first()

        if existing_user:

            flash("Email already registered!")

            return redirect(
                url_for("register")
            )

        # Password hash
        hashed_password = generate_password_hash(
            password
        )

        # Create new user
        new_user = User(
            name=name,
            email=email,
            password=hashed_password,
            role=role
        )

        # Save in MySQL
        db.session.add(new_user)
        db.session.commit()

        flash(
            "Registration successful! Please login."
        )

        return redirect(
            url_for("login")
        )

    return render_template("register.html")


# ==================================================
# LOGIN
# ==================================================

@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        email = request.form["email"]
        password = request.form["password"]

        # Find user using email
        user = User.query.filter_by(
            email=email
        ).first()

        # Check password
        if user and check_password_hash(
            user.password,
            password
        ):

            # Save user information in session
            session["user_id"] = user.id
            session["user_role"] = user.role
            session["user_name"] = user.name

            flash("Login successful!")

            # Role based dashboard
            if user.role == "student":

                return redirect(
                    url_for("student_dashboard")
                )

            elif user.role == "staff":

                return redirect(
                    url_for("staff_dashboard")
                )

            elif user.role == "admin":

                return redirect(
                    url_for("admin_dashboard")
                )

        else:

            flash(
                "Invalid email or password!"
            )

    return render_template("login.html")


# ==================================================
# LOGOUT
# ==================================================

@app.route("/logout")
def logout():

    session.clear()

    flash("You have been logged out.")

    return redirect(
        url_for("home")
    )


# ==================================================
# STUDENT DASHBOARD
# ==================================================

@app.route("/student-dashboard")
def student_dashboard():

    if "user_id" not in session:

        flash("Please login first!")

        return redirect(
            url_for("login")
        )

    return render_template(
        "student_dashboard.html"
    )


# ==================================================
# STAFF DASHBOARD
# ==================================================

@app.route("/staff-dashboard")
def staff_dashboard():

    if "user_id" not in session:

        flash("Please login first!")

        return redirect(
            url_for("login")
        )

    return render_template(
        "staff_dashboard.html"
    )




# ==================================================
# ADMIN DASHBOARD
# ==================================================

@app.route("/admin-dashboard")
def admin_dashboard():

    # Check login
    if "user_id" not in session:
        flash("Please login first!")
        return redirect(url_for("login"))

    # Only admin can access
    if session.get("user_role") != "admin":
        flash("Access denied!")
        return redirect(url_for("home"))

    # Complaint counts
    total_complaints = Complaint.query.count()

    pending_complaints = Complaint.query.filter_by(
        status="Pending"
    ).count()

    in_progress_complaints = Complaint.query.filter_by(
        status="In Progress"
    ).count()

    resolved_complaints = Complaint.query.filter_by(
        status="Resolved"
    ).count()

    return render_template(
        "admin_dashboard.html",
        total_complaints=total_complaints,
        pending_complaints=pending_complaints,
        in_progress_complaints=in_progress_complaints,
        resolved_complaints=resolved_complaints
    )




# ==================================================
# ADMIN - VIEW ALL COMPLAINTS
# ==================================================

@app.route("/admin-complaints")
def admin_complaints():

    # Check login
    if "user_id" not in session:
        flash("Please login first!")
        return redirect(url_for("login"))

    # Only admin can access
    if session.get("user_role") != "admin":
        flash("Access denied!")
        return redirect(url_for("home"))

    # Get all complaints
    complaints = Complaint.query.order_by(
        Complaint.created_at.desc()
    ).all()

    return render_template(
        "admin_complaints.html",
        complaints=complaints
    )



# ==================================================
# ADMIN - DELETE COMPLAINT
# ==================================================

@app.route("/delete-complaint/<int:complaint_id>", methods=["POST"])
def delete_complaint(complaint_id):

    # Check login
    if "user_id" not in session:
        flash("Please login first!")
        return redirect(url_for("login"))

    # Only admin
    if session.get("user_role") != "admin":
        flash("Access denied!")
        return redirect(url_for("home"))

    # Find complaint
    complaint = Complaint.query.get_or_404(
        complaint_id
    )

    # Delete complaint
    db.session.delete(complaint)
    db.session.commit()

    flash("Complaint deleted successfully!")

    return redirect(
        url_for("admin_complaints")
    )

# ==================================================
# ADD COMPLAINT
# ==================================================

@app.route("/add-complaint", methods=["GET", "POST"])
def add_complaint():

    if "user_id" not in session:
        flash("Please login first!")
        return redirect(url_for("login"))

    if request.method == "POST":

        category = request.form["category"]
        location = request.form["location"]
        description = request.form["description"]
        priority = request.form["priority"]

        image_filename = None

        # Image upload
        if "image" in request.files:

            file = request.files["image"]

            if file and file.filename != "":

                if allowed_file(file.filename):

                    filename = secure_filename(file.filename)

                    file.save(
                        os.path.join(
                            app.config["UPLOAD_FOLDER"],
                            filename
                        )
                    )

                    image_filename = filename

                else:

                    flash(
                        "Invalid image format! Please upload PNG, JPG, JPEG or GIF."
                    )

                    return redirect(
                        url_for("add_complaint")
                    )

        # Create complaint
        new_complaint = Complaint(
            user_id=session["user_id"],
            category=category,
            location=location,
            description=description,
            priority=priority,
            image=image_filename,
            status="Pending"
        )

        db.session.add(new_complaint)
        db.session.commit()

        flash("Complaint submitted successfully!")

        return redirect(
            url_for("my_complaints")
        )

    return render_template("add_complaint.html")



# ==================================================
# MY COMPLAINTS
# ==================================================

@app.route("/my-complaints")
def my_complaints():

    # Check login
    if "user_id" not in session:

        flash("Please login first!")

        return redirect(
            url_for("login")
        )

    # Get current student's complaints
    complaints = Complaint.query.filter_by(
        user_id=session["user_id"]
    ).order_by(
        Complaint.created_at.desc()
    ).all()

    return render_template(
        "my_complaints.html",
        complaints=complaints
    )

# ==================================================
# STAFF - VIEW COMPLAINTS
# ==================================================

@app.route("/staff-complaints")
def staff_complaints():

    # Check login
    if "user_id" not in session:
        flash("Please login first!")
        return redirect(url_for("login"))

    # Only staff can access
    if session.get("user_role") != "staff":
        flash("Access denied!")
        return redirect(url_for("home"))

    # Get all complaints
    complaints = Complaint.query.order_by(
        Complaint.created_at.desc()
    ).all()

    return render_template(
        "staff_complaints.html",
        complaints=complaints
    )

# ==================================================
# STAFF - UPDATE COMPLAINT STATUS
# ==================================================

@app.route("/update-status/<int:complaint_id>", methods=["POST"])
def update_status(complaint_id):

    # Check login
    if "user_id" not in session:
        flash("Please login first!")
        return redirect(url_for("login"))

    # Only staff
    if session.get("user_role") != "staff":
        flash("Access denied!")
        return redirect(url_for("home"))

    complaint = Complaint.query.get_or_404(
        complaint_id
    )

    new_status = request.form["status"]

    complaint.status = new_status

    db.session.commit()

    flash("Complaint status updated successfully!")

    return redirect(
        url_for("staff_complaints")
    )



# ==================================================
# RUN APPLICATION
# ==================================================

if __name__ == "__main__":

    app.run(
        debug=True
    )



    