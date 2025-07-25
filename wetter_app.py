import tkinter as tk
from tkinter import messagebox
import requests
from PIL import Image, ImageTk
import io
from datetime import datetime
import webbrowser
import smtplib
from email.message import EmailMessage
import os

API_KEY = "e4d5b8a650090326ee3fddcc3b106b3e"

use_celsius = True
weather_data = None
weather_icon = None

def fetch_weather_data():
    global weather_data, weather_icon

    city = city_entry.get()
    if not city:
        messagebox.showwarning("Input Error", "Please enter a city name.")
        return

    try:
        current_url = f"http://api.openweathermap.org/data/2.5/weather?q={city}&appid={API_KEY}&units=metric"
        current_res = requests.get(current_url).json()

        if current_res["cod"] != 200:
            messagebox.showerror("Error", f"City not found: {city}")
            return

        name = current_res["name"]
        temp = current_res["main"]["temp"]
        humidity = current_res["main"]["humidity"]
        desc = current_res["weather"][0]["description"]
        icon = current_res["weather"][0]["icon"]
        coord = current_res["coord"]
        timezone_offset = current_res["timezone"]
        wind_speed = current_res["wind"]["speed"]
        pressure = current_res["main"]["pressure"]
        sunrise = current_res["sys"]["sunrise"]
        sunset = current_res["sys"]["sunset"]

        forecast_url = f"http://api.openweathermap.org/data/2.5/forecast?q={city}&appid={API_KEY}&units=metric"
        forecast_res = requests.get(forecast_url).json()

        weather_data = {
            "city": name,
            "temp_c": temp,
            "humidity": humidity,
            "desc": desc,
            "icon": icon,
            "coord": coord,
            "forecast": forecast_res["list"],
            "timezone": timezone_offset,
            "wind_speed": wind_speed,
            "pressure": pressure,
            "sunrise": sunrise,
            "sunset": sunset
        }

        display_weather_results()

        icon_url = f"http://openweathermap.org/img/wn/{icon}@2x.png"
        icon_data = requests.get(icon_url).content
        image = Image.open(io.BytesIO(icon_data)).resize((70, 70))
        weather_icon = ImageTk.PhotoImage(image)
        icon_label.config(image=weather_icon)

    except Exception as e:
        messagebox.showerror("Error", str(e))

def display_weather_results():
    global use_celsius
    result_text.config(state='normal')
    result_text.delete("1.0", tk.END)

    if not weather_data:
        result_text.config(state='disabled')
        return

    temp = weather_data["temp_c"]
    unit = "°C"
    if not use_celsius:
        temp = (temp * 9/5) + 32
        unit = "°F"

    utc_now = datetime.utcnow()
    local_timestamp = utc_now.timestamp() + weather_data["timezone"]
    local_time_str = datetime.fromtimestamp(local_timestamp).strftime("%Y-%m-%d %H:%M")

    output = f"📍 {weather_data['city']}\n"
    output += f"🕒 Local Time: {local_time_str}\n\n"
    output += f"🌡️  Temp: {temp:.2f}{unit}\n"
    output += f"💧  Humidity: {weather_data['humidity']}%\n"
    output += f"☁️  Condition: {weather_data['desc']}\n"
    output += f"🌬️  Wind Speed: {weather_data['wind_speed']} m/s\n"
    output += f"📊  Pressure: {weather_data['pressure']} hPa\n"

    sunrise = datetime.fromtimestamp(weather_data["sunrise"] + weather_data["timezone"]).strftime("%H:%M")
    sunset = datetime.fromtimestamp(weather_data["sunset"] + weather_data["timezone"]).strftime("%H:%M")
    output += f"🌅  Sunrise: {sunrise}\n"
    output += f"🌇  Sunset: {sunset}\n\n"

    output += f"📅  3-Day Forecast:\n"
    printed_dates = set()
    for entry in weather_data["forecast"]:
        date_txt = entry["dt_txt"]
        date = date_txt.split()[0]
        if date not in printed_dates:
            day = datetime.strptime(date, "%Y-%m-%d").strftime("%A, %d %B")
            temp_f = entry["main"]["temp"]
            desc_f = entry["weather"][0]["description"]

            if not use_celsius:
                temp_f = (temp_f * 9/5) + 32
                temp_f = round(temp_f, 2)

            output += f"📆 {day}\n   🌡️ {temp_f}°{unit} | ☁️ {desc_f}\n\n"
            printed_dates.add(date)
        if len(printed_dates) == 3:
            break

    result_text.insert(tk.END, output)
    result_text.config(state='disabled')

def export_weather_report():
    if not weather_data:
        messagebox.showwarning("No Data", "No weather data available.")
        return

    content = result_text.get("1.0", tk.END).strip()
    if content:
        now = datetime.utcnow().timestamp() + weather_data["timezone"]
        dt_str = datetime.fromtimestamp(now).strftime("%Y-%m-%d_%H-%M")
        city = weather_data["city"].replace(" ", "_")
        filename = f"weather_{city}_{dt_str}.txt"

        with open(filename, "w", encoding="utf-8") as f:
            f.write(content)
        messagebox.showinfo("Saved", f"Weather report saved as:\n{filename}")
    else:
        messagebox.showwarning("Empty", "Nothing to save.")

def send_email_report():
    if not weather_data:
        messagebox.showwarning("No Data", "No weather data available to send.")
        return

    now = datetime.utcnow().timestamp() + weather_data["timezone"]
    dt_str = datetime.fromtimestamp(now).strftime("%Y-%m-%d_%H-%M")
    city = weather_data["city"].replace(" ", "_")
    filename = f"weather_{city}_{dt_str}.txt"

    content = result_text.get("1.0", tk.END).strip()
    with open(filename, "w", encoding="utf-8") as f:
        f.write(content)

    try:
        sender_email = "your_email@gmail.com"
        app_password = "your_app_password"
        receiver_email = "receiver@example.com"

        msg = EmailMessage()
        msg["Subject"] = f"Weather Report - {weather_data['city']}"
        msg["From"] = sender_email
        msg["To"] = receiver_email
        msg.set_content("Attached is the weather report.\n\nSent from Python App.")

        with open(filename, "rb") as file:
            file_data = file.read()
            msg.add_attachment(file_data, maintype="text", subtype="plain", filename=filename)

        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
            smtp.login(sender_email, app_password)
            smtp.send_message(msg)

        messagebox.showinfo("Email Sent", f"Report sent to {receiver_email}")

    except Exception as e:
        messagebox.showerror("Error", f"Failed to send email.\n{e}")

def clear_weather_display():
    global weather_icon
    result_text.config(state='normal')
    result_text.delete("1.0", tk.END)
    result_text.config(state='disabled')
    icon_label.config(image='')
    weather_icon = None

def toggle_temperature_unit():
    global use_celsius
    use_celsius = not use_celsius
    display_weather_results()

def open_city_in_maps():
    if weather_data and "coord" in weather_data:
        lat = weather_data["coord"]["lat"]
        lon = weather_data["coord"]["lon"]
        maps_url = f"https://www.google.com/maps?q={lat},{lon}"
        webbrowser.open(maps_url)
    else:
        messagebox.showwarning("No data", "No coordinates available.")

root = tk.Tk()
root.title("🌤️ Weather App")
root.geometry("450x670")
root.config(bg="#eaf6fb")

try:
    root.iconbitmap("weather_icon.ico")
except:
    pass

title = tk.Label(root, text="🌤️  Weather Forecast", font=("Segoe UI", 18, "bold"), bg="#eaf6fb")
title.pack(pady=12)

city_entry = tk.Entry(root, font=("Segoe UI", 14), justify='center', width=24)
city_entry.pack(pady=5)

btn_get = tk.Button(root, text="🔍 Get Weather", command=fetch_weather_data, font=("Segoe UI", 11), bg="#4db6ac", fg="white")
btn_get.pack(pady=10)

btn_frame1 = tk.Frame(root, bg="#eaf6fb")
btn_frame1.pack(pady=5)

btn_save = tk.Button(btn_frame1, text="📂 Save", command=export_weather_report, font=("Segoe UI", 10), bg="#81c784", fg="white", width=12)
btn_save.grid(row=0, column=0, padx=5)

btn_refresh = tk.Button(btn_frame1, text="🔄 Refresh", command=fetch_weather_data, font=("Segoe UI", 10), bg="#ffb74d", fg="black", width=12)
btn_refresh.grid(row=0, column=1, padx=5)

btn_clear = tk.Button(btn_frame1, text="🪑 Clear", command=clear_weather_display, font=("Segoe UI", 10), bg="#ef5350", fg="white", width=12)
btn_clear.grid(row=0, column=2, padx=5)

btn_email = tk.Button(btn_frame1, text="✉️ Send Email", command=send_email_report, font=("Segoe UI", 10), bg="#4fc3f7", fg="white", width=12)
btn_email.grid(row=0, column=3, padx=5)

btn_frame2 = tk.Frame(root, bg="#eaf6fb")
btn_frame2.pack(pady=5)

btn_switch = tk.Button(btn_frame2, text="🌡️ °C/°F", command=toggle_temperature_unit, font=("Segoe UI", 10), bg="#9575cd", fg="white", width=18)
btn_switch.grid(row=0, column=0, padx=5)

btn_map = tk.Button(btn_frame2, text="🗌 Open Maps", command=open_city_in_maps, font=("Segoe UI", 10), bg="#64b5f6", fg="white", width=18)
btn_map.grid(row=0, column=1, padx=5)

icon_label = tk.Label(root, bg="#eaf6fb")
icon_label.pack(pady=5)

frame = tk.Frame(root, bg="white", bd=2, relief="sunken")
frame.pack(padx=10, pady=10, fill="both", expand=True)

result_text = tk.Text(frame, height=20, font=("Consolas", 10), bg="white", wrap='word', borderwidth=0)
result_text.pack(padx=10, pady=10, fill="both", expand=True)
result_text.config(state='disabled')

root.mainloop()
