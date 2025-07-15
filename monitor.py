# monitor.py
import boto3
from flask import Flask, render_template, jsonify
import argparse

app = Flask(__name__)


@app.route('/jobs')
def list_jobs():
    # This is passed via command line now
    job_queue = app.config.get('JOB_QUEUE')
    job_status = 'RUNNING' # or other statuses like SUCCEEDED, FAILED, etc.
    
    try:
        batch = boto3.client('batch')
        response = batch.list_jobs(
            jobQueue=job_queue,
            jobStatus=job_status
        )
        return jsonify(response['jobSummaryList'])
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/dashboard')
def dashboard():
    # Render dashboard with job statistics
    job_queue = app.config.get('JOB_QUEUE')
    return render_template('dashboard.html', job_queue=job_queue)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Monitoring dashboard for Nextflow jobs on AWS Batch.')
    parser.add_argument('--queue', required=True, help='AWS Batch Job Queue name to monitor.')
    parser.add_argument('--host', default='127.0.0.1', help='Host to run the Flask app on.')
    parser.add_argument('--port', default=5000, type=int, help='Port to run the Flask app on.')
    args = parser.parse_args()

    app.config['JOB_QUEUE'] = args.queue
    app.run(host=args.host, port=args.port, debug=True)
