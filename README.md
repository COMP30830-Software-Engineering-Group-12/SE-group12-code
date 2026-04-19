# 🚀 SE - Group 12 - Dublin Bike

**SE - Group 12 - Dublin Bike** is a ✨ fantastic ✨ tool for checking bike and weather information and planning your route via bike. 🎉

---

## 📋 Table of Contents
- [✨ Features](#-features)
- [🚀 Getting Started](#-getting-started)
  - [🔧 Installation](#-installation)
  - [⚙️ Configuration](#️-configuration)
- [💻 Usage](#-usage)
- [🧬 Testing](#-testing)
- [🤝 Contributing](#-contributing)
- [📝 License](#-license)
- [📧 Contact](#-contact)

---

## ✨ Features
- **Feature 1**: Weather details via OpenWeather 🌟
- **Feature 2**: Bike stations shows on real map with bike availability information 🚀
- **Feature 3**: Login function and users can save their favourite bike stations 🔥
- **Feature 4**: Route planning and current location detection 🌟
- **Feature 5**: AI chatbot who help to plan your trip 🌟
- **Feature 6**: Machine Learning model applied for predicting bike availability for each station 🌟

---

## 🚀 Getting Started

### 🔧 Installation
To get started with **SE - Group 12 - Dublin Bike**, follow these steps:

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
   npm install  # or pip install -r requirements.txt, etc.
   ```

### ⚙️ Configuration
Currently we are using a dbinfo.py file instead of a .env file

All "hide" or "hiden" field need to be replaced with your own apikey and related information

---

## 💻 Usage
Here’s how to use **SE - Group 12 - Dublin Bike**:

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

For more advanced usage, check out the [documentation](#). 📚

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

- **Email**: jiaqi.yang1@ucdconnect.ie 📩
             caoimhe.coveneymckeown@ucdconnect.ie 📩
             casey.liew@ucdconnect.ie 📩
---

### **Key Sections Explained**

1. **Project Name with Emoticon**: Use a catchy emoticon to grab attention (e.g., 🚀 for a fast or cutting-edge project).
2. **Table of Contents**: Helps users navigate the README easily.
3. **Features**: Highlight the key features with emoticons to make them stand out.
4. **Getting Started**:
   - **Installation**: Provide clear steps to set up the project.
   - **Configuration**: Explain how to configure the project (e.g., environment variables).
5. **Usage**: Show how to use the project with examples.
6. **Testing**: Explain how to run tests.
7. **Contributing**: Encourage contributions with clear instructions.
8. **Contact**: Provide ways for users to reach out for support or feedback.

---

### **Emoticons to Use**
Here are some commonly used emoticons and their meanings:
- 🚀 **Rocket**: Fast, cutting-edge, or launch-related.
- ✨ **Sparkles**: Highlighting features or something special.
- 🔧 **Wrench**: Installation or configuration.
- ⚙️ **Gear**: Configuration or settings.
- 💻 **Computer**: Usage or running the project.
- 🧪 **Test Tube**: Testing or experiments.
- 🤝 **Handshake**: Contributing or collaboration.
- 📄 **Page**: Documentation or licenses.
- 📧 **Email**: Contact information.
- 🐦 **Bird**: Twitter or social media.
- 🐛 **Bug**: Issues or bug reports.
- ❤️ **Heart**: Love or passion for the project.

Check Emojis: [Emoji Cheatsheet](https://github.com/ikatyang/emoji-cheat-sheet)

---
