import boto3

# Define the certificate ARN template
CERTIFICATE_ARN = 'arn:aws:acm:eu-west-1:account-id:certificate/{}'

class CertificateFetcher:

    def __init__(self, certificate_arn, aws_region="us-east-1") -> None:
        self.certificate_arn = certificate_arn
        self.aws_region = aws_region

        # Initialize boto3 clients for the specified region
        self.elbv2_client = boto3.client('elbv2', region_name=self.aws_region)
        self.cloudfront_client = boto3.client('cloudfront', region_name=self.aws_region)
        self.apprunner_client = boto3.client('apprunner', region_name=self.aws_region)
        self.elasticbeanstalk_client = boto3.client('elasticbeanstalk', region_name=self.aws_region)

    def check_elbv2_listeners(self):
        paginator = self.elbv2_client.get_paginator('describe_load_balancers')
        for page in paginator.paginate():
            for lb in page['LoadBalancers']:
                listeners_paginator = self.elbv2_client.get_paginator('describe_listeners')
                for listener_page in listeners_paginator.paginate(LoadBalancerArn=lb['LoadBalancerArn']):
                    for listener in listener_page['Listeners']:
                        for cert in listener.get('Certificates', []):
                            if cert['CertificateArn'] == CERTIFICATE_ARN.format(self.certificate_arn):
                                print(f"Certificate used in ELBv2 listener: {listener['ListenerArn']} on load balancer: {lb['LoadBalancerArn']}")

    def check_cloudfront_distributions(self):
        paginator = self.cloudfront_client.get_paginator('list_distributions')
        for page in paginator.paginate():
            if 'Items' in page['DistributionList']:
                for distribution in page['DistributionList']['Items']:
                    if distribution['ViewerCertificate'].get('ACMCertificateArn') == CERTIFICATE_ARN.format(self.certificate_arn):
                        print(f"Certificate used in CloudFront distribution: {distribution['Id']} with domain name: {distribution['DomainName']}")

    def check_apprunner_services(self):
        paginator = self.apprunner_client.get_paginator('list_services')
        for page in paginator.paginate():
            services = page['ServiceSummaryList']
            for service in services:
                service_arn = service['ServiceArn']
                # Describe service to get detailed information including custom domains
                service_response = self.apprunner_client.describe_service(ServiceArn=service_arn)
                custom_domains = service_response['Service'].get('CustomDomains', [])
                for domain in custom_domains:
                    # Check if the associated certificate matches the one we're looking for
                    if domain['CertificateValidationRecords'][0]['Status'] == 'SUCCESS':
                        associated_cert_arn = domain.get('CertificateArn')
                        if associated_cert_arn == CERTIFICATE_ARN.format(self.certificate_arn):
                            print(f"Certificate used in App Runner service: {service_arn} for domain {domain['DomainName']}")


    def check_elastic_beanstalk_environments(self):
        paginator = self.elasticbeanstalk_client.get_paginator('describe_environments')
        for page in paginator.paginate():
            environments = page['Environments']
            for env in environments:
                env_name = env['EnvironmentName']
                settings_response = self.elasticbeanstalk_client.describe_configuration_settings(
                    ApplicationName=env['ApplicationName'],
                    EnvironmentName=env_name
                )
                option_settings = settings_response['ConfigurationSettings'][0]['OptionSettings']
                for setting in option_settings:
                    if setting['Namespace'] == 'aws:elbv2:listener:443' and setting['OptionName'] == 'SSLCertificateArns':
                        # Check if the SSLCertificateArns matches the certificate ARN
                        if setting['Value'] == CERTIFICATE_ARN.format(self.certificate_arn):
                            print(f"Certificate used in Elastic Beanstalk environment: {env_name}")
