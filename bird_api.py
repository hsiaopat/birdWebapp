from flask import Flask, request, render_template, flash, session, redirect, url_for, make_response
from flask_sqlalchemy import SQLAlchemy
from db_manager import db_session
from bird_classes import Location, Hotspot, Sighting, Bird
from flask_bootstrap import Bootstrap
from flaskext.markdown import Markdown
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from flask import Markup
import markdown
from functools import wraps

app = Flask(__name__)
app.config['SECRET_KEY'] = 'abcd'
Bootstrap(app)
Markdown(app)

hotspots = None

# def check_globals() -> None: # 8 LOC
#     global setr
#     global subs

#     # create the user object if it doesn't exist
#     if not setr:
#         setr = Hotspot()
#         db_session.add(setr)
#         db_session.commit()
#     else:
#         db_session.add(setr)
#         db_session.commit()

    # get the subreddit objects from the database and add the settings object
    # if the subreddit objects don't already exist
    #subs = db_session.query(location).all()
    #for sub in subs:
     #   sub.user = setr
     #   db_session.add(sub.settings)
   # db_session.commit()


@app.route('/')
def display_hotspots() -> str: # 6 LOC
    #check_globals()

    query = request.args.get('query', '') # get the query parameter, default to empty string if not present
    # return a template displaying all of the subreddits and links to their posts
    if query:
        loc = Location(str(query))
        db_session.add(Location(str(query)))
        db_session.commit()

        if loc:
           # try:
            sightings_links = loc.display(True)
            #except:
              #  sightings_links = []
              #  print('uh oh')
            print(loc.location)
            return render_template('hotspots.html', location = loc.location, sightings=sightings_links, query=query )
        else:
            return render_template('hotspots.html', location = '', sightings=[], query=query)
    else:
        return render_template('hotspots.html', location = '', sightings=[], query=query)


@app.template_filter('markdown')
def markdown_filter(s):
    return Markup(markdown.markdown(s))

@app.route('/<int:hotspot_id>/')
def display_sightings(hotspot_id: int) -> str: # 2 LOC

    search = request.args.get('search', '') # get the query parameter, default to empty string if not present
    # return a template displaying all of the posts and links to their comments
    sighting = db_session.query(Hotspot).filter(Hotspot.id == int(hotspot_id)).first()
    if not sighting:
        return 'Subreddit not found'
    
    
    sightings_links = sighting.display(int(hotspot_id),True)[1]
    return render_template('sightings.html',location = sighting.locName, birds=sightings_links,sighting=sighting,search=search,hotspot_id=hotspot_id)
    #except:
     #   return 'Subreddit access forbidden'


@app.route('/<int:hotspot_id>/<int:sighting_id>/')
def display_birds(hotspot_id: int, sighting_id: int) -> str: # 6 LOC
    search = request.args.get('search', '') # get the query parameter, default to empty string if not present
    # return a template displaying all of the comments
    bird = db_session.query(Sighting).filter(Sighting.id == int(sighting_id)).first()
    birds = bird.display(int(sighting_id),True)
    if not bird:
        return 'Subreddit not found'
    
    #bird = db_session.merge(bird)
    #try:
    return render_template('birds.html',birds=birds)
        #return 'Post comments access forbidden'

@app.route('/about/')
def display_about():
    return render_template('about.html')
        #return 'Post 


@app.teardown_appcontext
def shutdown_session(exception=None):
    db_session.remove()

if __name__ == '__main__':
    # run your app
    app.run()
