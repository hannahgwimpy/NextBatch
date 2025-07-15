# monitor.py
import boto3
from flask import Flask, render_template, jsonify
import argparse

app = Flask(__name__)


@app.route('/jobs')
def list_jobs():
    job_queue = app.config.get('JOB_QUEUE')
    # Fetch jobs from all statuses to get a complete picture
    all_jobs = []
    try:
        batch = boto3.client('batch')
        for status in ['SUBMITTED', 'PENDING', 'RUNNABLE', 'STARTING', 'RUNNING', 'SUCCEEDED', 'FAILED']:
            response = batch.list_jobs(jobQueue=job_queue, jobStatus=status)
            all_jobs.extend(response['jobSummaryList'])
        # Sort jobs by creation time
        all_jobs.sort(key=lambda x: x.get('createdAt', 0), reverse=True)
        return jsonify(all_jobs)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/jobs/<job_id>/logs')
def get_job_logs(job_id):
    try:
        batch = boto3.client('batch')
        logs_client = boto3.client('logs')

        # Get the job description to find the log stream name
        job_desc = batch.describe_jobs(jobs=[job_id])
        log_stream_name = job_desc['jobs'][0]['container']['logStreamName']

        if not log_stream_name:
            return jsonify({'logs': 'Log stream not available for this job yet.'})

        log_events = logs_client.get_log_events(
            logGroupName='/aws/batch/job',
            logStreamName=log_stream_name,
            startFromHead=True
        )

        return jsonify({'logs': [event['message'] for event in log_events['events']]})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/jobs/<job_id>/metrics')
def get_job_metrics(job_id):
    # Placeholder for fetching performance metrics from CloudWatch Metrics
    # This would involve using get_metric_data with the correct dimensions,
    # which are best determined once the infrastructure is live.
    return jsonify({
        'message': 'Metrics feature not fully implemented.',
        'metrics': {
            'cpu_utilization': 'N/A',
            'memory_utilization': 'N/A'
        }
    })

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
