// Nextflow process that reads S3 metadata
process generateSamplesheet {
    input:
    val experiment_id
    
    script:
    """
    aws s3api list-objects-v2 --bucket ${params.bucket} \
        --query "Contents[?contains(Metadata.experiment_contexts, '${experiment_id}')]" \
        | orchestra-meta parse-to-samplesheet > samplesheet.csv
    """
}
