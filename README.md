# 🏠 Rent Agent

An AI-powered real estate rental assistant built with **Google ADK (Agent Development Kit)** and **MCP (Model Context Protocol)** tools.

## 📁 Project Structure

```
Rent_Agent/
├── MCP_Tools/
│   └── mcp_server.py       # MCP server exposing real estate tools to the AI agent
├── Scraper/
│   └── scraper.py          # Web scraper for collecting rental listings
├── notebook/
│   └── realestate.ipynb    # Main agent notebook (ADK-based chat loop)
├── Data/
│   ├── Raw/                # Raw scraped data
│   ├── Pre-processed/      # Cleaned & processed datasets
│   └── Database/           # SQLite or structured DB files
└── README.md
```

## 🚀 Features

- **AI Agent** powered by Google ADK with session-based memory
- **MCP Server** providing tools for property search, filtering, and nearby amenity lookup (Azure Maps)
- **Web Scraper** to collect real estate listings from online portals
- **Data Pipeline** for cleaning and structuring rental data

## 🛠️ Setup

### Prerequisites

- Python 3.10+
- Google ADK
- Azure Maps API key (for amenity search)
- Required Python packages (see below)

### Installation

```bash
git clone https://github.com/<your-username>/Rent_Agent.git
cd Rent_Agent
pip install -r requirements.txt
```

### Environment Variables

Create a `.env` file in the root directory:

```env
AZURE_MAPS_KEY=your_azure_maps_api_key
GOOGLE_API_KEY=your_google_api_key
```

> ⚠️ **Never commit your `.env` file.** It is excluded via `.gitignore`.

## 📓 Usage

Open and run `notebook/realestate.ipynb` to start the AI rental assistant chat session.

## 📄 License

MIT License
