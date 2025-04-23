# **TaskCraftAI**

TaskCraft AI is a smart assistant that doesn’t just listen — it acts. From opening apps, sending emails, managing tasks in Jira, to scheduling events, checking the weather, or finding files — TaskCraft is built to streamline your digital life using just your voice.


This guide will walk you through the installation and running of **TaskCraftAI** on **Linux**, **macOS**, and **Windows**.

## **Installation and Running**

### **Linux, macOS, and Windows (From Source)**

Follow these steps to install and run **TaskCraftAI** from source on any platform. You’ll need **Python 3.10+** installed on your system.

#### Steps:

1. **Clone the repository**:
   - Open a terminal or command prompt and clone the repository from GitHub:
     ```bash
     git clone https://github.com/elhalili/taskcraft-ai.git
     cd taskcraft-ai
     ```

2. **Create a Python virtual environment**:
   - Create a virtual environment to isolate dependencies:
     ```bash
     python3 -m venv venv
     ```
   - Activate the virtual environment:
     - **Linux/macOS**:
       ```bash
       source venv/bin/activate
       ```
     - **Windows**:
       ```bash
       .\venv\Scripts\activate
       ```

3. **Install dependencies**:
   - Install the required dependencies using `pip`:
     ```bash
     pip install --upgrade pip
     pip install -r requirements.txt
     ```

4. **Run the application**:
   - After the dependencies are installed, run the application:
     ```bash
     python3 src/main.py
     ```

   - This will start **TaskCraftAI**, and the application should now be running and ready for use.


### **Pre-built Linux AppImage (Optional)**

For Linux users, you can download a pre-built **AppImage** for easy installation.

1. **Download the AppImage**:
   - Visit the [TaskCraftAI GitHub releases page](https://github.com/elhalili/taskcraft-ai/releases).
   - Download the latest **AppImage** release for your system (typically named `TaskCraftAI-x86_64.AppImage`).

2. **Make the AppImage executable**:
   - Open a terminal in the directory where the AppImage was downloaded and run:
     ```bash
     chmod +x TaskCraftAI-x86_64.AppImage
     ```

3. **Run the AppImage**:
   - Now, run the application by clicking on it or with the following command:
     ```bash
     ./TaskCraftAI-x86_64.AppImage
     ```

   - TaskCraftAI should now launch and be ready for use.

## **License**

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for more details.
