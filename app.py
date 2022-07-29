#----------------------------------------------------------------------------#
# Imports
#----------------------------------------------------------------------------#

import json
import dateutil.parser
import babel
from flask import Flask, render_template, request, Response, flash, redirect, url_for
from flask_moment import Moment
from flask_sqlalchemy import SQLAlchemy
import logging
from logging import Formatter, FileHandler
from flask_wtf import Form
from forms import *
import os
import sys

from flask_migrate import Migrate
#----------------------------------------------------------------------------#
# App Config.
#----------------------------------------------------------------------------#

app = Flask(__name__)
moment = Moment(app)
app.config.from_object('config')
db = SQLAlchemy(app)

# Make Migrations

migrate = Migrate(app, db)


print(db.engine.table_names())


# TODO Implement Show and Artist models, and complete all model relationships and properties, as a database migration.

#----------------------------------------------------------------------------#
# Filters.
#----------------------------------------------------------------------------#


class Venue(db.Model):
    __tablename__ = 'Venue'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, nullable=False)
    city = db.Column(db.String(120), nullable=False)
    state = db.Column(db.String(120), nullable=False)
    address = db.Column(db.String(120), nullable=False)
    phone = db.Column(db.String(120))
    genres = db.Column(db.String, nullable=False)
    image_link = db.Column(db.String(500))
    facebook_link = db.Column(db.String(120))
    website = db.Column(db.String(120))
    seeking_talent = db.Column(db.Boolean, nullable=False, default=False)
    seeking_description = db.Column(db.String(500))
    created_at = db.Column(
        db.DateTime, default=datetime.utcnow, nullable=False)
    shows = db.relationship("Show", backref="venues",
                            lazy=False, cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Venue id={self.id} name={self.name} city={self.city} state={self.city}> \n"

    # TODO: implement any missing fields, as a database migration using Flask-Migrate


class Artist(db.Model):
    __tablename__ = 'Artist'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, nullable=False)
    city = db.Column(db.String(120), nullable=False)
    state = db.Column(db.String(120), nullable=False)
    phone = db.Column(db.String(120))
    genres = db.Column(db.String(120), nullable=False)
    image_link = db.Column(db.String(500))
    facebook_link = db.Column(db.String(120))
    website = db.Column(db.String(120))
    seeking_venue = db.Column(db.String(), nullable=False, default=False)
    seeking_description = db.Column(db.String(500))
    created_at = db.Column(
        db.DateTime, default=datetime.utcnow, nullable=False)
    shows = db.relationship("Show", backref="artists",
                            lazy=False, cascade="all, delete-orphan")


class Show(db.Model):
    __tablename__ = "Show"

    id = db.Column(db.Integer, primary_key=True)
    artist_id = db.Column(db.Integer, db.ForeignKey(
        "Artist.id"), nullable=False)
    venue_id = db.Column(db.Integer, db.ForeignKey("Venue.id"), nullable=False)
    start_time = db.Column(db.DateTime, nullable=False,
                           default=datetime.utcnow)
    venue = db.relationship('Venue') 
    artist = db.relationship('Artist')


    def __repr__(self):
        return f"<Show id={self.id} artist_id={self.artist_id} venue_id={self.venue_id} start_time={self.start_time}"


def format_datetime(value, format='medium'):
    date = dateutil.parser.parse(value)
    if format == 'full':
        format = "EEEE MMMM, d, y 'at' h:mma"
    elif format == 'medium':
        format = "EE MM, dd, y h:mma"
    return babel.dates.format_datetime(date, format, locale='en')


app.jinja_env.filters['datetime'] = format_datetime

#----------------------------------------------------------------------------#
# Controllers.
#----------------------------------------------------------------------------#


@app.route('/')
def index():
    return render_template('pages/home.html')


#  Venues
#  ----------------------------------------------------------------

@app.route('/venues')
def venues():
    # TODO: replace with real venues data.
    #       num_upcoming_shows should be aggregated based on number of upcoming shows per venue.
    data = []

    results = Venue.query.distinct(Venue.city, Venue.state).all()

    for result in results:
        location = {
            "city": result.city,
            "state": result.state
        }

        venues = Venue.query.filter_by(
            city=result.city, state=result.state).all()
        venue_data = []

        for venue in venues:
            venue_data.append(
                {
                    "id": venue.id,
                    "name": venue.name,
                    'num_upcoming_shows': len(db.session.query(Show).filter(Show.start_time > datetime.now()).all())

                }
            )

            location["venues"] = venue_data

            data.append(location)

    return render_template('pages/venues.html', areas=data)


@app.route('/venues/search', methods=['POST'])
def search_venues():
    # TODO: implement search on artists with partial string search. Ensure it is case-insensitive.
    # seach for Hop should return "The Musical Hop".
    # search for "Music" should return "The Musical Hop" and "Park Square Live Music & Coffee"

    search_term = request.form.get('search_term', '')
    db_response = db.session.query(Venue).filter(
        Venue.name.ilike(f'%{search_term}%')).all()
    data = []

    rep_count = len(db_response)

    for venue in db_response:
        data.append({
            "id": venue.id,
            "name": venue.name,
            "num_upcoming_shows": len(list(filter(lambda x: x.start_time > datetime.now(), venue.shows)))
        })

    response = {
        "count": rep_count,
        "data": data
    }

    return render_template('pages/search_venues.html', results=response, search_term=request.form.get('search_term', ''))


@app.route('/venues/<int:venue_id>')
def show_venue(venue_id):
    # shows the venue page with the given venue_id
    # TODO: replace with real venue data from the venues table, using venue_id

    # Returns object by primary key, or None
    venue = Venue.query.get(venue_id)
    print(venue)

    # convert genre string back to array
    setattr(venue, "genres", venue.genres.split(","))

    # Get a list of shows, and count the ones in the past and future
    past_shows = []
    upcoming_shows = []
    now = datetime.now()
    for show in venue.shows:
        if show.start_time > now:

            upcoming_shows.append({
                "artist_id": show.artist_id,
                "artist_name": show.artist.name,
                "artist_image_link": show.artist.image_link,
                "start_time": format_datetime(str(show.start_time))
            })

        else:
            past_shows.append({
                "artist_id": show.artist_id,
                "artist_name": show.artist.name,
                "artist_image_link": show.artist.image_link,
                "start_time": format_datetime(str(show.start_time))
            })

    data = {
        "id": venue_id,
        "name": "",
        "genres": venue.genres,
        "address": venue.address,
        "city": venue.city,
        "state": venue.state,
        "phone": venue.phone,
        "website": venue.website,
        "facebook_link": venue.facebook_link,
        "seeking_talent": venue.seeking_talent,
        "seeking_description": venue.seeking_description,
        "image_link": venue.image_link,
        "past_shows": past_shows,
        "past_shows_count": len(past_shows),
        "upcoming_shows": upcoming_shows,
        "upcoming_shows_count": len(upcoming_shows)
    }

    return render_template('pages/show_venue.html', venue=data)


#  Create Venue
#  ----------------------------------------------------------------

@app.route('/venues/create', methods=['GET'])
def create_venue_form():
    form = VenueForm()
    return render_template('forms/new_venue.html', form=form)


@app.route('/venues/create', methods=['POST'])
def create_venue_submission():
    # TODO: insert form data as a new Venue record in the db, instead
    # TODO: modify data to be the data object returned from db insertion

    form = VenueForm(request.form)

    if form.validate():
        try:
            new_venue = Venue(
                name=form.name.data,
                city=form.city.data,
                state=form.state.data,
                address=form.address.data,
                phone=form.phone.data,
                genres=",".join(form.genres.data),
                facebook_link=form.facebook_link.data,
                image_link=form.image_link.data,
                seeking_talent=form.seeking_talent.data,
                seeking_description=form.seeking_description.data,
                website=form.website_link.data
            )
            db.session.add(new_venue)
            db.session.commit()
            flash('Venue was successfully listed!')

        except Exception:
            db.session.rollback()
            print(sys.exc_info())
            flash('An error occurred. Venue could not be listed.')

        finally:
            db.session.close()
    else:
        print("\n\n", form.errors)
        flash('An error occurred. Venue could not be listed.')

    return redirect(url_for("index"))


@app.route('/delete/<venue_id>', methods=['POST'])
def delete_venue(venue_id):
    # TODO: Complete this endpoint for taking a venue_id, and using
    # SQLAlchemy ORM to delete a record. Handle cases where the session commit could fail.
    print(venue_id)
    try:
        venue = Venue.query.get(venue_id)
        db.session.delete(venue)
        db.session.commit()
        flash("Venue was deleted successfully!")

    except:
        db.session.rollback()
        print(sys.exc_info())
        flash("Venue was not deleted.")
    finally:
        db.session.close()

    return render_template('pages/home.html')

    # BONUS CHALLENGE: Implement a button to delete a Venue on a Venue Page, have it so that
    # clicking that button delete it from the db then redirect the user to the homepage


@app.route('/venues/<int:venue_id>/edit', methods=['GET'])
def edit_venue(venue_id):
    # TODO: populate form with values from venue with ID <venue_id>
    form = VenueForm()
    venue = Venue.query.get(venue_id)

    form = VenueForm(
        name=venue.name,
        genres=venue.genres,
        address=venue.address,
        city=venue.city,
        state=venue.state,
        phone=venue.phone,
        website_link=venue.website,
        facebook_link=venue.facebook_link,
        seeking_talent=venue.seeking_talent,
        seeking_description=venue.seeking_description,
        image_link=venue.image_link,)

    return render_template('forms/edit_venue.html', form=form, venue=venue)


@app.route('/venues/<int:venue_id>/edit', methods=['POST'])
def edit_venue_submission(venue_id):
    # TODO: take values from the form submitted, and update existing
    # venue record with ID <venue_id> using the new attributes
    form = VenueForm()

    if form.validate():
        try:
            venue = Venue.query.get(venue_id)
            venue.name = form.name.data
            venue.city = form.city.data
            venue.state = form.state.data
            venue.address = form.address.data
            venue.phone = form.phone.data
            venue.genres = ",".join(form.genres.data)
            venue.facebook_link = form.facebook_link.data
            venue.image_link = form.image_link.data
            venue.seeking_talent = form.seeking_talent.data
            venue.seeking_description = form.seeking_description.data
            venue.website = form.website.data
            db.session.add(venue)
            db.session.commit()

            flash("Venue  edited successfully")
        except:
            db.session.rollback()
            print(sys.exc_info())
            flash("Venue  not edited successfully.")
        finally:
            db.session.close()
    else:
        print("\n\n", form.errors)
        flash("Venue not edited successfully.")

    return redirect(url_for('show_venue', venue_id=venue_id))


#  Artists
#  ----------------------------------------------------------------
@app.route('/artists')
def artists():
    # TODO: replace with real data returned from querying the database
    data = Artist.query.all()
    return render_template('pages/artists.html', artists=data)


@app.route('/artists/search', methods=['POST'])
def search_artists():
    # TODO: implement search on artists with partial string search. Ensure it is case-insensitive.
    # seach for "A" should return "Guns N Petals", "Matt Quevado", and "The Wild Sax Band".
    # search for "band" should return "The Wild Sax Band".

    search_term = request.form.get('search_term', '')
    db_response = db.session.query(Artist).filter(
        Artist.name.ilike(f'%{search_term}%')).all()
    art_count = len(db_response)

    response = {
        "count": art_count,
        "data": db_response
    }
    return render_template('pages/search_artists.html', results=response, search_term=request.form.get('search_term', ''))


@app.route('/artists/<int:artist_id>')
def show_artist(artist_id):
    # shows the artist page with the given artist_id
    # TODO: replace with real artist data from the artist table, using artist_id

    # Returns object by primary key, or None
    artist = Artist.query.get(artist_id)
    setattr(artist, "genres", artist.genres.split(","))

    # Get past and present shows
    p_shows = list(filter(lambda show: show.start_time <
                   datetime.now(), artist.shows))
    u_shows = list(filter(lambda show: show.start_time >
                   datetime.now(), artist.shows))
                   

    # Get a list of shows, and count the ones in the past and future
    past_shows = []
    upcoming_shows = []
    for show in u_shows:

        upcoming_shows.append({
            "venue_name": show.venues.name,
            "venue_id": show.venues.id,
            "venue_image_link": show.venues.image_link,
            "start_time": format_datetime(str(show.start_time))
        })

    for show in p_shows:
        past_shows.append({
            "venue_name": show.venues.name,
            "venue_id": show.venues.id,
            "venue_image_link": show.venues.image_link,
            "start_time": format_datetime(str(show.start_time))
        })

    data = {
        "id": artist.id,
        "name": artist.name,
        "genres": artist.genres,
        "city": artist.city,
        "state": artist.state,
        "phone": artist.phone,
        "website": artist.website,
        "facebook_link": artist.facebook_link,
        "seeking_venue": artist.seeking_venue,
        "seeking_description": artist.seeking_description,
        "image_link": artist.image_link,
        "past_shows": past_shows,
        "upcoming_shows": upcoming_shows,
        "past_shows_count": len(p_shows),
        "upcoming_shows_count": len(u_shows),
    }

    return render_template('pages/show_artist.html', artist=data)

#  Update
#  ----------------------------------------------------------------


@app.route('/artists/<int:artist_id>/edit', methods=['GET'])
def edit_artist(artist_id):

    # TODO: populate form with fields from artist with ID <artist_id>
    form = ArtistForm()
    artist = Artist.query.get(artist_id)
    form = ArtistForm(
        name=artist.name,
        genres=artist.genres,
        city=artist.city,
        state=artist.state,
        phone=artist.phone,
        website_link=artist.website,
        facebook_link=artist.facebook_link,
        seeking_venue=artist.seeking_venue,
        seeking_description=artist.seeking_description,
        image_link=artist.image_link)

    return render_template('forms/edit_artist.html', form=form, artist=artist)


@app.route('/artists/<int:artist_id>/edit', methods=['POST'])
def edit_artist_submission(artist_id):
    # TODO: take values from the form submitted, and update existing
    # artist record with ID <artist_id> using the new attributes
    form = ArtistForm(request.form)

    if form.validate():
        try:
            artist = Artist.query.get(artist_id)
            artist.name = form.name.data
            artist.city = form.city.data
            artist.state = form.state.data
            artist.phone = form.phone.data
            artist.genres = ",".join(form.genres.data)
            artist.facebook_link = form.facebook_link.data
            artist.image_link = form.image_link.data
            artist.seeking_venue = form.seeking_venue.data
            artist.seeking_description = form.seeking_description.data
            artist.website = form.website_link.data
            db.session.add(artist)
            db.session.commit()
            flash("Artist " + artist.name + " successfully edited!")
        except:
            db.session.rollback()
            print(sys.exc_info())
            flash("Artist not edited successfully.")
        finally:
            db.session.close()
    else:
        print("\n\n", form.errors)
        flash("Artist  not edited successfully.")

    return redirect(url_for('show_artist', artist_id=artist_id))


#  Create Artist
#  ----------------------------------------------------------------


@app.route('/artists/create', methods=['GET'])
def create_artist_form():
    form = ArtistForm()
    return render_template('forms/new_artist.html', form=form)


@app.route('/artists/create', methods=['POST'])
def create_artist_submission():
    # called upon submitting the new artist listing form
    # TODO: insert form data as a new Venue record in the db, instead
    # TODO: modify data to be the data object returned from db insertion
    # on successful db insert, flash success
    # TODO: on unsuccessful db insert, flash an error instead.
    # e.g., flash('An error occurred. Artist ' + data.name + ' could not be listed.')
    try:
        artist = Artist(
        name=request.form['name'],
        city=request.form['city'],
        state=request.form['state'],
        phone=request.form['phone'],
        genres=request.form.getlist('genres'),
        image_link=request.form['image_link'],
        facebook_link=request.form['facebook_link'],
        website=request.form['website_link'],
        seeking_venue=request.form['seeking_venue'], 
        seeking_description=request.form['seeking_description']) 
    
        print(request.form["seeking_venue"])
        db.session.add(artist)
        db.session.commit()
    
    
        # on successful db insert, flash success
        flash('Artist ' + request.form['name'] + ' was successfully listed!')
        # TODO: on unsuccessful db insert, flash an error instead.
    except Exception as e:
        print(e)
        flash('An error occurred. Artist ' + request.form['name'] + ' could not be listed!')
        db.session.rollback()
        print(sys.exc_info())
    finally:
        db.session.close() 

    return render_template('pages/home.html')


#  Shows
#  ----------------------------------------------------------------

@app.route('/shows')
def shows():
    # displays list of shows at /shows
    # TODO: replace with real venues data.
    shows = Show.query.all()
    print(shows)
    data = []

    # Loop through shows and add data to the array


    for i in shows:
        data.append({
            "venue_id": i.venue_id,
            "venue_name": i.venue.name,
            "artist_id": i.artist_id,
            "artist_name": i.artist.name,
            "artist_image_link": i.artist.image_link,
            "start_time": str(i.start_time)
        })
    return render_template('pages/shows.html', shows=data)


@app.route('/shows/create')
def create_shows():
    # renders form. do not touch.
    form = ShowForm()
    return render_template('forms/new_show.html', form=form)


@app.route('/shows/create', methods=['POST'])
def create_show_submission():
    # called to create new shows in the db, upon submitting new show listing form
    # TODO: insert form data as a new Show record in the db, instead
    form = ShowForm(request.form)

    if(form.validate):
        try:
            show = Show(
                artist_id=form.artist_id.data,
                venue_id=form.venue_id.data,
                start_time=form.start_time.data
            )
            db.session.add(show)
            db.session.commit()
            flash('Show was successfully listed!')
        except Exception:
            db.session.rollback()
            print(sys.exc_info())
            flash('An error occurred.Show was not successfully listed.')
        finally:
            db.session.close()

    else:
        flash('Show was not successfully listed.')

    # on successful db insert, flash success
    
    # TODO: on unsuccessful db insert, flash an error instead.
    # e.g., flash('An error occurred. Show could not be listed.')
    # see: http://flask.pocoo.org/docs/1.0/patterns/flashing/
    return render_template('pages/home.html')


@app.errorhandler(404)
def not_found_error(error):
    return render_template('errors/404.html'), 404


@app.errorhandler(500)
def server_error(error):
    return render_template('errors/500.html'), 500


if not app.debug:
    file_handler = FileHandler('error.log')
    file_handler.setFormatter(
        Formatter(
            '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]')
    )
    app.logger.setLevel(logging.INFO)
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
    app.logger.info('errors')

#----------------------------------------------------------------------------#
# Launch.
#----------------------------------------------------------------------------#

# Default port:
# if __name__ == '__main__':
#     app.run()

# Or specify port manually:

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
