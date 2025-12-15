#!/bin/sh
# Start Streamlit using PORT env (Cloud Run sets $PORT)
PORT=${PORT:-8080}
echo "Starting Streamlit on 0.0.0.0:${PORT}"
streamlit run app.py --server.port ${PORT} --server.address 0.0.0.0
