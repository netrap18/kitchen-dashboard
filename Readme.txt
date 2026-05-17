KITCHEN P&L DASHBOARD

Python Version: 3.14

Packages:
- streamlit
- pandas
- plotly
- openpyxl
- numpy

HOW TO RUN:
1. Create a virtual environment:
   python -m venv venv

2. Activate it:
   Windows: venv\Scripts\activate
   Mac/Linux: source venv/bin/activate

3. Install packages:
   pip install -r requirements.txt

4. Run the dashboard:
   streamlit run app.py

5. Opens automatically at http://localhost:8501

ASSUMPTIONS:
- No CM column in source data. Gross Margin used as CM proxy.
- All variance records are below 2%. Other buckets will be empty.

WHAT'S IN THE SUBMISSION:
- app.py: Streamlit dashboard (2 dashboards + bonus insights tab)
- analysis.ipynb: Data exploration and insights notebook
- requirements.txt: Package versions
