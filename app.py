import streamlit as st
import requests
from datetime import datetime, time
from random import randint
from collections import Counter
import plotly.express as px
from plotly.subplots import make_subplots
import plotly.graph_objects as go
import hashlib
import sqlite3
from model_loading import *

from resources import choose_resources

# Login & Security

def make_hashes(password):
    return hashlib.sha256(str.encode(password)).hexdigest()


def check_hashes(password, hashed_text):
    if make_hashes(password) == hashed_text:
        return hashed_text
    return False


# DB for Passwords

conn = sqlite3.connect('data.db')
c = conn.cursor()


def create_usertable():
    c.execute('CREATE TABLE IF NOT EXISTS userstable(username TEXT UNIQUE, password TEXT)')


def add_userdata(username, password):
    c.execute('INSERT INTO userstable(username,password) VALUES (?,?)', (username, password))
    conn.commit()


def login_user(username, password):
    c.execute('SELECT * FROM userstable WHERE username = ? AND password = ?', (username, password))
    data = c.fetchall()
    return data


def view_all_users():
    c.execute('SELECT * FROM userstable')
    data = c.fetchall()
    return data



def main():
    pages = {
        "Home": page_home,
        "Journal": page_journal,
        "Previous Journals": page_previous_journals,
        "Analytics": page_analytics,
        "Resources": page_resources,
    }

    if "page" not in st.session_state:
        st.session_state.update({
            # Default page
            "page": "Home",

            # Notes already made for demo
            "notes": [
                ("When I awoke today early, I didn't want to get out of bed. I just lay there for a while  I was still thinking about last night.",
                 "sadness", datetime(2022, 1, 12)),
                ("Today, I went out with a friend and we had lot of fun and ate some good food.", "joy",
                 datetime(2022, 1, 13)),
                ("I am excited about the project that my friend and I are working on.", "joy",
                 datetime(2022, 1, 14)),
                ("Still thinking about the talk, I had last night with my friend. It was so much fun and I was finally happy after a long time.", "surprise", datetime(2022, 1, 15)),
                ("Why does my friend always get late for a meeting, still angry at her.", "anger", datetime(2022, 1, 16)),
                (
                "This morning I woke up with a horrible headache. why do I think so much", "anger", datetime(2022, 1, 17)),
                ("Finally, some progress on the project. looks like we will complete it on time.", "surprise",
                 datetime(2022, 1, 18)),
                ("WHY AM I SO STUPID. I got blank at a presentation today.", "anger", datetime(2022, 1, 19)),
                ("I cant stop thinking about that presentation.", "sadness", datetime(2022, 1, 20)),
                ("ppt still on my mind...", "sadness", datetime(2022, 1, 21)),
                ("Ordered something good to eat to take off my mind from that presentation. good food does lift up the mood.", "joy", datetime(2022, 1, 22)),
                ("Today was a beautiful day", "joy", datetime(2022, 1, 23)),
        
                ("I cant decide weather or not to message him...", "love", datetime(2022, 1, 24)),
            ],
            "placeholder_text": "..."

        })

    with st.sidebar:
        st.title("mieux me")
        if st.button("Home 🏠"): st.session_state.page = "Home"
        if st.button("Journal 📝     "): st.session_state.page = "Journal"
        if st.button("Previous Journals 📕"): st.session_state.page = "Previous Journals"
        if st.button("Analytics 📊"): st.session_state.page = "Analytics"
        if st.button("Recommendations 📚"): st.session_state.page = "Resources"

    pages[st.session_state.page]()


def page_home():
    with st.container():
        st.title("Home 🏠")
        username = st.text_input('Username')
        password = st.text_input("Password", type="password")

        if st.button('Login'):
            create_usertable()
            hashed_pswd = make_hashes(password)
            result = login_user(username, check_hashes(password, hashed_pswd))
            if result:
                st.success("Logged In as {}".format(username))
                st.session_state.page = "Journal"
                page_journal()
            else:
                st.warning("Incorrect Username/Password")

        st.write('Not a member? Sign up from the button below')

        if st.button('Sign Me Up'):
            page_signup()


def page_signup():
    with st.container():

        new_username = st.text_input('New username')
        new_password = st.text_input("New password", type="password")

        if st.button('Sign Up'):
            if new_username or new_password is None:
                st.warning("Please input a username and/or password!")
            create_usertable()
            try:
                add_userdata(new_username, make_hashes(new_password))
                st.success("You have successfully created a valid Account")
                st.session_state.page = "Journal"
                page_journal()
            except Exception as e:
                st.warning("Username already exists")


def page_journal():
    st.title("Write a note 📝 ")
    API_URL = "https://api-inference.huggingface.co/models/mrm8488/t5-base-finetuned-emotion"
    API_TOKEN = "rAplzyQGYLwcFPzUfSqVpGvRdvvXHrmfOitDsopymDDjoxtaOIEfDMeFALNMdDaNuQNIoPZfutTtqBCMlcRsDACtBUoHTsiPFsrQagnPmqyzKbJLAMBBTJTgLNpcvpOZ"
    headers = {"Authorization": f"Bearer {API_TOKEN}"}

    def mood_to_emoji(mood):
        return {'sadness': '🥺', 'joy': '😁', 'fear': '😱', 'anger': '😡', 'love': '😍', 'surprise': '😲'}[mood]

    def mood_inference(note):
        data = {"inputs": note}
        st.session_state.placeholder_text = note
        res = requests.post(API_URL, json=data, headers=headers).json()
        try:
            mood = res[0]['generated_text']
            date = datetime.now()
            st.info(f"Your mood report -- {mood} {mood_to_emoji(mood)}")
        except KeyError:
            st.warning("We're sorry! No meaningful mood analysis could be completed 😢.")
        st.session_state.notes.append((note, mood, date))
        return mood

    st.write("What's on your mind today?")
    note = st.text_area("", placeholder=st.session_state.placeholder_text, max_chars=256)
    if st.button("Click here to add the note"):
        mood = mood_inference(note)
        while not mood: time.sleep(1)

        with st.container():
            p1, p2, p3 = choose_resources(mood, 3)
            c1, c2, c3 = st.columns(3)
            with c1:
                st.header(p1.title)
                st.write(p1.description)
                st.markdown("[Learn More](%s)" % p1.url, unsafe_allow_html=True)

            with c2:
                st.header(p2.title)
                st.write(p2.description)
                st.markdown("[Learn More](%s)" % p2.url, unsafe_allow_html=True)

            with c3:
                st.header(p3.title)
                st.write(p3.description)
                st.markdown("[Learn More](%s)" % p3.url, unsafe_allow_html=True)


def page_previous_journals():
    st.title("Previous journals 📕")

    mood_box = {
        "anger": st.error,
        "fear": st.warning,
        "joy": st.success,
        "love": st.error,
        "sadness": st.info,
        "surprise": st.success,
    }

    def sample_journal(note):
        text, mood, date = note
        st.header(date.date())
        st.write(text)
        mood_box[mood](mood)

    for i in range(0, len(st.session_state.notes), 3):
        with st.container():
            col0, col1, col2 = st.columns(3)
            col_map = {0: col0, 1: col1, 2: col2}
            for j in range(i, min(i + 3, len(st.session_state.notes))):
                with col_map[j % 3]:
                    sample_journal(st.session_state.notes[j])

            st.markdown('---')


def page_analytics():
    st.title("Analytics 📊")

    counter = Counter(map(lambda x: x[1], st.session_state.get("notes", [])))
    mood_list = ["anger", "fear", "joy", "love", "sadness", "surprise"]
    mood_colors = ["red", "yellow", "green", "pink", "blue", "white"]

    mood_counts = pd.DataFrame({
        'Moods': mood_list,
        'Counts': [counter[mood] for mood in mood_list]
    })

    fig = make_subplots(rows=1, cols=2, subplot_titles=("Mood count -- bar", "Mood count -- pie"),
                        specs=[[{"type": "xy"}, {"type": "domain"}]], horizontal_spacing=0.1)
    fig.add_trace(go.Bar(x=mood_counts['Moods'], y=mood_counts['Counts']), row=1, col=1)
    fig.add_trace(go.Pie(values=mood_counts['Counts'], labels=mood_counts['Moods']), row=1, col=2)
    fig.layout.update(width=800, margin=dict(l=0))
    st.write(fig)

    earliest_date = min(map(lambda x: x[2], st.session_state.get("notes", [])))
    latest_date = max(map(lambda x: x[2], st.session_state.get("notes", [])))
    date_iterator = pd.date_range(earliest_date, latest_date, freq='W')


def page_resources():
    st.title("Resources 📚 ")
    col1, col2, col3 = st.columns(3)

    # TODO: Change based on analytics page
    mood = "anger"

    p1, p2, p3 = choose_resources(mood, 3)

    with col1:
        st.header(p1.title)
        st.write(p1.description)
        st.markdown("[Learn More](%s)" % p1.url, unsafe_allow_html=True)

    with col2:
        st.header(p2.title)
        st.write(p2.description)
        st.markdown("[Learn More](%s)" % p2.url, unsafe_allow_html=True)

    with col3:
        st.header(p3.title)
        st.write(p3.description)
        st.markdown("[Learn More](%s)" % p3.url, unsafe_allow_html=True)

    st.markdown("---")

if __name__ == "__main__":
    main()

