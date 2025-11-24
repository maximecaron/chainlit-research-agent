# Deep Research Agent 🕵️‍♂️

A conversational AI agent built with [Chainlit](https://docs.chainlit.io/) designed to perform deep research tasks. This agent breaks down complex user queries, plans a research strategy, gathers information from various sources (simulated currently), and synthesizes the findings into a comprehensive report.

## Features

- **Chainlit UI:** Clean, chat-based interface with support for "Steps" to show the agent's thought process.
- **Research Planning:** Breaks down queries into actionable steps.
- **Source Citations:** Lists sources used in the final report.
- **Hot Reloading:** configured for rapid development.

## Prerequisites

- Python 3.9 or higher
- [Visual Studio Code](https://code.visualstudio.com/) (Recommended)

## Installation

1.  **Clone the repository (or create the directory):**
    ```bash
    cd chainlit-research-agent
    ```

2.  **Create a Virtual Environment:**
    ```bash
    python3 -m venv venv
    ```

3.  **Activate the Virtual Environment:**
    * **macOS/Linux:**
        ```bash
        source venv/bin/activate
        ```
    * **Windows:**
        ```bash
        .\venv\Scripts\activate
        ```

4.  **Install Dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

## Usage

To start the application with hot-reloading enabled (updates automatically when you save `app.py`):

1.  Navigate to the project folder:
    ```bash
    cd chainlit-research-agent
    ```

2.  Activate your virtual environment (if not already active):
    ```bash
    source venv/bin/activate
    ```

3.  Run the Chainlit app:
    ```bash
    chainlit run app.py -w
    ```

4.  The application will open automatically in your browser at `http://localhost:8000`.

## Project Structure

```text
chainlit-research-agent/
├── app.py              # Main application logic
├── requirements.txt    # Python dependencies
└── .chainlit/          # Chainlit configuration files