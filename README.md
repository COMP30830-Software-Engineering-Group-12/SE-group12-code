# 🚴‍♂️ Dublin Bikes Smart Planner (SE Group 12)

A full-stack web application for exploring Dublin Bike stations, checking real-time availability, and planning optimal cycling routes with integrated weather insights and machine learning predictions.

🌐 **Live Demo**: https://www.segroup12.me  

🔒 **HTTPS Enabled (SSL Secured)**

---

## 📋 Table of Contents
- [📌 Overview](#-overview)
- [✨ Key Features](#-key-features)
- [🚀 Getting Started](#-getting-started)
  - [🔧 Installation](#-installation)
  - [⚙️ Configuration](#️-configuration)
- [💻 Usage](#-usage)
- [🧬 Testing](#-testing)
- [📁 Project Structure](#-project-structure)
- [🧠 Machine Learning Model](#-machine-learning-model)
- [🤝 Contributing](#-contributing)
- [📧 Contact](#-contact)
- [⭐ Highlights](#-highlights)
- [📜 License](#-license)

---

## 📌 Overview

This project integrates real-time bike data, weather intelligence, and machine learning to help users make better decisions when using Dublin Bikes.

It demonstrates a complete end-to-end system including:

- Backend API design  
- Data pipelines  
- Machine learning integration  
- Frontend UI/UX  
- Cloud deployment  

---

## ✨ Key Features

### 🚲 Bike Availability
- Real-time Dublin Bike station data
- Interactive Google Maps integration
- Live bike and stand availability

### 🌦 Weather Integration
- Current, hourly, and 7-day forecast (OpenWeather API)
- Weather-aware cycling insights

### 🧭 Route Planning
- Multi-step route planning:
  - Walk → Bike → Walk
- Travel time estimation
- Current location detection

### 🤖 AI Chatbot
- Natural language route planning assistant
- Helps users plan journeys interactively

### 📊 Machine Learning Prediction
- Predicts future bike availability
- Random Forest model using weather and time features

### ⭐ User System
- Login / Signup
- Google Login
- Save favourite bike stations

### 🌐 Production Deployment
- Hosted on real domain  
- Nginx + Gunicorn deployment  
- Background data collection jobs  
- SSL certificate enabled  

---

## 🚀 Getting Started

### 🔧 Installation
To get started with **Dublin Bikes Smart Planner (SE Group 12)**, follow these steps:

1. Clone the repository:
   ```bash
   git clone https://github.com/COMP30830-Software-Engineering-Group-12/SE-group12-code.git
   ```

2. Navigate to the project directory:
   ```bash
   cd SE-group12-code/server_applied_code
   ```

3. Install the dependencies:
   ```bash
   conda env create -f environment.yml
   ```

### ⚙️ Configuration
Currently we are using a dbinfo.py file instead of a .env file

All "hide" or "hiden" field need to be replaced with your own apikey and related information

---

## 💻 Usage
Here’s how to use **SE - Group 12 - Dublin Bike**:
0. Active environment
   ```bash
   conda activate comp30830
   ```

1. Run the project: (Make sure you have mysql installed in your server)
   ```bash
   python one_time_run.py
   nohup python long_run_bike_data.py > bike.log 2>&1 &
   nohup python long_run_weather_data.py > weather.log 2>&1 &
   nohup python app_flask.py > flask.log 2>&1 &
   ```

2. Install gunicorn and nginx.
   
3. configure your domain and activate your setting.

4. Start gunicorn service.
   ```bash
   nohup /home/ubuntu/miniconda3/envs/comp30830/bin/gunicorn -w 2 -b 127.0.0.1:8000 app_flask:app > gunicorn.log 2>&1 &
   ```
   (For saving server's memory usage, we only use 2 workers)

For more advanced usage, check out the [documentation](https://nginx.org/en/docs/beginners_guide.html). 📚

---

## 🧬 Testing
To run the tests, use the following command:

```bash
cat flask.log
curl http://127.0.0.1:8000
tail -n 50 gunicorn.log
sudo systemctl status nginx
```

---

## 📁 Project Structure
server_applied_code/     
│     
├── component_py_file/     
│   ├── db_request.py     
│   ├── prediction.py     
│   ├── data_scraping.py     
│     
├── templates/     
├── static/     
│     
├── app_flask.py     
├── one_time_run.py     
├── long_run_bike_data.py     
├── long_run_weather_data.py     

---

## 🧠 Machine Learning Model
* Model: Random Forest
* Target: Bike availability
* Features:
    * Station ID
    * Temperature
    * Humidity
    * Wind speed
    * Weather condition
    * Hour of day
    * Day of week

## 🤝 Contributing
We welcome contributions! 🎉 If you'd like to contribute, please follow these steps:

1. Fork the repository.

2. Create a new branch:
   ```bash
   git checkout -b feature/your-feature-name
   ```

3. Commit your changes:
   ```bash
   git commit -m "Add your awesome feature"
   ```

4. Push to the branch:
   ```bash
   git push origin feature/your-feature-name
   ```

5. Open a pull request. 🚀

---

## 📧 Contact
If you have any questions or feedback, feel free to reach out:

- **Email**:   
  jiaqi.yang1@ucdconnect.ie 📩   
  caoimhe.coveneymckeown@ucdconnect.ie 📩   
  casey.liew@ucdconnect.ie 📩   
---

## ⭐ Highlights
* Full-stack production deployment
* Real-time + predictive data system
* Machine learning integrated into web app
* Cloud-based architecture
---

## 📜 License
This project was developed as part of the COMP30830 Software Engineering module.

---
