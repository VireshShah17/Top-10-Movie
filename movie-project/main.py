from flask import Flask, render_template, redirect, url_for, request
from flask_bootstrap import Bootstrap
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired
import requests

API_Key = 'b9f498d2eedfb6e6b08118de2c1969af'
MOVIE_DB_SEARCH_URL = "https://api.themoviedb.org/3/search/movie"
MOVIE_DB_INFO_URL = "https://api.themoviedb.org/3/movie"
MOVIE_DB_IMAGE_URL = "https://image.tmdb.org/t/p/w500"
app = Flask(__name__)
app.config['SECRET_KEY'] = '8BYkEfBA6O6donzWlSihBXox7C0sKR6b'
Bootstrap(app)

# Creating the database and the table
app.config['SQLALCHEMY_DATABASE_URI'] = "sqlite:///movies.db"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# Creating the table
with app.app_context():
    class Movie(db.Model):
        id = db.Column(db.Integer, primary_key=True)
        title = db.Column(db.String(250), nullable=False, unique=True)
        year = db.Column(db.Integer, nullable=False)
        description = db.Column(db.String(500), nullable=False)
        rating = db.Column(db.Float, nullable=True)
        ranking = db.Column(db.Integer, nullable=True)
        review = db.Column(db.String(250), nullable=True)
        img_url = db.Column(db.String(250), nullable=False)


    db.create_all()


# Creating a form to edit review and rating
class RateMovieForm(FlaskForm):
    rating = StringField("Your Rating Out of 10 e.g. 7.5")
    review = StringField("Your Review")
    submit = SubmitField("Done")


# Creating a form to add movie in our website
class AddMovieForm(FlaskForm):
    movieTitle = StringField("Movie Title", validators=[DataRequired()])
    addButton = SubmitField("Add Movie")

@app.route("/")
def home():
    all_movies = Movie.query.order_by(Movie.rating).all()
    for i in range(len(all_movies)):
        all_movies[i].ranking = len(all_movies) - i
    db.session.commit()
    return render_template("index.html", movies=all_movies)


# Updating the movie ratings and review
@app.route("/edit", methods=['GET', 'POST'])
def update_page():
    form = RateMovieForm()
    movie_id = request.args.get("id")
    movie = Movie.query.get(movie_id)
    if form.validate_on_submit():
        movie.rating = float(form.rating.data)
        movie.review = form.review.data
        db.session.commit()
        return redirect(url_for('home'))
    return render_template('edit.html', movie=movie, form=form)


# Deleting a movie
@app.route('/delete')
def delete():
    movie_id = request.args.get("id")
    with app.app_context():
        movie_to_delete = Movie.query.get(movie_id)
        db.session.delete(movie_to_delete)
        db.session.commit()
        return redirect(url_for('home'))


# Adding a movie
@app.route('/add', methods=["GET", "POST"])
def add_movies():
    form = AddMovieForm()
    if form.validate_on_submit():
        movie_title = form.movieTitle.data
        response = requests.get(MOVIE_DB_SEARCH_URL, params={"api_key": API_Key, "query": movie_title})
        data = response.json()['results']
        return render_template("select.html", options=data)
    return render_template('add.html', form=form)


@app.route("/find")
def find_movie():
    movie_api_id = request.args.get("id")
    if movie_api_id:
        movie_api_url = f"{MOVIE_DB_INFO_URL}/{movie_api_id}"
        response = requests.get(movie_api_url, params={"api_key": API_Key, "language": "en-US"})
        data = response.json()
        new_movie = Movie(
            title=data["title"],
            #The data in release_date includes month and day, we will want to get rid of.
            year=data["release_date"].split("-")[0],
            img_url=f"{MOVIE_DB_IMAGE_URL}{data['poster_path']}",
            description=data["overview"]
        )
        with app.app_context():
            db.session.add(new_movie)
            db.session.commit()
            return redirect(url_for("update_page", id=new_movie.id))


if __name__ == '__main__':
    app.run(debug=True)
