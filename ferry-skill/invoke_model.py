import boto3

def getPrediction():
    endpoint_name = "test"

    client = boto3.client('sagemaker-runtime')

    prediction_data = '{"instances": [ {"start": "2018-01-01 00:00:00", "target": [8.371208085491508, 8.38437885371535, 8.860699073980985, 8.047195011672134, 9.42771383264719, 8.02120332304575, 9.839234913116105, 9.237618947392374, 8.214949470821212, 9.814497679561292, 9.052164695305954, 8.102437854966766, 8.928941871965348, 9.844116398312188, 9.221646100693144, 8.853571486995326, 8.560903044968434, 8.240263518568812, 9.221323908588538, 9.448381346299827, 9.996678314417732, 8.520757726306975, 9.978841260562627, 9.196420806291513, 9.587904493744922, 9.367880938747199, 9.606228859687628, 9.277298500001638, 8.694011829622228]}],"configuration": {"output_types": ["mean", "quantiles", "samples"], "quantiles": ["0.1", "0.9"], "num_samples": 100}}'

    response = client.invoke_endpoint(
        EndpointName=endpoint_name,
        Body=prediction_data,
        ContentType='application/json',
        Accept='string'#,
        #CustomAttributes='string'
    )

    return response