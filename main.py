from flask import Flask, render_template, redirect, url_for, request
from flask_bootstrap import Bootstrap
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import FlaskForm
from wtforms import StringField, FloatField, SubmitField
from wtforms.validators import DataRequired
import requests
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = '8BYkEfBA6O6donzWlSihBXox7C0sKR6b'
Bootstrap(app)

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///movies.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)


class Movie(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(250), unique=True, nullable=False)
    year = db.Column(db.Integer, nullable=False)
    description = db.Column(db.String(500), nullable=False)
    rating = db.Column(db.Float, nullable=True)
    ranking = db.Column(db.Integer, nullable=True)
    review = db.Column(db.String, nullable=True)
    img_url = db.Column(db.String, nullable=False)


if not os.path.isfile('sqlite:///movies.db'):
    db.create_all()


class MovieEditForm(FlaskForm):
    rating = FloatField('Your Rating out of 10 e.g. 7.5', validators=[DataRequired()])
    review = StringField('Your Review', validators=[DataRequired()])
    submit = SubmitField('Submit')


class MovieAdd(FlaskForm):
    title = StringField('Movie Title', validators=[DataRequired()])
    add = SubmitField('Add Movie')


URL_API_SEARCH = 'https://api.themoviedb.org/3/search/movie'
API_KEY = '637257a4e33eb7da30b86ba5b11724bc'


@app.route("/")
def home():
    movies = db.session.query(Movie).all()
    ranking = []
    for element in movies:
        ranking.append(element.rating)
        print(element.rating)
    ranking = sorted(ranking, key=float, reverse=True)
    for pos, item in enumerate(ranking):
        print(pos)
        print(item)
        movie_to_rank = Movie.query.filter_by(rating=item).first()
        movie_to_rank.ranking = pos + 1
        db.session.commit()
    print(ranking)
    return render_template('index.html', movies=db.session.query(Movie).order_by('rating').all())


@app.route('/edit<int:movie_id>', methods=['GET', 'POST'])
def edit(movie_id):
    form = MovieEditForm()
    if form.validate_on_submit():
        new_rating = form.data['rating']
        new_review = form.data['review']
        movie_to_update = Movie.query.filter_by(id=movie_id).first()
        movie_to_update.rating = new_rating
        movie_to_update.review = new_review
        db.session.commit()
        return redirect(url_for('home'))
    return render_template('edit.html', movie=Movie.query.filter_by(id=movie_id).first(), form=form)


@app.route('/delete<int:movie_id>')
def delete(movie_id):
    movie_to_delete = Movie.query.get(movie_id)
    db.session.delete(movie_to_delete)
    db.session.commit()
    return redirect(url_for('home'))


@app.route('/add', methods=['GET', 'POST'])
def add():
    form = MovieAdd()
    if form.validate_on_submit():
        new_movie_title = form.data['title']
        params = {
            'api_key': API_KEY,
            'query': new_movie_title,
        }
        data = requests.get(URL_API_SEARCH, params=params)
        return render_template('select.html', data=data.json())
    return render_template('add.html', form=form)


@app.route('/select<int:movie_id>', methods=['GET', 'POST'])
def select(movie_id):
    data = requests.get(f'https://api.themoviedb.org/3/movie/{movie_id}?api_key={API_KEY}&language=en-US')
    data = data.json()
    title = data['original_title']
    new_movie = Movie(
        title=data['original_title'],
        year=data['release_date'][:4],
        description=data['overview'],
        img_url=f"https://image.tmdb.org/t/p/w500/{data['poster_path']}"
        )
    db.session.add(new_movie)
    db.session.commit()
    print(title)
    movie_to_update = Movie.query.filter_by(title=title).first()
    movie_to_update = movie_to_update.id
    print(movie_to_update)
    return redirect(url_for('edit', movie_id=movie_to_update))


if __name__ == '__main__':
    app.run(debug=True)
