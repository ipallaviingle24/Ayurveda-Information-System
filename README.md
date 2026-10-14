# 🌿 Ayurveda Information System

A web-based application developed using Python, Flask, and SQLite to manage, organize, and retrieve information about Ayurvedic medicines, herbs, diseases, and treatments.

The system provides a centralized platform for accessing Ayurvedic information through a user-friendly interface, with search functionality and a dashboard for exploring the available data.

## ✨ Features

- 🔍 **Search & Filter:** Search and filter Ayurvedic information efficiently.
- 💊 **Medicine Information:** Access information about Ayurvedic medicines.
- 🌱 **Herb Information:** Explore details about medicinal herbs.
- 🩺 **Disease Information:** Browse information related to diseases.
- 🌿 **Treatment Information:** Retrieve information about Ayurvedic treatments.
- 📊 **Interactive Dashboard:** Visualize available data through charts and statistics.
- 🗄️ **Database Management:** Store and retrieve information using SQLite.
- 🖥️ **User-Friendly Interface:** Navigate the system through a simple web interface.

## 🛠️ Technologies Used

| Technology | Purpose |
|---|---|
| Python | Backend development |
| Flask | Web application framework |
| SQLite | Database management |
| HTML5 | Page structure |
| CSS3 | Styling and layout |
| JavaScript | Client-side interactivity |
| Bootstrap 5 | Responsive UI components |
| Chart.js | Data visualization |

## 📂 Project Structure

```text
Ayurveda-Information-System/
│
├── app.py                  # Main Flask application
├── data.py                 # Data handling
├── setup_db.py             # Database setup
├── ayurveda.db             # SQLite database
├── ayurveda_dataset.csv    # Dataset
│
├── templates/
│   ├── index.html          # Main page
│   ├── dashboard.html      # Dashboard
│   └── result.html         # Search results
│
├── static/                 # CSS, JavaScript, and assets
├── requirements.txt        # Python dependencies
└── README.md               # Project documentation
