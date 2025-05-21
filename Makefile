.PHONY: run_app load_test run_dashboard setup_iac

run_app:
	cd app/model-api && PYTHONPATH=/home/sotsuba/gdgaic/app/model-api uvicorn main:app --host 0.0.0.0 --port 8000 --reload
load_test:
	locust -f tests/load_test.py --host http://localhost:5000 --users 50 --spawn-rate 2 
run_dashboard:
	cd app/dashboard && streamlit run main.py
setup_iac:
	cd iac/terraform/environments/dev && bash apply.sh